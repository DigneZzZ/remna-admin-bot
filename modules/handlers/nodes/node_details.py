from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import NODE_MENU
from modules.api.nodes import NodeAPI
from modules.utils.formatters import format_node_details

logger = logging.getLogger(__name__)

async def show_node_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show detailed node information"""
    try:
        await update.callback_query.edit_message_text("🔄 Загрузка данных сервера...")
        
        node_response = await NodeAPI.get_node_by_uuid(uuid)
        
        if not node_response or 'response' not in node_response:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Сервер не найден или ошибка при получении данных.",
                reply_markup=reply_markup
            )
            return NODE_MENU
        
        node = node_response['response']
        message = format_node_details(node)
        
        # Create comprehensive action buttons
        keyboard = []
        
        # Status control
        if node.get("isDisabled"):
            keyboard.append([InlineKeyboardButton("🟢 Включить сервер", callback_data=f"enable_node_{uuid}")])
        else:
            keyboard.append([InlineKeyboardButton("🔴 Отключить сервер", callback_data=f"disable_node_{uuid}")])
        
        # Operations row
        keyboard.append([
            InlineKeyboardButton("🔄 Перезапустить", callback_data=f"restart_node_{uuid}"),
            InlineKeyboardButton("📊 Статистика", callback_data=f"node_stats_{uuid}")
        ])
        
        # Configuration row
        keyboard.append([
            InlineKeyboardButton("📝 Редактировать", callback_data=f"edit_node_{uuid}"),
            InlineKeyboardButton("📜 Сертификат", callback_data=f"show_certificate_{uuid}")
        ])
        
        # Advanced operations
        keyboard.append([
            InlineKeyboardButton("🔧 Управление inbound'ами", callback_data=f"node_inbounds_{uuid}"),
            InlineKeyboardButton("🗑️ Удалить сервер", callback_data=f"delete_node_{uuid}")
        ])
        
        # Navigation
        keyboard.append([InlineKeyboardButton("🔙 К списку серверов", callback_data="list_nodes")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return NODE_MENU
        
    except Exception as e:
        logger.error(f"Error showing node details: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке данных сервера.",
            reply_markup=reply_markup
        )
        return NODE_MENU

async def handle_node_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle various node actions"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("node_inbounds_"):
        uuid = data.split("_", 2)[2]
        return await show_node_inbounds_management(update, context, uuid)
    elif data.startswith("delete_node_"):
        uuid = data.split("_", 2)[2]
        return await confirm_delete_node(update, context, uuid)
    
    return NODE_MENU

async def show_node_inbounds_management(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show inbound management for a specific node"""
    try:
        from modules.api.inbounds import InboundAPI
        
        await update.callback_query.edit_message_text("📡 Загрузка inbound'ов...")
        
        # Get node details
        node_response = await NodeAPI.get_node_by_uuid(uuid)
        if not node_response or 'response' not in node_response:
            raise Exception("Сервер не найден")
        
        node = node_response['response']
        
        # Get all inbounds
        inbounds_response = await InboundAPI.get_inbounds()
        if not inbounds_response or 'response' not in inbounds_response:
            raise Exception("Не удалось получить список inbound'ов")
        
        inbounds = inbounds_response['response']
        excluded_inbounds = node.get('excludedInbounds', [])
        
        message = f"📡 *Управление inbound'ами для {node['name']}*\n\n"
        message += "🟢 = Включен на сервере\n"
        message += "🔴 = Отключен на сервере\n\n"
        
        keyboard = []
        
        for inbound in inbounds:
            inbound_id = inbound['uuid']
            protocol = inbound.get('type', 'Unknown')
            port = inbound.get('port', 'N/A')
            tag = inbound.get('tag', 'Unknown')
            
            if inbound_id in excluded_inbounds:
                # Excluded (disabled)
                button_text = f"🔴 {tag} ({protocol}:{port})"
                callback_data = f"enable_inbound_on_node_{uuid}_{inbound_id}"
            else:
                # Included (enabled)
                button_text = f"🟢 {tag} ({protocol}:{port})"
                callback_data = f"disable_inbound_on_node_{uuid}_{inbound_id}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("🔙 К деталям сервера", callback_data=f"view_node_{uuid}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return NODE_MENU
        
    except Exception as e:
        logger.error(f"Error showing node inbounds management: {e}")
        keyboard = [[InlineKeyboardButton("🔙 К деталям сервера", callback_data=f"view_node_{uuid}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке inbound'ов: {str(e)}",
            reply_markup=reply_markup
        )
        return NODE_MENU

async def confirm_delete_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Confirm node deletion"""
    try:
        node_response = await NodeAPI.get_node_by_uuid(uuid)
        if not node_response or 'response' not in node_response:
            raise Exception("Сервер не найден")
        
        node = node_response['response']
        
        message = f"⚠️ *Подтверждение удаления сервера*\n\n"
        message += f"Вы уверены, что хотите удалить сервер **{node['name']}**?\n\n"
        message += f"🔴 *Это действие необратимо!*\n"
        message += f"• Сервер будет полностью удален\n"
        message += f"• Все связанные данные будут потеряны\n"
        message += f"• Активные соединения будут разорваны\n\n"
        message += f"Для подтверждения введите название сервера: `{node['name']}`"
        
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data=f"view_node_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Store deletion context
        context.user_data["pending_delete_node"] = {
            "uuid": uuid,
            "name": node['name']
        }
        
        return NODE_MENU
        
    except Exception as e:
        logger.error(f"Error confirming node deletion: {e}")
        keyboard = [[InlineKeyboardButton("🔙 К деталям сервера", callback_data=f"view_node_{uuid}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=reply_markup
        )
        return NODE_MENU