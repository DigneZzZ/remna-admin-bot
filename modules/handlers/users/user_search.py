from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import USER_MENU, SELECTING_USER
from modules.api.users import UserAPI
from modules.utils.formatters import format_user_details, escape_markdown

logger = logging.getLogger(__name__)

async def handle_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search input"""
    search_type = context.user_data.get("search_type")
    
    # Проверяем наличие update.message
    if not update.message:
        logger.error("update.message is None in handle_search_input")
        # Если у нас есть callback_query, используем его для ответа
        if update.callback_query:
            await update.callback_query.answer("❌ Не удалось обработать поисковый запрос.")
            return USER_MENU
        return USER_MENU
    
    search_value = update.message.text.strip()
    
    try:
        if search_type == "username":
            users_response = await UserAPI.search_users_by_partial_name(search_value)
        elif search_type == "telegram_id":
            users_response = await UserAPI.get_user_by_telegram_id(search_value)
        elif search_type == "description":
            users_response = await UserAPI.search_users_by_description(search_value)
        else:
            await update.message.reply_text("❌ Неизвестный тип поиска.")
            return USER_MENU
        
        if not users_response or 'response' not in users_response or not users_response['response']:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ Пользователи по запросу '{search_value}' не найдены.",
                reply_markup=reply_markup
            )
            return USER_MENU
        
        users = users_response['response']
        
        if len(users) == 1:
            # Single user found - show details
            return await show_single_user_result(update, context, users[0])
        else:
            # Multiple users found - show list
            return await show_multiple_users_result(update, context, users, search_value)
            
    except Exception as e:
        logger.error(f"Error in search: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ Произошла ошибка при поиске: {e}",
            reply_markup=reply_markup
        )
        return USER_MENU

async def show_single_user_result(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """Show single user search result"""
    from modules.utils.selection_helpers import SelectionHelper
    
    # Проверяем, есть ли update.message
    if not update.message:
        logger.error("update.message is None in show_single_user_result")
        return USER_MENU
    
    try:
        from modules.utils.formatters import format_user_details
        message = format_user_details(user)
        
        # Убедимся, что user содержит UUID
        user_uuid = user.get('uuid')
        if not user_uuid:
            raise ValueError("UUID пользователя не найден в результате")
            
        # Используем helper для создания клавиатуры с действиями
        keyboard = SelectionHelper.create_user_info_keyboard(user_uuid, action_prefix="user_action")
        
        # Если keyboard не содержит кнопок или вернул None, создадим базовую клавиатуру
        if not keyboard or not keyboard.inline_keyboard:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"✏️ Изменить", callback_data=f"user_action_edit_{user_uuid}")],
                [InlineKeyboardButton(f"📊 Статистика", callback_data=f"user_action_stats_{user_uuid}")],
                [InlineKeyboardButton(f"❌ Удалить", callback_data=f"user_action_delete_{user_uuid}")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]
            ])
        
        await update.message.reply_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        context.user_data["current_user"] = user
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error showing single user result: {e}")
        # Fallback - простая клавиатура если что-то пошло не так
        try:
            user_uuid = user.get('uuid', '')
            user_name = user.get('username', 'Unknown')
            
            keyboard = [
                [InlineKeyboardButton(f"👤 Просмотреть {user_name}", callback_data=f"view_{user_uuid}")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                text=f"Найден пользователь: {user_name}",
                reply_markup=reply_markup
            )
            return SELECTING_USER
        except:
            # Крайний случай - просто вернем пользователя в меню
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")]]
            await update.message.reply_text(
                "❌ Ошибка при отображении пользователя.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return USER_MENU

async def show_multiple_users_result(update: Update, context: ContextTypes.DEFAULT_TYPE, users, search_value):
    """Show multiple users search result"""
    message = f"🔍 Найдено {len(users)} пользователей по запросу '{search_value}':\n\n"
    keyboard = []
    
    for i, user in enumerate(users):
        message += f"{i+1}. {user['username']} - {user['status']}\n"
        keyboard.append([InlineKeyboardButton(f"👤 {user['username']}", callback_data=f"view_{user['uuid']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup
    )
    
    return SELECTING_USER