from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import SELECTING_USER, CONFIRM_ACTION
from modules.api.users import UserAPI
from modules.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

async def handle_action_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle action confirmation"""
    if not update.callback_query:
        return SELECTING_USER
    
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "confirm_action":
        action = context.user_data.get("action")
        uuid = context.user_data.get("uuid")
        
        if not action or not uuid:
            await query.edit_message_text("❌ Ошибка: данные действия потеряны.")
            return SELECTING_USER
        
        return await execute_user_action(update, context, action, uuid)
    
    elif data.startswith("view_"):
        from modules.handlers.users.user_details import show_user_details
        uuid = data.split("_", 1)[1]
        return await show_user_details(update, context, uuid)
    
    return SELECTING_USER

async def execute_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, uuid: str):
    """Execute user action"""
    await update.callback_query.edit_message_text("⏳ Выполняется операция...")
    
    try:
        result = False
        message = ""
        
        if action == "disable":
            result = await UserAPI.disable_user(uuid)
            message = "✅ Пользователь успешно отключен." if result else "❌ Не удалось отключить пользователя."
        
        elif action == "enable":
            result = await UserAPI.enable_user(uuid)
            message = "✅ Пользователь успешно включен." if result else "❌ Не удалось включить пользователя."
        
        elif action == "reset":
            result = await UserAPI.reset_user_traffic(uuid)
            message = "✅ Трафик пользователя успешно сброшен." if result else "❌ Не удалось сбросить трафик."
        
        elif action == "revoke":
            result = await UserAPI.revoke_user_subscription(uuid)
            message = "✅ Подписка пользователя успешно отозвана." if result else "❌ Не удалось отозвать подписку."
        
        else:
            message = "❌ Неизвестное действие."
        
        # Show result with options
        keyboard = [
            [InlineKeyboardButton("👁️ Показать пользователя", callback_data=f"view_{uuid}")],
            [InlineKeyboardButton("🔙 К списку пользователей", callback_data="list_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup
        )
        
        # Clear action data
        context.user_data.pop("action", None)
        context.user_data.pop("uuid", None)
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error executing action {action} for user {uuid}: {e}")
        
        keyboard = [
            [InlineKeyboardButton("👁️ Показать пользователя", callback_data=f"view_{uuid}")],
            [InlineKeyboardButton("🔙 К списку пользователей", callback_data="list_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Произошла ошибка при выполнении операции: {str(e)}",
            reply_markup=reply_markup
        )
        
        return SELECTING_USER

async def setup_bulk_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, user_uuids: list):
    """Setup bulk action confirmation"""
    if not user_uuids:
        await update.callback_query.edit_message_text("❌ Список пользователей пуст.")
        return SELECTING_USER
    
    action_messages = {
        "disable": f"отключить {len(user_uuids)} пользователей",
        "enable": f"включить {len(user_uuids)} пользователей",
        "reset": f"сбросить трафик у {len(user_uuids)} пользователей",
        "revoke": f"отозвать подписки у {len(user_uuids)} пользователей",
        "delete": f"удалить {len(user_uuids)} пользователей"
    }
    
    action_text = action_messages.get(action, f"выполнить операцию для {len(user_uuids)} пользователей")
    
    keyboard = [
        [
            InlineKeyboardButton(f"✅ Да, {action_text}", callback_data=f"confirm_bulk_{action}"),
            InlineKeyboardButton("❌ Отмена", callback_data="list_users")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    context.user_data["bulk_action"] = action
    context.user_data["bulk_uuids"] = user_uuids
    
    await update.callback_query.edit_message_text(
        f"⚠️ Вы уверены, что хотите {action_text}?\n\n❗ Это действие необратимо!",
        reply_markup=reply_markup
    )
    
    return CONFIRM_ACTION

async def execute_bulk_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute bulk action"""
    action = context.user_data.get("bulk_action")
    user_uuids = context.user_data.get("bulk_uuids", [])
    
    if not action or not user_uuids:
        await update.callback_query.edit_message_text("❌ Ошибка: данные операции потеряны.")
        return SELECTING_USER
    
    await update.callback_query.edit_message_text("⏳ Выполняется массовая операция...")
    
    try:
        success_count = 0
        
        for uuid in user_uuids:
            try:
                result = False
                
                if action == "disable":
                    result = await UserAPI.disable_user(uuid)
                elif action == "enable":
                    result = await UserAPI.enable_user(uuid)
                elif action == "reset":
                    result = await UserAPI.reset_user_traffic(uuid)
                elif action == "revoke":
                    result = await UserAPI.revoke_user_subscription(uuid)
                elif action == "delete":
                    result = await UserAPI.delete_user(uuid)
                
                if result:
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Error in bulk action {action} for user {uuid}: {e}")
        
        # Show results
        total_count = len(user_uuids)
        failed_count = total_count - success_count
        
        message = f"📊 *Результаты массовой операции:*\n\n"
        message += f"✅ Успешно: {success_count}\n"
        
        if failed_count > 0:
            message += f"❌ Ошибок: {failed_count}\n"
        
        message += f"📋 Всего обработано: {total_count}"
        
        keyboard = [[InlineKeyboardButton("🔙 К списку пользователей", callback_data="list_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Clear bulk data
        context.user_data.pop("bulk_action", None)
        context.user_data.pop("bulk_uuids", None)
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error in bulk operation: {e}")
        
        keyboard = [[InlineKeyboardButton("🔙 К списку пользователей", callback_data="list_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Произошла ошибка при выполнении массовой операции: {str(e)}",
            reply_markup=reply_markup
        )
        
        return SELECTING_USER