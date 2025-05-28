from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
import random
import string
import re

from modules.config import CREATE_USER_FIELD, USER_FIELDS, MAIN_MENU
from modules.api.users import UserAPI
from modules.utils.formatters import escape_markdown, format_bytes

logger = logging.getLogger(__name__)

async def start_create_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start creating a new user - show template selection"""
    # Clear previous data
    context.user_data.pop("create_user", None)
    context.user_data.pop("create_user_fields", None)
    context.user_data.pop("current_field_index", None)
    context.user_data.pop("search_type", None)
    context.user_data.pop("using_template", None)
    
    context.user_data["create_user"] = {}
    
    await show_template_selection(update, context)
    return CREATE_USER_FIELD

async def show_template_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show template selection menu"""
    from modules.utils.presets import get_template_names
    
    message = "🎯 *Создание пользователя*\n\n"
    message += "Выберите готовый шаблон или создайте пользователя вручную:\n\n"
    message += "📋 *Готовые шаблоны* содержат все необходимые настройки\n"
    message += "⚙️ *Ручное создание* позволяет настроить каждое поле отдельно"
    
    keyboard = []
    templates = get_template_names()
    
    # Add template buttons
    for i in range(0, len(templates), 2):
        row = []
        for j in range(2):
            if i + j < len(templates):
                template_name = templates[i + j]
                row.append(InlineKeyboardButton(
                    template_name, 
                    callback_data=f"template_{template_name}"
                ))
        keyboard.append(row)
    
    keyboard.extend([
        [InlineKeyboardButton("⚙️ Создать вручную", callback_data="create_manual")],
        [InlineKeyboardButton("❌ Отмена", callback_data="back_to_users")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def handle_create_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user input when creating a user"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    # Handle template selection
    if query.data.startswith("template_"):
        template_name = query.data[9:]  # Remove "template_" prefix
        logger.info(f"Template selected: {template_name}")
        
        from modules.utils.presets import get_template_by_name, apply_template_to_user_data, format_template_info
        
        template = get_template_by_name(template_name)
        if not template:
            await query.edit_message_text(
                "❌ Шаблон не найден. Попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="create_user")
                ]])
            )
            return CREATE_USER_FIELD
        
        # Apply template to user data
        context.user_data["create_user"] = apply_template_to_user_data({}, template_name)
        context.user_data["using_template"] = template_name
        
        # Show template confirmation
        await show_template_confirmation(query, context, template_name)
        return CREATE_USER_FIELD
        
    # Handle manual creation
    elif query.data == "create_manual":
        await show_manual_creation_fields(query, context)
        return CREATE_USER_FIELD
        
    # Handle template confirmation
    elif query.data == "confirm_template":
        await ask_username(query, context)
        return CREATE_USER_FIELD
        
    # Handle template modification
    elif query.data == "modify_template":
        await show_manual_creation_fields(query, context)
        return CREATE_USER_FIELD
        
    # Handle username input completion
    elif query.data == "username_done":
        username = context.user_data.get("temp_username", "")
        if username:
            context.user_data["create_user"]["username"] = username
            context.user_data.pop("temp_username", None)
            await finish_create_user(update, context)
        return MAIN_MENU
        
    # Handle field editing in manual mode
    elif query.data.startswith("edit_field_"):
        field_name = query.data[11:]  # Remove "edit_field_" prefix
        await show_field_editor(query, context, field_name)
        return CREATE_USER_FIELD
        
    # Handle field value selection
    elif query.data.startswith("set_"):
        await handle_field_value_selection(query, context)
        return CREATE_USER_FIELD
        
    # Handle navigation
    elif query.data == "back_to_users":
        from modules.handlers.user_handlers import show_users_menu
        await show_users_menu(update, context)
        return USER_MENU
        
    elif query.data == "back_to_template_selection":
        await show_template_selection(update, context)
        return CREATE_USER_FIELD
        
    elif query.data == "finish_manual_creation":
        await ask_username(query, context)
        return CREATE_USER_FIELD
    
    return CREATE_USER_FIELD

async def finish_create_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish creating a user"""
    user_data = context.user_data["create_user"]
    
    # Validate and set defaults
    if "username" not in user_data or not user_data["username"]:
        characters = string.ascii_letters + string.digits
        user_data["username"] = ''.join(random.choice(characters) for _ in range(20))
    
    # Set required defaults
    defaults = {
        "trafficLimitStrategy": "NO_RESET",
        "trafficLimitBytes": 100 * 1024 * 1024 * 1024,  # 100 GB
        "hwidDeviceLimit": 1,
        "resetDay": 1
    }
    
    for key, value in defaults.items():
        if key not in user_data:
            user_data[key] = value
    
    if "expireAt" not in user_data:
        user_data["expireAt"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000Z")
    
    if "description" not in user_data or not user_data["description"]:
        user_data["description"] = f"Автоматически созданный пользователь {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
    # Handle device limit strategy
    if user_data.get("hwidDeviceLimit", 0) > 0:
        user_data["trafficLimitStrategy"] = "NO_RESET"
    
    # Create user
    result = await UserAPI.create_user(user_data)
    
    if result and 'response' in result:
        user = result['response']
        keyboard = [
            [InlineKeyboardButton("👁️ Просмотр пользователя", callback_data=f"view_{user['uuid']}")],
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"✅ Пользователь успешно создан!\n\n"
        message += f"👤 Имя: {escape_markdown(user['username'])}\n"
        message += f"🆔 UUID: `{user['uuid']}`\n"
        message += f"🔑 Короткий UUID: `{user['shortUuid']}`\n"
        message += f"📝 UUID подписки: `{user['subscriptionUuid']}`\n\n"
        message += f"🔗 URL подписки:\n```\n{user['subscriptionUrl']}\n```\n"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return MAIN_MENU
    else:
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="create_user")],
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Не удалось создать пользователя. Проверьте введенные данные.",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU