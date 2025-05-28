from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import NODE_MENU, SELECTING_NODE
from modules.api.nodes import NodeAPI
from modules.utils.formatters import escape_markdown, format_bytes
from modules.utils.selection_helpers import SelectionHelper

logger = logging.getLogger(__name__)

async def handle_node_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search input for nodes"""
    search_type = context.user_data.get("search_type")
    search_value = update.message.text.strip()
    
    try:
        if search_type == "name":
            nodes_response = await NodeAPI.search_nodes_by_name(search_value)
        elif search_type == "address":
            nodes_response = await NodeAPI.search_nodes_by_address(search_value)
        elif search_type == "country":
            nodes_response = await NodeAPI.search_nodes_by_country(search_value)
        elif search_type == "status":
            # Search by status (online/offline/enabled/disabled)
            nodes_response = await NodeAPI.get_all_nodes()
            if nodes_response and 'response' in nodes_response:
                all_nodes = nodes_response['response']
                # Filter by status
                search_lower = search_value.lower()
                filtered_nodes = []
                
                for node in all_nodes:
                    if search_lower in ['online', 'онлайн'] and node.get('isNodeOnline'):
                        filtered_nodes.append(node)
                    elif search_lower in ['offline', 'оффлайн'] and not node.get('isNodeOnline'):
                        filtered_nodes.append(node)
                    elif search_lower in ['enabled', 'включен'] and not node.get('isDisabled'):
                        filtered_nodes.append(node)
                    elif search_lower in ['disabled', 'отключен'] and node.get('isDisabled'):
                        filtered_nodes.append(node)
                    elif search_lower in ['connected', 'подключен'] and node.get('isConnected'):
                        filtered_nodes.append(node)
                    elif search_lower in ['disconnected', 'отключен'] and not node.get('isConnected'):
                        filtered_nodes.append(node)
                
                nodes_response = {'response': filtered_nodes}
            else:
                nodes_response = None
        else:
            await update.message.reply_text("❌ Неизвестный тип поиска.")
            return NODE_MENU
        
        if not nodes_response or 'response' not in nodes_response:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ Серверы по запросу '{search_value}' не найдены.",
                reply_markup=reply_markup
            )
            return NODE_MENU
        
        nodes = nodes_response['response']
        
        if len(nodes) == 1:
            # Single node found - show details
            return await show_single_node_result(update, context, nodes[0])
        else:
            # Multiple nodes found - show list
            return await show_multiple_nodes_result(update, context, nodes, search_value)
            
    except Exception as e:
        logger.error(f"Error in node search: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ Ошибка при поиске: {str(e)}",
            reply_markup=reply_markup
        )
        return NODE_MENU

async def show_single_node_result(update: Update, context: ContextTypes.DEFAULT_TYPE, node):
    """Show single node search result"""
    from modules.handlers.nodes.node_details import show_node_details
    
    # Send confirmation message first
    keyboard = [[InlineKeyboardButton("👁️ Просмотреть", callback_data=f"view_node_{node['uuid']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status_emoji = "🟢" if node.get("isConnected") and not node.get("isDisabled") else "🔴"
    
    message = f"✅ *Найден сервер:*\n\n"
    message += f"🖥️ *Название:* {escape_markdown(node['name'])}\n"
    message += f"🌐 *Адрес:* {escape_markdown(node['address'])}:{node['port']}\n"
    message += f"📊 *Статус:* {status_emoji}\n"
    
    if node.get('countryCode'):
        message += f"🌍 *Страна:* {node['countryCode']}\n"
    
    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def show_multiple_nodes_result(update: Update, context: ContextTypes.DEFAULT_TYPE, nodes, search_value):
    """Show multiple nodes search results"""
    message = f"🔍 *Результаты поиска по запросу:* `{search_value}`\n\n"
    message += f"Найдено серверов: *{len(nodes)}*\n\n"
    
    # Group nodes by status for better overview
    online_nodes = [n for n in nodes if n.get('isNodeOnline') and not n.get('isDisabled')]
    offline_nodes = [n for n in nodes if not n.get('isNodeOnline') or n.get('isDisabled')]
    
    if online_nodes:
        message += f"🟢 *Онлайн ({len(online_nodes)}):*\n"
        for node in online_nodes[:5]:  # Show first 5
            message += f"• {escape_markdown(node['name'])} ({escape_markdown(node['address'])})\n"
        if len(online_nodes) > 5:
            message += f"... и еще {len(online_nodes) - 5}\n"
        message += "\n"
    
    if offline_nodes:
        message += f"🔴 *Оффлайн/Отключенные ({len(offline_nodes)}):*\n"
        for node in offline_nodes[:5]:  # Show first 5
            message += f"• {escape_markdown(node['name'])} ({escape_markdown(node['address'])})\n"
        if len(offline_nodes) > 5:
            message += f"... и еще {len(offline_nodes) - 5}\n"
        message += "\n"
    
    # Create selection keyboard
    keyboard = []
    
    # Show up to 10 nodes in keyboard
    for i, node in enumerate(nodes[:10]):
        status_emoji = "🟢" if node.get("isConnected") and not node.get("isDisabled") else "🔴"
        name = node['name']
        if len(name) > 25:
            name = name[:22] + "..."
        
        keyboard.append([InlineKeyboardButton(
            f"{status_emoji} {name}",
            callback_data=f"view_node_{node['uuid']}"
        )])
    
    # Add pagination if more than 10 nodes
    if len(nodes) > 10:
        context.user_data["search_results"] = nodes
        context.user_data["search_page"] = 0
        context.user_data["search_query"] = search_value
        
        keyboard.append([
            InlineKeyboardButton("⬅️ Пред", callback_data="search_prev_page"),
            InlineKeyboardButton(f"1/{(len(nodes) + 9) // 10}", callback_data="search_page_info"),
            InlineKeyboardButton("След ➡️", callback_data="search_next_page")
        ])
    
    # Add action buttons
    keyboard.extend([
        [InlineKeyboardButton("🔍 Новый поиск", callback_data="search_nodes")],
        [InlineKeyboardButton("🔙 К серверам", callback_data="back_to_nodes")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def handle_search_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search results pagination"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    search_results = context.user_data.get("search_results", [])
    current_page = context.user_data.get("search_page", 0)
    search_query = context.user_data.get("search_query", "")
    
    if not search_results:
        await query.edit_message_text("❌ Результаты поиска не найдены.")
        return NODE_MENU
    
    total_pages = (len(search_results) + 9) // 10
    
    if data == "search_next_page" and current_page < total_pages - 1:
        current_page += 1
    elif data == "search_prev_page" and current_page > 0:
        current_page -= 1
    
    context.user_data["search_page"] = current_page
    
    # Calculate range for current page
    start_idx = current_page * 10
    end_idx = min(start_idx + 10, len(search_results))
    page_results = search_results[start_idx:end_idx]
    
    message = f"🔍 *Результаты поиска:* `{search_query}`\n\n"
    message += f"Страница {current_page + 1} из {total_pages}\n"
    message += f"Показано {start_idx + 1}-{end_idx} из {len(search_results)}\n\n"
    
    # Create keyboard for current page
    keyboard = []
    
    for node in page_results:
        status_emoji = "🟢" if node.get("isConnected") and not node.get("isDisabled") else "🔴"
        name = node['name']
        if len(name) > 25:
            name = name[:22] + "..."
        
        keyboard.append([InlineKeyboardButton(
            f"{status_emoji} {name}",
            callback_data=f"view_node_{node['uuid']}"
        )])
    
    # Pagination controls
    pagination_row = []
    if current_page > 0:
        pagination_row.append(InlineKeyboardButton("⬅️ Пред", callback_data="search_prev_page"))
    
    pagination_row.append(InlineKeyboardButton(
        f"{current_page + 1}/{total_pages}",
        callback_data="search_page_info"
    ))
    
    if current_page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton("След ➡️", callback_data="search_next_page"))
    
    keyboard.append(pagination_row)
    
    # Action buttons
    keyboard.extend([
        [InlineKeyboardButton("🔍 Новый поиск", callback_data="search_nodes")],
        [InlineKeyboardButton("🔙 К серверам", callback_data="back_to_nodes")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def show_node_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show node search options"""
    keyboard = [
        [InlineKeyboardButton("🏷️ По названию", callback_data="search_node_name")],
        [InlineKeyboardButton("🌐 По адресу", callback_data="search_node_address")],
        [InlineKeyboardButton("🌍 По стране", callback_data="search_node_country")],
        [InlineKeyboardButton("📊 По статусу", callback_data="search_node_status")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = "🔍 *Поиск серверов*\n\n"
    message += "Выберите тип поиска:\n\n"
    message += "🏷️ *По названию* - поиск по имени сервера\n"
    message += "🌐 *По адресу* - поиск по IP адресу или домену\n"
    message += "🌍 *По стране* - поиск по коду страны\n"
    message += "📊 *По статусу* - поиск по состоянию (онлайн/оффлайн/включен/отключен)\n"
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU

async def setup_node_search(update: Update, context: ContextTypes.DEFAULT_TYPE, search_type: str):
    """Setup node search by type"""
    context.user_data["search_type"] = search_type
    
    search_prompts = {
        "name": "🏷️ Введите название сервера для поиска:",
        "address": "🌐 Введите IP адрес или домен для поиска:",
        "country": "🌍 Введите код страны (например: US, RU, DE):",
        "status": "📊 Введите статус для поиска:\n• online/онлайн\n• offline/оффлайн\n• enabled/включен\n• disabled/отключен\n• connected/подключен\n• disconnected/отсоединен"
    }
    
    prompt = search_prompts.get(search_type, "Введите поисковый запрос:")
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel_search")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=prompt,
        reply_markup=reply_markup
    )
    
    return NODE_MENU
