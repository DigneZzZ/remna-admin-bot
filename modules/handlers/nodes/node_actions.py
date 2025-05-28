from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import NODE_MENU
from modules.api.nodes import NodeAPI

logger = logging.getLogger(__name__)

async def enable_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Enable node"""
    logger.info(f"Attempting to enable node with UUID: {uuid}")
    
    try:
        await update.callback_query.edit_message_text("🔄 Включение сервера...")
        
        result = await NodeAPI.enable_node(uuid)
        logger.info(f"Enable node API result: {result}")
        
        if result and 'response' in result:
            response_data = result['response']
            if response_data.get("uuid") == uuid or response_data.get("isDisabled") is False:
                message = "✅ *Сервер успешно включен*\n\n"
                message += "Сервер теперь активен и готов к обработке соединений."
            else:
                message = "❌ Ошибка при включении сервера."
        else:
            message = "❌ Ошибка при включении сервера."
            
    except Exception as e:
        message = f"❌ Ошибка при включении сервера: {str(e)}"
        logger.error(f"Exception while enabling node: {e}")
    
    keyboard = [
        [InlineKeyboardButton("👁️ Показать детали", callback_data=f"view_node_{uuid}")],
        [InlineKeyboardButton("🔙 К списку серверов", callback_data="list_nodes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def disable_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Disable node"""
    logger.info(f"Attempting to disable node with UUID: {uuid}")
    
    try:
        await update.callback_query.edit_message_text("🔄 Отключение сервера...")
        
        result = await NodeAPI.disable_node(uuid)
        logger.info(f"Disable node API result: {result}")
        
        if result and 'response' in result:
            response_data = result['response']
            if response_data.get("uuid") == uuid or response_data.get("isDisabled") is True:
                message = "✅ *Сервер успешно отключен*\n\n"
                message += "Сервер отключен и не принимает новые соединения."
            else:
                message = "❌ Ошибка при отключении сервера."
        else:
            message = "❌ Ошибка при отключении сервера."
            
    except Exception as e:
        message = f"❌ Ошибка при отключении сервера: {str(e)}"
        logger.error(f"Exception while disabling node: {e}")
    
    keyboard = [
        [InlineKeyboardButton("👁️ Показать детали", callback_data=f"view_node_{uuid}")],
        [InlineKeyboardButton("🔙 К списку серверов", callback_data="list_nodes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def restart_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Restart node"""
    logger.info(f"Attempting to restart node with UUID: {uuid}")
    
    try:
        await update.callback_query.edit_message_text("🔄 Перезапуск сервера...")
        
        result = await NodeAPI.restart_node(uuid)
        logger.info(f"Restart node API result: {result}")
        
        if result and result.get("eventSent"):
            message = "✅ *Команда перезапуска отправлена*\n\n"
            message += "📤 Команда на перезапуск сервера успешно отправлена.\n\n"
            message += "⏳ *Процесс перезапуска:*\n"
            message += "• Остановка сервисов: ~30 сек\n"
            message += "• Запуск сервисов: ~30 сек\n"
            message += "• Полное восстановление: ~1-2 мин\n\n"
            message += "🔍 Проверьте статус через несколько минут."
        else:
            message = "❌ *Ошибка при перезапуске*\n\n"
            message += "Не удалось отправить команду перезапуска."
            
    except Exception as e:
        message = f"❌ Ошибка при перезапуске сервера: {str(e)}"
        logger.error(f"Exception while restarting node: {e}")
    
    keyboard = [
        [InlineKeyboardButton("📊 Проверить статус", callback_data=f"node_stats_{uuid}")],
        [InlineKeyboardButton("👁️ Показать детали", callback_data=f"view_node_{uuid}")],
        [InlineKeyboardButton("🔙 К списку серверов", callback_data="list_nodes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def delete_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Delete node after confirmation"""
    try:
        await update.callback_query.edit_message_text("🗑️ Удаление сервера...")
        
        result = await NodeAPI.delete_node(uuid)
        
        if result:
            message = "✅ *Сервер успешно удален*\n\n"
            message += "Сервер и все связанные с ним данные удалены."
            
            keyboard = [[InlineKeyboardButton("🔙 К списку серверов", callback_data="list_nodes")]]
        else:
            message = "❌ *Ошибка при удалении сервера*\n\n"
            message += "Попробуйте еще раз или обратитесь к администратору."
            
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"delete_node_{uuid}")],
                [InlineKeyboardButton("👁️ К деталям сервера", callback_data=f"view_node_{uuid}")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Clear deletion context
        context.user_data.pop("pending_delete_node", None)
        
        return NODE_MENU
        
    except Exception as e:
        logger.error(f"Error deleting node: {e}")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"delete_node_{uuid}")],
            [InlineKeyboardButton("👁️ К деталям сервера", callback_data=f"view_node_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при удалении сервера: {str(e)}",
            reply_markup=reply_markup
        )
        return NODE_MENU