from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import USER_MENU, SELECTING_USER
from modules.api.users import UserAPI
from modules.utils.selection_helpers import SelectionHelper

logger = logging.getLogger(__name__)

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users with improved selection interface"""
    await update.callback_query.edit_message_text("📋 Загрузка списка пользователей...")

    try:
        keyboard, users_data = await SelectionHelper.get_users_selection_keyboard(
            callback_prefix="select_user",
            include_back=True,
            max_per_row=1
        )
        
        if not users_data:
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Пользователи не найдены.",
                reply_markup=reply_markup
            )
            return USER_MENU

        context.user_data["users_data"] = users_data
        
        message = f"👥 *Список пользователей* ({len(users_data)} шт.)\n\n"
        message += "Выберите пользователя для просмотра подробной информации:"

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error in list_users: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке списка пользователей: {str(e)}",
            reply_markup=reply_markup
        )
        return USER_MENU

async def handle_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user selection with improved UI"""
    from modules.handlers.users.user_details import show_user_details
    from modules.handlers.user_handlers import show_users_menu
    
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("select_user_"):
        user_uuid = data.split("_", 2)[2]
        return await show_user_details(update, context, user_uuid)
    elif data == "back":
        return await show_users_menu(update, context)
    elif data.startswith("users_page_"):
        page = int(data.split("_")[2])
        try:
            keyboard, users_data = await SelectionHelper.get_users_selection_keyboard(
                callback_prefix="select_user",
                include_back=True,
                max_per_row=1,
                page=page
            )
            
            context.user_data["users_data"] = users_data
            
            message = f"👥 *Список пользователей* ({len(users_data)} шт.) - страница {page + 1}\n\n"
            message += "Выберите пользователя для просмотра подробной информации:"

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error in pagination: {e}")
            return await show_users_menu(update, context)

    return SELECTING_USER