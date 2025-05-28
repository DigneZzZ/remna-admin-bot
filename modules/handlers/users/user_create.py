from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
import random
import string
import re

from modules.config import CREATE_USER_FIELD, USER_FIELDS, MAIN_MENU, USER_MENU
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
    """Finish creating a user with improved API response handling"""
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
    
    try:
        # Create user
        result = await UserAPI.create_user(user_data)
        logger.info(f"User creation API result: {result}")
        
        # Handle different API response formats
        user = None
        if isinstance(result, dict):
            if 'response' in result:
                user = result['response']
                logger.debug("Found user data in 'response' field")
            elif 'uuid' in result:
                user = result
                logger.debug("Found user data directly in result")
        
        if user and 'uuid' in user:
            keyboard = [
                [InlineKeyboardButton("👁️ Просмотр пользователя", callback_data=f"view_{user['uuid']}")],
                [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = f"✅ Пользователь успешно создан!\n\n"
            message += f"👤 Имя: {escape_markdown(user['username'])}\n"
            message += f"🆔 UUID: `{user['uuid']}`\n"
            message += f"🔑 Короткий UUID: `{user.get('shortUuid', 'N/A')}`\n"
            message += f"📝 UUID подписки: `{user.get('subscriptionUuid', 'N/A')}`\n\n"
            
            # Handle subscription URL with proper escaping
            if 'subscriptionUrl' in user:
                sub_url = user['subscriptionUrl']
                message += f"🔗 URL подписки:\n```\n{sub_url}\n```\n"
            
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
            
            # Clear creation data
            context.user_data.pop("create_user", None)
            context.user_data.pop("using_template", None)
            
            return MAIN_MENU
        else:
            logger.error(f"Invalid user creation response: {result}")
            raise Exception("Invalid API response format")
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="create_user")],
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        error_message = "❌ Не удалось создать пользователя. Проверьте введенные данные."
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                error_message,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                error_message,
                reply_markup=reply_markup
            )
        
        return MAIN_MENU
    
async def show_template_confirmation(query, context: ContextTypes.DEFAULT_TYPE, template_name: str):
    """Show template confirmation with details"""
    from modules.utils.presets import format_template_info
    
    info = format_template_info(template_name)
    message = f"📋 *Подтверждение шаблона*\n\n{info}\n\n"
    message += "Вы можете использовать этот шаблон как есть или изменить настройки:"
    
    keyboard = [
        [InlineKeyboardButton("✅ Использовать шаблон", callback_data="confirm_template")],
        [InlineKeyboardButton("⚙️ Изменить настройки", callback_data="modify_template")],
        [InlineKeyboardButton("🔙 Выбрать другой шаблон", callback_data="back_to_template_selection")]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_manual_creation_fields(query, context: ContextTypes.DEFAULT_TYPE):
    """Show manual field editing interface"""
    user_data = context.user_data.get("create_user", {})
    
    message = "⚙️ *Ручное создание пользователя*\n\n"
    message += "Настройте параметры пользователя:\n\n"
    
    # Show current values
    from modules.utils.formatters import format_bytes
    
    traffic = user_data.get("trafficLimitBytes", 100 * 1024 * 1024 * 1024)
    if traffic == 0:
        traffic_str = "Безлимитный"
    else:
        traffic_str = format_bytes(traffic)
    
    devices = user_data.get("hwidDeviceLimit", 1)
    devices_str = f"{devices} устройств" if devices > 0 else "Без лимита"
    
    strategy = user_data.get("trafficLimitStrategy", "MONTH")
    strategy_map = {
        "NO_RESET": "Без сброса",
        "DAY": "Ежедневно", 
        "WEEK": "Еженедельно",
        "MONTH": "Ежемесячно"
    }
    strategy_str = strategy_map.get(strategy, strategy)
    
    description = user_data.get("description", "Пользователь VPN")
    
    message += f"📈 Лимит трафика: *{traffic_str}*\n"
    message += f"📱 Лимит устройств: *{devices_str}*\n"
    message += f"🔄 Сброс трафика: *{strategy_str}*\n"
    message += f"📝 Описание: *{description}*\n"
    
    keyboard = [
        [
            InlineKeyboardButton("📈 Трафик", callback_data="edit_field_traffic"),
            InlineKeyboardButton("📱 Устройства", callback_data="edit_field_devices")
        ],
        [
            InlineKeyboardButton("🔄 Сброс", callback_data="edit_field_strategy"),
            InlineKeyboardButton("📝 Описание", callback_data="edit_field_description")
        ],
        [InlineKeyboardButton("✅ Готово", callback_data="finish_manual_creation")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_template_selection")]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def ask_username(query, context: ContextTypes.DEFAULT_TYPE):
    """Ask for username or create user if template was used"""
    using_template = context.user_data.get("using_template")
    
    if using_template:
        # For templates, create user automatically with generated username
        await finish_create_user_directly(query, context)
    else:
        # For manual creation, ask for username
        message = "👤 *Введите имя пользователя*\n\n"
        message += "Оставьте пустым для автоматической генерации:"
        
        keyboard = [
            [InlineKeyboardButton("🎲 Сгенерировать автоматически", callback_data="username_done")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_template_selection")]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def finish_create_user_directly(query, context: ContextTypes.DEFAULT_TYPE):
    """Finish creating user directly (for templates) with improved error handling"""
    # Generate username if not provided
    user_data = context.user_data["create_user"]
    if "username" not in user_data or not user_data["username"]:
        characters = string.ascii_letters + string.digits
        user_data["username"] = ''.join(random.choice(characters) for _ in range(20))
    
    # Set required defaults
    defaults = {
        "trafficLimitStrategy": "MONTH",
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
        user_data["trafficLimitStrategy"] = user_data.get("trafficLimitStrategy", "MONTH")
    
    try:
        # Create user
        result = await UserAPI.create_user(user_data)
        logger.info(f"Template user creation API result: {result}")
        
        # Handle different API response formats
        user = None
        if isinstance(result, dict):
            if 'response' in result:
                user = result['response']
            elif 'uuid' in result:
                user = result
        
        if user and 'uuid' in user:
            keyboard = [
                [InlineKeyboardButton("👁️ Просмотр пользователя", callback_data=f"view_{user['uuid']}")],
                [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = f"✅ Пользователь успешно создан!\n\n"
            message += f"👤 Имя: {escape_markdown(user['username'])}\n"
            message += f"🆔 UUID: `{user['uuid']}`\n"
            message += f"🔑 Короткий UUID: `{user.get('shortUuid', 'N/A')}`\n"
            message += f"📝 UUID подписки: `{user.get('subscriptionUuid', 'N/A')}`\n\n"
            
            # Handle subscription URL with proper escaping
            if 'subscriptionUrl' in user:
                sub_url = user['subscriptionUrl']
                message += f"🔗 URL подписки:\n```\n{sub_url}\n```\n"
            
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            # Clear creation data
            context.user_data.pop("create_user", None)
            context.user_data.pop("using_template", None)
            
        else:
            logger.error(f"Invalid template user creation response: {result}")
            raise Exception("Invalid API response format")
            
    except Exception as e:
        logger.error(f"Error creating template user: {e}")
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="create_user")],
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="❌ Не удалось создать пользователя. Проверьте введенные данные.",
            reply_markup=reply_markup
        )
async def show_field_editor(query, context: ContextTypes.DEFAULT_TYPE, field_name: str):
    """Show field value selection interface"""
    message = f"⚙️ *Настройка: {field_name}*\n\n"
    keyboard = []
    
    if field_name == "traffic":
        message += "Выберите лимит трафика:"
        from modules.utils.presets import TRAFFIC_LIMIT_PRESETS
        
        options = list(TRAFFIC_LIMIT_PRESETS.items())
        for i in range(0, len(options), 2):
            row = []
            for j in range(2):
                if i + j < len(options):
                    name, value = options[i + j]
                    row.append(InlineKeyboardButton(
                        name, 
                        callback_data=f"set_traffic_{value}"
                    ))
            keyboard.append(row)
            
    elif field_name == "devices":
        message += "Выберите лимит устройств:"
        from modules.utils.presets import DEVICE_LIMIT_PRESETS
        
        options = list(DEVICE_LIMIT_PRESETS.items())
        for i in range(0, len(options), 2):
            row = []
            for j in range(2):
                if i + j < len(options):
                    name, value = options[i + j]
                    row.append(InlineKeyboardButton(
                        name,
                        callback_data=f"set_devices_{value}"
                    ))
            keyboard.append(row)
            
    elif field_name == "strategy":
        message += "Выберите стратегию сброса трафика:"
        strategies = [
            ("Без сброса", "NO_RESET"),
            ("Ежедневно", "DAY"),
            ("Еженедельно", "WEEK"), 
            ("Ежемесячно", "MONTH")
        ]
        
        for name, value in strategies:
            keyboard.append([InlineKeyboardButton(
                name,
                callback_data=f"set_strategy_{value}"
            )])
            
    elif field_name == "description":
        message += "Выберите описание:"
        from modules.utils.presets import DESCRIPTION_PRESETS
        
        for desc in DESCRIPTION_PRESETS:
            keyboard.append([InlineKeyboardButton(
                desc,
                callback_data=f"set_description_{desc}"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="modify_template")])
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_field_value_selection(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle field value selection"""
    data = query.data
    user_data = context.user_data.get("create_user", {})
    
    if data.startswith("set_traffic_"):
        value = int(data[12:])  # Remove "set_traffic_" prefix
        user_data["trafficLimitBytes"] = value
        
    elif data.startswith("set_devices_"):
        value = int(data[12:])  # Remove "set_devices_" prefix  
        user_data["hwidDeviceLimit"] = value
        
    elif data.startswith("set_strategy_"):
        value = data[13:]  # Remove "set_strategy_" prefix
        user_data["trafficLimitStrategy"] = value
        
    elif data.startswith("set_description_"):
        value = data[16:]  # Remove "set_description_" prefix
        user_data["description"] = value
    
    context.user_data["create_user"] = user_data
    await show_manual_creation_fields(query, context)

async def handle_username_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for username"""
    if not update.message:
        return CREATE_USER_FIELD
    
    username = update.message.text.strip()
    
    # Validate username
    if username and not re.match(r'^[a-zA-Z0-9_-]{3,30}$', username):
        await update.message.reply_text(
            "❌ Имя пользователя должно содержать только буквы, цифры, дефисы и подчеркивания (3-30 символов).\n"
            "Попробуйте еще раз или используйте автоматическую генерацию:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 Сгенерировать автоматически", callback_data="username_done")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_template_selection")]
            ])
        )
        return CREATE_USER_FIELD
    
    # Store username and finish creation
    if username:
        context.user_data["create_user"]["username"] = username
    
    await finish_create_user(update, context)
    return MAIN_MENU