from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import SELECTING_USER, WAITING_FOR_INPUT
from modules.api.users import UserAPI
from modules.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

async def confirm_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Confirm user deletion"""
    response = await UserAPI.get_user_by_uuid(uuid)
    
    if not response or 'response' not in response:
        await update.callback_query.edit_message_text("❌ Пользователь не найден.")
        return SELECTING_USER
    
    user = response['response']
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{uuid}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"view_{uuid}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"⚠️ *Подтверждение удаления*\n\n"
    message += f"Вы действительно хотите удалить пользователя:\n"
    message += f"👤 Имя: `{escape_markdown(user['username'])}`\n"
    message += f"🆔 UUID: `{user['uuid']}`\n"
    message += f"📊 Статус: `{user['status']}`\n\n"
    message += f"❗ Это действие необратимо!\n\n"
    message += f"💡 Для подтверждения введите имя пользователя: `{user['username']}`"
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Store deletion context
    context.user_data["deleting_user"] = user
    context.user_data["waiting_for"] = "delete_confirmation"
    
    return WAITING_FOR_INPUT

async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delete confirmation input"""
    user_input = update.message.text.strip()
    user = context.user_data.get("deleting_user")
    
    if not user:
        await update.message.reply_text("❌ Ошибка: данные удаления потеряны.")
        return SELECTING_USER
    
    expected_username = user['username']
    uuid = user['uuid']
    
    if user_input != expected_username:
        keyboard = [
            [InlineKeyboardButton("❌ Отмена удаления", callback_data=f"view_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ Неверное имя пользователя!\n"
            f"Ожидалось: `{expected_username}`\n"
            f"Введено: `{user_input}`\n\n"
            f"Попробуйте еще раз или отмените операцию:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return WAITING_FOR_INPUT
    
    return await execute_delete_user(update, context, uuid)

async def execute_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Execute user deletion"""
    await update.message.reply_text("⏳ Удаление пользователя...")
    
    try:
        result = await UserAPI.delete_user(uuid)
        
        keyboard = [[InlineKeyboardButton("🔙 К списку пользователей", callback_data="list_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if result:
            message = "✅ Пользователь успешно удален."
        else:
            message = "❌ Не удалось удалить пользователя."
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup
        )
        
        # Clear deletion context
        context.user_data.pop("deleting_user", None)
        context.user_data.pop("waiting_for", None)
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error deleting user {uuid}: {e}")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"delete_{uuid}")],
            [InlineKeyboardButton("🔙 К пользователю", callback_data=f"view_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ Произошла ошибка при удалении: {str(e)}",
            reply_markup=reply_markup
        )
        
        return SELECTING_USER

async def bulk_delete_users(update: Update, context: ContextTypes.DEFAULT_TYPE, user_uuids: list):
    """Bulk delete users"""
    if not user_uuids:
        await update.callback_query.edit_message_text("❌ Список пользователей для удаления пуст.")
        return SELECTING_USER
    
    await update.callback_query.edit_message_text("⏳ Массовое удаление пользователей...")
    
    try:
        success_count = 0
        failed_users = []
        
        for uuid in user_uuids:
            try:
                result = await UserAPI.delete_user(uuid)
                if result:
                    success_count += 1
                else:
                    failed_users.append(uuid)
            except Exception as e:
                logger.error(f"Error deleting user {uuid}: {e}")
                failed_users.append(uuid)
        
        total_count = len(user_uuids)
        failed_count = len(failed_users)
        
        message = f"📊 *Результаты массового удаления:*\n\n"
        message += f"✅ Успешно удалено: {success_count}\n"
        
        if failed_count > 0:
            message += f"❌ Ошибок: {failed_count}\n"
            message += f"📋 Всего обработано: {total_count}\n\n"
            
            if failed_count <= 10:  # Show failed UUIDs if not too many
                message += f"❌ *Не удалось удалить:*\n"
                for failed_uuid in failed_users[:10]:
                    message += f"• `{failed_uuid[:8]}...`\n"
        else:
            message += f"🎉 Все {total_count} пользователей успешно удалены!"
        
        keyboard = [[InlineKeyboardButton("🔙 К списку пользователей", callback_data="list_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        
        keyboard = [[InlineKeyboardButton("🔙 К списку пользователей", callback_data="list_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Произошла ошибка при массовом удалении: {str(e)}",
            reply_markup=reply_markup
        )
        
        return SELECTING_USER