from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import NODE_MENU
from modules.api.nodes import NodeAPI
from modules.utils.selection_helpers import SelectionHelper
from modules.utils.formatters import format_bytes

logger = logging.getLogger(__name__)

async def list_nodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all nodes using SelectionHelper"""
    await update.callback_query.edit_message_text("🖥️ Загрузка списка серверов...")

    try:
        # Use SelectionHelper for user-friendly display
        keyboard, nodes_data = await SelectionHelper.get_nodes_selection_keyboard(
            callback_prefix="view_node",
            include_back=True
        )
        
        # Replace back button with custom callback
        if keyboard.inline_keyboard and keyboard.inline_keyboard[-1][0].text == "🔙 Назад":
            new_keyboard = []
            for row in keyboard.inline_keyboard[:-1]:
                new_keyboard.append(row)
            new_keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")])
            keyboard = InlineKeyboardMarkup(new_keyboard)
        
        # Store nodes data in context
        context.user_data["nodes_data"] = nodes_data
        
        if not nodes_data:
            await update.callback_query.edit_message_text(
                "❌ Серверы не найдены или ошибка при получении списка.",
                reply_markup=keyboard
            )
            return NODE_MENU

        # Count online/offline nodes
        online_count = sum(1 for node in nodes_data.values() 
                          if not node.get("isDisabled", False) and node.get("isConnected", False))
        total_count = len(nodes_data)
        disabled_count = sum(1 for node in nodes_data.values() if node.get("isDisabled", False))
        
        message = f"🖥️ *Список серверов*\n\n"
        message += f"📊 *Статистика:* {online_count}/{total_count} онлайн"
        if disabled_count > 0:
            message += f" | {disabled_count} отключено"
        message += "\n\n"
        message += "Выберите сервер для просмотра подробной информации:"

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка серверов.",
            reply_markup=reply_markup
        )

    return NODE_MENU

async def handle_node_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle node selection from list"""
    query = update.callback_query
    await query.answer()
    
    # Extract node ID from callback data
    if query.data.startswith("select_node_"):
        node_id = query.data.replace("select_node_", "")
        from modules.handlers.nodes.node_details import show_node_details
        return await show_node_details(update, context, node_id)
    
    return NODE_MENU

async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Handle pagination for node list"""
    try:
        nodes_response = await NodeAPI.get_all_nodes()
        if not nodes_response or 'response' not in nodes_response:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Серверы не найдены или ошибка при получении списка.",
                reply_markup=reply_markup
            )
            return NODE_MENU

        nodes = nodes_response['response']

        # Format items for SelectionHelper
        items = []
        for node in nodes:
            status_emoji = "🟢" if node.get("isConnected") and not node.get("isDisabled") else "🔴"
            
            description = f"{status_emoji} {node['address']}:{node['port']}"
            
            if node.get("usersOnline") is not None:
                description += f" | 👥 {node['usersOnline']}"
            
            if node.get("trafficLimitBytes"):
                used = node.get('trafficUsedBytes', 0)
                limit = node.get('trafficLimitBytes', 0)
                if limit > 0:
                    percentage = (used / limit) * 100
                    description += f" | 📊 {percentage:.1f}%"

            items.append({
                'id': node['uuid'],
                'name': node['name'],
                'description': description
            })

        # Use SelectionHelper for pagination
        helper = SelectionHelper(
            title="🖥️ Выберите сервер",
            items=items,
            callback_prefix="select_node",
            back_callback="back_to_nodes",
            items_per_page=6
        )

        keyboard = helper.get_keyboard(page=page)
        message = helper.get_message(page=page)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error handling node pagination: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка серверов.",
            reply_markup=reply_markup
        )

    return NODE_MENU