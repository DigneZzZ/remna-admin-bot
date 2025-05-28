from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from datetime import datetime, timedelta

from modules.config import MAIN_MENU, NODE_MENU, EDIT_NODE, EDIT_NODE_FIELD, CREATE_NODE, SEARCH_NODES
from modules.utils.auth import check_authorization
from modules.utils.formatters import safe_edit_message, format_bytes, escape_markdown
from modules.handlers.start_handler import show_main_menu

# Import node sub-modules
from modules.handlers.nodes.node_list import list_nodes, handle_node_selection
from modules.handlers.nodes.node_details import show_node_details, handle_node_action
from modules.handlers.nodes.node_edit import start_edit_node, handle_edit_field_selection, handle_edit_field_value, save_node_changes
from modules.handlers.nodes.node_create import start_create_node, handle_create_node_input, finish_create_node, execute_create_node
from modules.handlers.nodes.node_actions import enable_node, disable_node, restart_node, delete_node
from modules.handlers.nodes.node_stats import show_node_stats, show_node_traffic_graph
from modules.handlers.nodes.node_certificate import show_node_certificate
from modules.handlers.nodes.node_search import handle_node_search_input, show_node_search_menu, setup_node_search, handle_search_pagination

logger = logging.getLogger(__name__)

async def show_nodes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show enhanced nodes menu with comprehensive options"""
    if not update.effective_user or not check_authorization(update.effective_user.id):
        if update.callback_query:
            await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END

    message = "🖥️ *Управление серверами*\n\n"
    message += "Выберите действие для управления серверами:"

    keyboard = [
        [
            InlineKeyboardButton("📋 Список серверов", callback_data="list_nodes"),
            InlineKeyboardButton("➕ Добавить сервер", callback_data="add_node")
        ],
        [
            InlineKeyboardButton("🔍 Поиск серверов", callback_data="search_nodes"),
            InlineKeyboardButton("📊 Статистика серверов", callback_data="nodes_usage")
        ],
        [
            InlineKeyboardButton("🖥️ Системная информация", callback_data="nodes_system_info"),
            InlineKeyboardButton("📈 Мониторинг серверов", callback_data="nodes_monitoring")
        ],
        [
            InlineKeyboardButton("🔑 Сертификат панели", callback_data="get_panel_certificate"),
            InlineKeyboardButton("🔄 Перезапустить все", callback_data="restart_all_nodes")
        ],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await safe_edit_message(
            update.callback_query,
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error showing nodes menu: {e}")
        
    return NODE_MENU

async def handle_nodes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle nodes menu selection with comprehensive routing"""
    query = update.callback_query
    if not query:
        return ConversationHandler.END
        
    await query.answer()
    
    data = query.data
    if not data:
        return NODE_MENU
    
    try:
        # Main node operations
        if data == "list_nodes":
            return await list_nodes(update, context)
        elif data == "add_node":
            return await start_create_node(update, context)
        elif data == "search_nodes":
            return await setup_node_search(update, context, "name")
        
        # Statistics and monitoring
        elif data == "nodes_usage":
            return await show_nodes_stats(update, context)
        elif data == "nodes_system_info":
            return await show_nodes_system_info(update, context)
        elif data == "nodes_monitoring":
            return await show_nodes_monitoring(update, context)
        
        # Certificate operations
        elif data == "get_panel_certificate":
            return await show_node_certificate(update, context)
        
        # Mass operations
        elif data == "restart_all_nodes":
            return await confirm_restart_all_nodes(update, context)
        elif data == "confirm_restart_all":
            return await restart_all_nodes(update, context)
        
        # Node-specific operations
        elif data.startswith("view_node_"):
            uuid = data.split("_", 2)[2]
            return await show_node_details(update, context, uuid)
        elif data.startswith("select_node_"):
            node_id = data.replace("select_node_", "")
            return await show_node_details(update, context, node_id)
        elif data.startswith("enable_node_"):
            uuid = data.split("_", 2)[2]
            return await enable_node(update, context, uuid)
        elif data.startswith("disable_node_"):
            uuid = data.split("_", 2)[2]
            return await disable_node(update, context, uuid)
        elif data.startswith("restart_node_"):
            uuid = data.split("_", 2)[2]
            return await restart_node(update, context, uuid)
        elif data.startswith("node_stats_"):
            uuid = data.split("_", 2)[2]
            return await show_node_stats(update, context, uuid)
        elif data.startswith("edit_node_"):
            uuid = data.split("_", 2)[2]
            return await start_edit_node(update, context, uuid)
        elif data.startswith("show_certificate_"):
            return await show_node_certificate(update, context)
        
        # Pagination
        elif data.startswith("page_nodes_"):
            page = int(data.split("_")[2])
            return await list_nodes(update, context)
        
        # Navigation
        elif data == "back_to_main":
            return await show_main_menu(update, context)
        elif data == "back_to_nodes":
            return await show_nodes_menu(update, context)
        
        return NODE_MENU
        
    except Exception as e:
        logger.error(f"Error handling nodes menu: {e}")
        await query.answer("❌ Произошла ошибка при обработке запроса", show_alert=True)
        return await show_nodes_menu(update, context)

async def show_nodes_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show comprehensive node statistics"""
    try:
        from modules.api.nodes import NodeAPI
        
        await update.callback_query.edit_message_text("📊 Загрузка статистики серверов...")
        
        # Get nodes data
        nodes_response = await NodeAPI.get_all_nodes()
        if not nodes_response or 'response' not in nodes_response:
            await update.callback_query.edit_message_text(
                "❌ Не удалось получить данные о серверах.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]])
            )
            return NODE_MENU
        
        nodes = nodes_response['response']
        
        if not nodes:
            await update.callback_query.edit_message_text(
                "📊 *Статистика серверов*\n\n❌ Серверы не найдены.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]])
            )
            return NODE_MENU
        
        # Calculate statistics
        total_nodes = len(nodes)
        online_nodes = sum(1 for node in nodes if node.get('isConnected', False))
        enabled_nodes = sum(1 for node in nodes if not node.get('isDisabled', False))
        
        # Build message
        message = "📊 *Статистика серверов*\n\n"
        message += f"🖥️ *Общее количество*: {total_nodes}\n"
        message += f"🟢 *Онлайн*: {online_nodes}\n"
        message += f"🔴 *Офлайн*: {total_nodes - online_nodes}\n"
        message += f"✅ *Включено*: {enabled_nodes}\n"
        message += f"❌ *Отключено*: {total_nodes - enabled_nodes}\n\n"
        
        # Country distribution
        countries = {}
        for node in nodes:
            country = node.get('countryCode', 'Unknown')
            countries[country] = countries.get(country, 0) + 1
        
        if countries:
            message += "🌍 *Распределение по странам*:\n"
            for country, count in sorted(countries.items()):
                message += f"  • {country}: {count}\n"
        
        keyboard = [
            [InlineKeyboardButton("📈 Мониторинг", callback_data="nodes_monitoring")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing nodes stats: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при загрузке статистики серверов.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]])
        )
    
    return NODE_MENU

async def show_nodes_system_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system information for all nodes"""
    try:
        from modules.api.nodes import NodeAPI
        
        await update.callback_query.edit_message_text("🖥️ Загрузка системной информации...")
        
        nodes_response = await NodeAPI.get_all_nodes()
        if not nodes_response or 'response' not in nodes_response:
            await update.callback_query.edit_message_text(
                "❌ Не удалось получить данные о серверах.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]])
            )
            return NODE_MENU
        
        nodes = nodes_response['response']
        
        message = "🖥️ *Системная информация серверов*\n\n"
        
        if not nodes:
            message += "❌ Серверы не найдены."
        else:
            for i, node in enumerate(nodes[:10], 1):  # Limit to 10 nodes
                name = escape_markdown(node.get('name', 'Unknown'))
                status = "🟢 Онлайн" if node.get('isConnected', False) else "🔴 Офлайн"
                version = escape_markdown(node.get('version', 'Unknown'))
                uptime = escape_markdown(node.get('uptime', 'Unknown'))
                
                message += f"{i}\\. *{name}*\n"
                message += f"   Status: {status}\n"
                message += f"   Version: `{version}`\n"
                message += f"   Uptime: `{uptime}`\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error showing nodes system info: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при загрузке системной информации.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]])
        )
    
    return NODE_MENU

async def show_nodes_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show real-time monitoring for nodes"""
    try:
        from modules.api.nodes import NodeAPI
        
        await update.callback_query.edit_message_text("📈 Загрузка мониторинга...")
        
        # Get realtime usage
        usage_response = await NodeAPI.get_nodes_realtime_usage()
        if not usage_response or 'response' not in usage_response:
            await update.callback_query.edit_message_text(
                "❌ Не удалось получить данные мониторинга.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]])
            )
            return NODE_MENU
        
        usage_data = usage_response['response']
        
        message = "📈 *Мониторинг серверов в реальном времени*\n\n"
        
        if not usage_data:
            message += "❌ Данные мониторинга недоступны."
        else:
            # Calculate totals
            total_download_speed = 0
            total_upload_speed = 0
            
            for node_data in usage_data:
                download_speed = node_data.get('downloadSpeedBps', 0)
                upload_speed = node_data.get('uploadSpeedBps', 0)
                total_download_speed += download_speed
                total_upload_speed += upload_speed
            
            message += f"📊 *Общая скорость*:\n"
            message += f"⬇️ Download: {format_bytes(total_download_speed)}/s\n"
            message += f"⬆️ Upload: {format_bytes(total_upload_speed)}/s\n\n"
            
            # Show top active nodes
            active_nodes = [node for node in usage_data if node.get('totalSpeedBps', 0) > 0]
            if active_nodes:
                sorted_nodes = sorted(
                    active_nodes,
                    key=lambda x: x.get('totalSpeedBps', 0),
                    reverse=True
                )
                
                if sorted_nodes and sorted_nodes[0].get('totalSpeedBps', 0) > 0:
                    message += "🔥 *Наиболее активные серверы*:\n"
                    for i, node in enumerate(sorted_nodes[:5], 1):
                        if node.get('totalSpeedBps', 0) > 0:
                            name = node.get('nodeName', 'Unknown')[:15]
                            speed = format_bytes(node.get('totalSpeedBps', 0))
                            message += f"{i}. `{name}`: {speed}/с\n"
            else:
                message += "💤 В данный момент активности нет."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="nodes_monitoring")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing nodes monitoring: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при загрузке мониторинга.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]])
        )
    
    return NODE_MENU

async def confirm_restart_all_nodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm restart all nodes operation"""
    message = "⚠️ *Подтверждение операции*\n\n"
    message += "Вы действительно хотите перезапустить ВСЕ серверы?\n\n"
    message += "🔄 Это может временно прервать соединения пользователей.\n"
    message += "⏱️ Операция может занять несколько минут."

    keyboard = [
        [
            InlineKeyboardButton("✅ Да, перезапустить", callback_data="confirm_restart_all"),
            InlineKeyboardButton("❌ Отмена", callback_data="back_to_nodes")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return NODE_MENU

async def restart_all_nodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart all nodes"""
    try:
        from modules.api.nodes import NodeAPI
        
        await update.callback_query.edit_message_text("🔄 Отправка команды перезапуска...")
        
        result = await NodeAPI.restart_all_nodes()
        
        if result and 'response' in result:
            message = "✅ *Команда перезапуска отправлена*\n\n"
            message += "🔄 Все серверы получили команду перезапуска.\n"
            message += "⏱️ Процесс может занять несколько минут.\n\n"
            message += "💡 Вы можете проверить статус серверов в мониторинге."
        else:
            message = "❌ *Ошибка при перезапуске*\n\n"
            message += "Не удалось отправить команду перезапуска.\n"
            message += "Попробуйте позже или обратитесь к администратору."

        keyboard = [
            [InlineKeyboardButton("📈 Проверить статус", callback_data="nodes_monitoring")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error restarting all nodes: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при выполнении операции.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]])
        )
    
    return NODE_MENU

async def handle_node_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for various node operations"""
    
    # Check if this is a search operation
    search_type = context.user_data.get("search_type")
    if search_type == "nodes":
        return await handle_node_search_input(update, context)
    
    # Check if this is node creation
    elif context.user_data.get("node_creation_step"):
        return await handle_create_node_input(update, context)
    
    # Check if this is node editing
    elif context.user_data.get("editing_field"):
        return await handle_edit_field_value(update, context)
    
    # Default fallback
    else:
        await update.message.reply_text(
            "❌ Неожиданный ввод. Пожалуйста, используйте кнопки меню.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 К серверам", callback_data="back_to_nodes")]])
        )
        return NODE_MENU

# Export functions for conversation handler
__all__ = [
    'show_nodes_menu',
    'handle_nodes_menu', 
    'handle_node_text_input',
    'show_nodes_stats',
    'show_nodes_system_info',
    'show_nodes_monitoring',
    'confirm_restart_all_nodes',
    'restart_all_nodes'
]
