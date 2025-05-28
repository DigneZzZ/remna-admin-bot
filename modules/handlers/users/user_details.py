from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import USER_MENU, SELECTING_USER, CONFIRM_ACTION
from modules.api.users import UserAPI
from modules.utils.formatters import format_user_details, format_user_details_safe, escape_markdown
from modules.utils.selection_helpers import SelectionHelper

logger = logging.getLogger(__name__)

async def show_user_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show user details"""
    response = await UserAPI.get_user_by_uuid(uuid)
    
    if not response or 'response' not in response:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Пользователь не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return USER_MENU

    user = response['response']

    try:
        message = format_user_details(user)
    except Exception as e:
        logger.error(f"Error formatting user details: {e}")
        message = format_user_details_safe(user)

    keyboard = SelectionHelper.create_user_info_keyboard(uuid, action_prefix="user_action")

    try:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        if "can't parse entities" in str(e).lower():
            logger.warning(f"Markdown parsing error, using safe format: {e}")
            safe_message = format_user_details_safe(user)
            await update.callback_query.edit_message_text(
                text=safe_message,
                reply_markup=keyboard
            )
        else:
            logger.error(f"Error updating message: {e}")
            await update.callback_query.answer("❌ Ошибка при отображении данных")

    context.user_data["current_user"] = user
    return SELECTING_USER

async def handle_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user action with improved SelectionHelper support"""
    from modules.handlers.users.user_edit import start_edit_user
    from modules.handlers.users.user_delete import confirm_delete_user
    from modules.handlers.users.user_hwid import show_user_hwid_devices
    from modules.handlers.users.user_stats import show_user_stats
    
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("user_action_"):
        action_parts = data.split("_")
        if len(action_parts) >= 4:
            action = action_parts[2]
            uuid = "_".join(action_parts[3:])
            
            if action == "edit":
                return await start_edit_user(update, context, uuid)
            elif action == "refresh":
                return await show_user_details(update, context, uuid)
            elif action == "delete":
                return await confirm_delete_user(update, context, uuid)
            elif action == "hwid":
                return await show_user_hwid_devices(update, context, uuid)
            elif action == "stats":
                return await show_user_stats(update, context, uuid)
            elif action in ["disable", "enable", "reset", "revoke"]:
                return await setup_action_confirmation(update, context, action, uuid)

    return SELECTING_USER

async def setup_action_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, uuid: str):
    """Setup action confirmation"""
    context.user_data["action"] = action
    context.user_data["uuid"] = uuid
    
    action_messages = {
        "disable": "отключить",
        "enable": "включить", 
        "reset": "сбросить трафик",
        "revoke": "отозвать подписку"
    }
    
    action_text = action_messages.get(action, action)
    
    keyboard = [
        [
            InlineKeyboardButton(f"✅ Да, {action_text}", callback_data="confirm_action"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"view_{uuid}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"⚠️ Вы уверены, что хотите {action_text} пользователя?\n\nUUID: `{uuid}`",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return CONFIRM_ACTION