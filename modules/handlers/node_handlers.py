from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import MAIN_MENU, NODE_MENU, EDIT_NODE, EDIT_NODE_FIELD, CREATE_NODE, SEARCH_NODES
from modules.utils.auth import check_authorization
from modules.utils.formatters import safe_edit_message
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
    keyboard = [
        [
            InlineKeyboardButton("📋 Список серверов", callback_data="list_nodes"),
            InlineKeyboardButton("➕ Добавить сервер", callback_data="add_node")
        ],
        [
            InlineKeyboardButton("🔍 Поиск сервера", callback_data="search_nodes"),
            InlineKeyboardButton("📊 Статистика", callback_data="nodes_usage")
        ],
        [
            InlineKeyboardButton("📜 Сертификат панели", callback_data="get_panel_certificate"),
            InlineKeyboardButton("🔄 Перезапуск всех", callback_data="restart_all_nodes")
        ],
        [
            InlineKeyboardButton("🖥️ Системная информация", callback_data="nodes_system_info"),
            InlineKeyboardButton("📈 Мониторинг", callback_data="nodes_monitoring")
        ],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🖥️ *Управление серверами*\n\n"
    message += "🎛️ *Доступные функции:*\n"
    message += "• 📋 Просмотр всех серверов с статусами\n"
    message += "• ➕ Добавление новых серверов\n"
    message += "• 🔍 Поиск по названию или адресу\n"
    message += "• 📊 Статистика использования в реальном времени\n"
    message += "• 🔄 Массовые операции\n"
    message += "• 📜 Получение сертификата для настройки\n\n"
    message += "Выберите действие:"

    await safe_edit_message(update.callback_query, message, reply_markup, "Markdown")
    return NODE_MENU

async def handle_nodes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle nodes menu selection with comprehensive routing"""
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        # Basic operations
        if data == "list_nodes":
            return await list_nodes(update, context)
        elif data == "add_node":
            return await start_create_node(update, context)
        elif data == "search_nodes":
            return await setup_node_search(update, context)
        
        # Statistics and monitoring
        elif data == "nodes_usage":
            return await show_nodes_usage(update, context)
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
            return await handle_node_pagination(update, context, page)
        
        # Navigation
        elif data == "back_to_nodes":
            return await show_nodes_menu(update, context)
        elif data == "back_to_main":
            return await show_main_menu(update, context)
        
        # Default fallback
        else:
            logger.warning(f"Unknown nodes menu action: {data}")
            return await show_nodes_menu(update, context)

    except Exception as e:
        logger.error(f"Error in nodes menu handler for {data}: {e}")
        await query.answer("❌ Произошла ошибка при обработке запроса", show_alert=True)
        return await show_nodes_menu(update, context)

async def setup_node_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup node search"""
    message = "🔍 *Поиск серверов*\n\n"
    message += "Введите часть названия сервера или его адрес для поиска:\n\n"
    message += "💡 *Примеры поиска:*\n"
    message += "• `Germany` - поиск по названию\n"
    message += "• `192.168` - поиск по IP адресу\n"
    message += "• `server1` - поиск по части названия\n\n"
    message += "Минимум 2 символа для поиска."

    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_nodes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    context.user_data["search_type"] = "nodes"
    return SEARCH_NODES

async def show_nodes_system_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system information for all nodes"""
    try:
        from modules.api.nodes import NodeAPI
        from modules.utils.formatters import format_bytes
        
        await update.callback_query.edit_message_text("🖥️ Загрузка системной информации...")
        
        nodes_response = await NodeAPI.get_all_nodes()
        if not nodes_response or 'response' not in nodes_response:
            raise Exception("Не удалось получить список серверов")
        
        nodes = nodes_response['response']
        
        if not nodes:
            message = "ℹ️ Серверы не найдены."
        else:
            total_nodes = len(nodes)
            online_nodes = sum(1 for node in nodes if node.get('isConnected'))
            disabled_nodes = sum(1 for node in nodes if node.get('isDisabled'))
            xray_running = sum(1 for node in nodes if node.get('isXrayRunning'))
            
            message = f"🖥️ *Системная информация серверов*\n\n"
            message += f"📊 *Общая статистика:*\n"
            message += f"• Всего серверов: `{total_nodes}`\n"
            message += f"• 🟢 Онлайн: `{online_nodes}`\n"
            message += f"• 🔴 Офлайн: `{total_nodes - online_nodes}`\n"
            message += f"• ❌ Отключено: `{disabled_nodes}`\n"
            message += f"• ⚡ Xray запущен: `{xray_running}`\n\n"
            
            # Group by country
            countries = {}
            for node in nodes:
                country = node.get('countryCode', 'XX')
                if country not in countries:
                    countries[country] = {'total': 0, 'online': 0}
                countries[country]['total'] += 1
                if node.get('isConnected'):
                    countries[country]['online'] += 1
            
            if countries:
                message += f"🌍 *По странам:*\n"
                for country, stats in sorted(countries.items()):
                    message += f"• {country}: {stats['online']}/{stats['total']} онлайн\n"

        keyboard = [
            [InlineKeyboardButton("📊 Детальная статистика", callback_data="nodes_usage")],
            [InlineKeyboardButton("📈 Мониторинг", callback_data="nodes_monitoring")],
            [InlineKeyboardButton("🔄 Обновить", callback_data="nodes_system_info")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        return NODE_MENU

    except Exception as e:
        logger.error(f"Error showing nodes system info: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке системной информации: {str(e)}",
            reply_markup=reply_markup
        )
        return NODE_MENU

async def show_nodes_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show real-time monitoring for nodes"""
    try:
        from modules.api.nodes import NodeAPI
        from modules.utils.formatters import format_bytes
        
        await update.callback_query.edit_message_text("📈 Загрузка мониторинга...")
        
        # Get realtime usage data
        usage_data = await NodeAPI.get_nodes_realtime_usage()
        
        if not usage_data:
            message = "📈 *Мониторинг серверов*\n\n"
            message += "ℹ️ Данные мониторинга временно недоступны."
        else:
            message = f"📈 *Мониторинг серверов в реальном времени*\n\n"
            
            total_download_speed = 0
            total_upload_speed = 0
            active_nodes = 0
            
            for node_data in usage_data:
                download_speed = node_data.get('downloadSpeedBps', 0)
                upload_speed = node_data.get('uploadSpeedBps', 0)
                
                total_download_speed += download_speed
                total_upload_speed += upload_speed
                
                if download_speed > 0 or upload_speed > 0:
                    active_nodes += 1
            
            message += f"🚀 *Общая активность:*\n"
            message += f"• ⬇️ Скачивание: `{format_bytes(total_download_speed)}/с`\n"
            message += f"• ⬆️ Загрузка: `{format_bytes(total_upload_speed)}/с`\n"
            message += f"• 📡 Активных серверов: `{active_nodes}`\n\n"
            
            # Show top 5 most active nodes
            if usage_data:
                sorted_nodes = sorted(usage_data, 
                                    key=lambda x: x.get('totalSpeedBps', 0), 
                                    reverse=True)[:5]
                
                if sorted_nodes and sorted_nodes[0].get('totalSpeedBps', 0) > 0:
                    message += f"🔥 *Самые активные серверы:*\n"
                    for i, node in enumerate(sorted_nodes, 1):
                        if node.get('totalSpeedBps', 0) > 0:
                            name = node.get('nodeName', 'Unknown')[:15]
                            speed = format_bytes(node.get('totalSpeedBps', 0))
                            message += f"{i}. `{name}`: {speed}/с\n"

        keyboard = [
            [InlineKeyboardButton("📊 Полная статистика", callback_data="nodes_usage")],
            [InlineKeyboardButton("🔄 Обновить", callback_data="nodes_monitoring")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        return NODE_MENU

    except Exception as e:
        logger.error(f"Error showing nodes monitoring: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке мониторинга: {str(e)}",
            reply_markup=reply_markup
        )
        return NODE_MENU

async def confirm_restart_all_nodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm restart all nodes operation"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, перезапустить все", callback_data="confirm_restart_all"),
            InlineKeyboardButton("❌ Отмена", callback_data="back_to_nodes")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "⚠️ *Подтверждение массового перезапуска*\n\n"
    message += "Вы уверены, что хотите перезапустить **ВСЕ** серверы?\n\n"
    message += "🔴 *Внимание:*\n"
    message += "• Все активные соединения будут разорваны\n"
    message += "• Серверы будут недоступны на время перезапуска\n"
    message += "• Операция может занять несколько минут\n\n"
    message += "Продолжить?"

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
        
        if result and result.get("eventSent"):
            message = "✅ *Команда перезапуска отправлена*\n\n"
            message += "📤 Команда на перезапуск всех серверов успешно отправлена.\n\n"
            message += "⏳ *Процесс может занять:*\n"
            message += "• 30-60 секунд для перезапуска сервисов\n"
            message += "• До 2-3 минут для полного восстановления\n\n"
            message += "🔍 Проверьте статус серверов через несколько минут."
        else:
            message = "❌ *Ошибка при отправке команды*\n\n"
            message += "Не удалось отправить команду перезапуска.\n"
            message += "Попробуйте еще раз или перезапустите серверы по отдельности."

        keyboard = [
            [InlineKeyboardButton("📊 Проверить статус", callback_data="nodes_system_info")],
            [InlineKeyboardButton("🔙 К меню серверов", callback_data="back_to_nodes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        return NODE_MENU

    except Exception as e:
        logger.error(f"Error restarting all nodes: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            f"❌ Ошибка при перезапуске серверов: {str(e)}",
            reply_markup=reply_markup
        )
        return NODE_MENU

async def handle_node_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Handle pagination for node list"""
    # This will be handled by the node_list module
    from modules.handlers.nodes.node_list import handle_pagination
    return await handle_pagination(update, context, page)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for node operations"""
    search_type = context.user_data.get("search_type")
    
    if search_type == "nodes":
        from modules.handlers.nodes.node_search import handle_search_input
        return await handle_search_input(update, context)
    elif context.user_data.get("node_creation_step"):
        return await handle_node_creation(update, context)
    elif context.user_data.get("editing_field"):
        return await handle_node_field_input(update, context)
    else:
        await update.message.reply_text(
            "❌ Неожиданный ввод текста. Используйте кнопки меню для навигации.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 К серверам", callback_data="back_to_nodes")
            ]])
        )
        return await show_nodes_menu(update, context)

# Export functions for use in conversation handler
__all__ = [
    'show_nodes_menu',
    'handle_nodes_menu',
    'handle_text_input',
    'handle_node_pagination',
    'setup_node_search',
    'show_nodes_system_info',
    'show_nodes_monitoring',
    'confirm_restart_all_nodes',
    'restart_all_nodes'
]