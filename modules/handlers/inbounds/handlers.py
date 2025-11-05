from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from modules.config import MAIN_MENU, INBOUND_MENU
from modules.api.inbounds import InboundAPI
from modules.api.users import UserAPI
from modules.api.nodes import NodeAPI
from modules.utils.formatters import format_inbound_details, escape_markdown
from modules.utils.selection_helpers import SelectionHelper
from modules.handlers.core.start import show_main_menu

logger = logging.getLogger(__name__)

# Constants for better organization
class InboundConstants:
    """Constants for inbound management"""
    class CallbackData:
        LIST_INBOUNDS = "list_inbounds"
        LIST_FULL_INBOUNDS = "list_full_inbounds"
        LIST_INBOUNDS_STATS = "list_inbounds_stats"
        FILTER_INBOUNDS = "filter_inbounds"
        VIEW_INBOUND = "view_inbound"
        INBOUND_CONFIG = "inbound_config"
        INBOUND_USERS = "inbound_users"
        INBOUND_NODES = "inbound_nodes"
        INBOUND_STATS = "inbound_stats"
        DEBUG_USERS = "debug_users"
        BACK_TO_INBOUNDS = "back_to_inbounds"
        BACK_TO_MAIN = "back_to_main"
    
    class Messages:
        TITLE = "🔌 *Управление Inbounds*"
        LOADING = "🔄 Загрузка данных..."
        NO_INBOUNDS = "❌ Inbounds не найдены или ошибка при получении списка."
        ERROR_LOADING = "❌ Произошла ошибка при загрузке данных."
        SELECT_ACTION = "Выберите действие:"
        SELECT_INBOUND = "Выберите Inbound для просмотра подробной информации:"
        
    class Emojis:
        INBOUND = "🔌"
        PORT = "🔢"
        TYPE = "🏷️"
        USERS = "👥"
        NODES = "🖥️"
        STATS = "📊"
        CONFIG = "⚙️"
        BACK = "🔙"
        REFRESH = "🔄"
        FILTER = "🔍"
        DETAILS = "📋"
        ACTIVE = "✅"
        INACTIVE = "❌"
        LOADING = "⏳"

async def show_inbounds_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show enhanced inbounds menu with statistics"""
    try:
        # Get basic statistics
        inbounds = await InboundAPI.get_inbounds()
        total_inbounds = len(inbounds) if inbounds else 0
        
        # Count by type
        type_counts = {}
        if inbounds:
            for inbound in inbounds:
                inbound_type = inbound.get('type', 'Unknown')
                type_counts[inbound_type] = type_counts.get(inbound_type, 0) + 1
        
        # Create enhanced menu
        keyboard = [
            [InlineKeyboardButton(f"📋 Список Inbounds ({total_inbounds})", callback_data=InboundConstants.CallbackData.LIST_INBOUNDS)],
            [InlineKeyboardButton(f"📊 Детальный просмотр", callback_data=InboundConstants.CallbackData.LIST_FULL_INBOUNDS)],
            [InlineKeyboardButton(f"📈 Статистика и аналитика", callback_data=InboundConstants.CallbackData.LIST_INBOUNDS_STATS)],
            [InlineKeyboardButton(f"🔍 Фильтры и поиск", callback_data=InboundConstants.CallbackData.FILTER_INBOUNDS)],
            [InlineKeyboardButton(f"🔄 Обновить данные", callback_data="refresh_inbounds")],
            [InlineKeyboardButton(f"🔍 Отладка пользователей", callback_data=InboundConstants.CallbackData.DEBUG_USERS)],
            [InlineKeyboardButton(f"🔙 Назад в главное меню", callback_data=InboundConstants.CallbackData.BACK_TO_MAIN)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Create enhanced message with statistics
        message = f"{InboundConstants.Messages.TITLE}\n\n"
        message += f"📊 *Общая статистика:*\n"
        message += f"  • Всего Inbounds: {total_inbounds}\n"
        
        if type_counts:
            message += f"  • По типам:\n"
            for inbound_type, count in type_counts.items():
                message += f"    - {inbound_type}: {count}\n"
        
        message += f"\n{InboundConstants.Messages.SELECT_ACTION}"

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing inbounds menu: {e}")
        # Fallback to simple menu
        keyboard = [
            [InlineKeyboardButton("📋 Список Inbounds", callback_data=InboundConstants.CallbackData.LIST_INBOUNDS)],
            [InlineKeyboardButton("📊 Детальный просмотр", callback_data=InboundConstants.CallbackData.LIST_FULL_INBOUNDS)],
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data=InboundConstants.CallbackData.BACK_TO_MAIN)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = f"{InboundConstants.Messages.TITLE}\n\n{InboundConstants.Messages.SELECT_ACTION}"

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def handle_inbounds_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle enhanced inbounds menu selection"""
    query = update.callback_query
    await query.answer()

    data = query.data
    logger.info(f"=== INBOUND MENU HANDLER ===")
    logger.info(f"Handling inbound menu callback: {data}")
    logger.info(f"Current state: {context.user_data.get('conversation_state', 'unknown')}")
    logger.info(f"Available constants: LIST_INBOUNDS={InboundConstants.CallbackData.LIST_INBOUNDS}")
    logger.info(f"===========================")

    if data == InboundConstants.CallbackData.LIST_INBOUNDS:
        logger.info("Calling list_inbounds")
        await list_inbounds(update, context)
        return INBOUND_MENU

    elif data == InboundConstants.CallbackData.LIST_FULL_INBOUNDS:
        logger.info("Calling list_full_inbounds")
        await list_full_inbounds(update, context)
        return INBOUND_MENU
        
    elif data == InboundConstants.CallbackData.LIST_INBOUNDS_STATS:
        logger.info("Calling show_inbounds_statistics")
        await show_inbounds_statistics(update, context)
        return INBOUND_MENU

    elif data == InboundConstants.CallbackData.FILTER_INBOUNDS:
        logger.info("Calling show_inbounds_filters")
        await show_inbounds_filters(update, context)
        return INBOUND_MENU
        
    elif data == "refresh_inbounds":
        logger.info("Calling show_inbounds_menu (refresh)")
        # Refresh inbounds data and show menu
        await show_inbounds_menu(update, context)
        return INBOUND_MENU
        
    elif data == InboundConstants.CallbackData.DEBUG_USERS:
        logger.info("Calling debug_user_structure")
        # Debug user structure
        await debug_user_structure(update, context)
        return INBOUND_MENU

    elif data == InboundConstants.CallbackData.BACK_TO_INBOUNDS:
        await show_inbounds_menu(update, context)
        return INBOUND_MENU

    elif data == InboundConstants.CallbackData.BACK_TO_MAIN:
        await show_main_menu(update, context)
        return MAIN_MENU
        
    elif data.startswith("view_inbound_"):
        uuid = data.split("_")[2]
        await show_inbound_details(update, context, uuid)
        return INBOUND_MENU

    elif data.startswith("select_inbound_"):
        # Handle SelectionHelper callback for inbound selection
        inbound_id = data.replace("select_inbound_", "")
        await show_inbound_details(update, context, inbound_id)
        return INBOUND_MENU

    elif data.startswith("select_full_inbound_"):
        # Handle SelectionHelper callback for full inbound selection
        inbound_id = data.replace("select_full_inbound_", "")
        await show_inbound_details(update, context, inbound_id)
        return INBOUND_MENU
        
    elif data.startswith("inbound_action_"):
        # Handle inbound actions (config, users, nodes, stats)
        action_data = data.replace("inbound_action_", "")
        action, uuid = action_data.split("_", 1)
        await handle_inbound_action(update, context, action, uuid)
        return INBOUND_MENU

    elif data.startswith("page_inbounds_"):
        # Handle pagination for inbound list
        page = int(data.split("_")[2])
        await handle_inbound_pagination(update, context, page)
        return INBOUND_MENU

    elif data.startswith("page_full_inbounds_"):
        # Handle pagination for full inbound list
        page = int(data.split("_")[3])
        await handle_full_inbound_pagination(update, context, page)
        return INBOUND_MENU

    return INBOUND_MENU

async def debug_user_structure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug function to understand user data structure"""
    await update.callback_query.edit_message_text("🔍 Анализ структуры данных пользователей...")
    
    try:
        # Call debug function
        await InboundAPI.debug_user_structure()
        
        # Get a sample user to show structure
        users_response = await UserAPI.get_all_users()
        if not users_response:
            message = "❌ Не удалось получить данные пользователей для отладки"
        else:
            users = []
            if isinstance(users_response, dict) and 'users' in users_response:
                users = users_response['users']
            elif isinstance(users_response, list):
                users = users_response
            
            if not users:
                message = "❌ Пользователи не найдены"
            else:
                user = users[0]  # Get first user
                message = f"🔍 *Структура данных пользователя*\n\n"
                message += f"👤 *Пользователь*: {escape_markdown(user.get('username', 'N/A'))}\n"
                message += f"📊 *Статус*: {user.get('status', 'N/A')}\n"
                message += f"🆔 *UUID*: `{user.get('uuid', 'N/A')}`\n\n"
                
                # Subscription info
                subscription = user.get('subscription')
                if subscription:
                    message += f"📋 *Подписка:*\n"
                    message += f"  • Статус: {subscription.get('status', 'N/A')}\n"
                    message += f"  • Config Profile UUID: `{subscription.get('configProfileUuid', 'N/A')}`\n"
                    message += f"  • Inbounds: {subscription.get('inbounds', 'N/A')}\n\n"
                else:
                    message += f"📋 *Подписка*: Нет данных\n\n"
                
                # Direct inbound references
                user_inbounds = user.get('inbounds', [])
                if user_inbounds:
                    message += f"🔌 *Прямые Inbounds*: {len(user_inbounds)} шт.\n"
                    for i, inbound in enumerate(user_inbounds[:3]):
                        message += f"  {i+1}. {inbound.get('tag', 'N/A')} ({inbound.get('uuid', 'N/A')[:8]}...)\n"
                    if len(user_inbounds) > 3:
                        message += f"  ... и еще {len(user_inbounds) - 3}\n"
                else:
                    message += f"🔌 *Прямые Inbounds*: Нет данных\n"
                
                # Active inbounds
                active_inbounds = user.get('activeInbounds', [])
                if active_inbounds:
                    message += f"✅ *Активные Inbounds*: {len(active_inbounds)} шт.\n"
                    for i, inbound in enumerate(active_inbounds[:3]):
                        message += f"  {i+1}. {inbound.get('tag', 'N/A')} ({inbound.get('uuid', 'N/A')[:8]}...)\n"
                    if len(active_inbounds) > 3:
                        message += f"  ... и еще {len(active_inbounds) - 3}\n"
                else:
                    message += f"✅ *Активные Inbounds*: Нет данных\n"
                
                message += f"\n📝 *Проверьте логи для подробной информации*"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in debug_user_structure: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка отладки: {str(e)[:200]}...",
            reply_markup=reply_markup
        )
    
    return INBOUND_MENU

async def show_inbounds_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics for all inbounds"""
    await update.callback_query.edit_message_text(InboundConstants.Messages.LOADING)
    
    try:
        inbounds = await InboundAPI.get_inbounds()
        
        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                InboundConstants.Messages.NO_INBOUNDS,
                reply_markup=reply_markup
            )
            return INBOUND_MENU
        
        # Calculate statistics
        total_inbounds = len(inbounds)
        type_stats = {}
        port_stats = {}
        total_users = 0
        total_nodes = 0
        
        for inbound in inbounds:
            # Type statistics
            inbound_type = inbound.get('type', 'Unknown')
            type_stats[inbound_type] = type_stats.get(inbound_type, 0) + 1
            
            # Port statistics
            port = inbound.get('port', 0)
            port_range = f"{port // 1000 * 1000}-{(port // 1000 + 1) * 1000 - 1}"
            port_stats[port_range] = port_stats.get(port_range, 0) + 1
            
            # User and node statistics
            if 'users' in inbound:
                total_users += inbound['users'].get('enabled', 0) + inbound['users'].get('disabled', 0)
            if 'nodes' in inbound:
                total_nodes += inbound['nodes'].get('enabled', 0) + inbound['nodes'].get('disabled', 0)
        
        # Create statistics message
        message = f"📊 *Статистика Inbounds*\n\n"
        message += f"🔢 *Общие показатели:*\n"
        message += f"  • Всего Inbounds: {total_inbounds}\n"
        message += f"  • Пользователей: {total_users}\n"
        message += f"  • Серверов: {total_nodes}\n\n"
        
        message += f"🏷️ *По типам:*\n"
        for inbound_type, count in sorted(type_stats.items()):
            percentage = (count / total_inbounds) * 100
            message += f"  • {inbound_type}: {count} ({percentage:.1f}%)\n"
        
        message += f"\n🔢 *По портам:*\n"
        for port_range, count in sorted(port_stats.items()):
            percentage = (count / total_inbounds) * 100
            message += f"  • {port_range}: {count} ({percentage:.1f}%)\n"
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("📋 Список Inbounds", callback_data=InboundConstants.CallbackData.LIST_INBOUNDS)],
            [InlineKeyboardButton("📊 Детальный просмотр", callback_data=InboundConstants.CallbackData.LIST_FULL_INBOUNDS)],
            [InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing inbound statistics: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            InboundConstants.Messages.ERROR_LOADING,
            reply_markup=reply_markup
        )

    return INBOUND_MENU

async def show_inbounds_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show filtering options for inbounds"""
    try:
        inbounds = await InboundAPI.get_inbounds()
        
        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                InboundConstants.Messages.NO_INBOUNDS,
                reply_markup=reply_markup
            )
            return INBOUND_MENU
        
        # Get unique types and port ranges
        types = sorted(list(set(inbound.get('type', 'Unknown') for inbound in inbounds)))
        port_ranges = sorted(list(set(f"{inbound.get('port', 0) // 1000 * 1000}-{(inbound.get('port', 0) // 1000 + 1) * 1000 - 1}" for inbound in inbounds)))
        
        # Create filter keyboard
        keyboard = []
        
        # Filter by type
        keyboard.append([InlineKeyboardButton("🏷️ Фильтр по типу", callback_data="filter_type")])
        for inbound_type in types[:5]:  # Limit to 5 types
            keyboard.append([InlineKeyboardButton(f"  • {inbound_type}", callback_data=f"filter_by_type_{inbound_type}")])
        
        # Filter by port range
        keyboard.append([InlineKeyboardButton("🔢 Фильтр по портам", callback_data="filter_ports")])
        for port_range in port_ranges[:5]:  # Limit to 5 port ranges
            keyboard.append([InlineKeyboardButton(f"  • {port_range}", callback_data=f"filter_by_ports_{port_range}")])
        
        # Other filters
        keyboard.append([InlineKeyboardButton("👥 С пользователями", callback_data="filter_with_users")])
        keyboard.append([InlineKeyboardButton("🖥️ С серверами", callback_data="filter_with_nodes")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"🔍 *Фильтры и поиск Inbounds*\n\n"
        message += f"Доступно фильтров:\n"
        message += f"  • По типу: {len(types)} вариантов\n"
        message += f"  • По портам: {len(port_ranges)} диапазонов\n"
        message += f"  • С пользователями/серверами\n\n"
        message += f"Выберите фильтр:"
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing inbound filters: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            InboundConstants.Messages.ERROR_LOADING,
            reply_markup=reply_markup
        )
    
    return INBOUND_MENU

async def handle_inbound_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, uuid: str):
    """Handle specific inbound actions (config, users, nodes, stats)"""
    try:
        inbounds = await InboundAPI.get_inbounds()
        inbound = next((i for i in inbounds if i['uuid'] == uuid), None)
        
        if not inbound:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Inbound не найден",
                reply_markup=reply_markup
            )
            return INBOUND_MENU
        
        if action == "config":
            await show_inbound_config(update, context, inbound)
        elif action == "users":
            await show_inbound_users(update, context, inbound)
        elif action == "nodes":
            await show_inbound_nodes(update, context, inbound)
        elif action == "stats":
            await show_inbound_stats(update, context, inbound)
        else:
            await show_inbound_details(update, context, uuid)
            
    except Exception as e:
        logger.error(f"Error handling inbound action {action}: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            InboundConstants.Messages.ERROR_LOADING,
            reply_markup=reply_markup
        )

    return INBOUND_MENU

async def show_inbound_config(update: Update, context: ContextTypes.DEFAULT_TYPE, inbound: Dict[str, Any]):
    """Show inbound configuration details"""
    message = f"⚙️ *Конфигурация Inbound*\n\n"
    message += f"🏷️ *Тег*: {escape_markdown(inbound['tag'])}\n"
    message += f"🆔 *UUID*: `{inbound['uuid']}`\n"
    message += f"🔌 *Тип*: {inbound['type']}\n"
    message += f"🔢 *Порт*: {inbound['port']}\n"
    
    if inbound.get('network'):
        message += f"🌐 *Сеть*: {inbound['network']}\n"
    
    if inbound.get('security'):
        message += f"🔒 *Безопасность*: {inbound['security']}\n"
    
    if inbound.get('settings'):
        message += f"\n⚙️ *Настройки*:\n"
        for key, value in inbound['settings'].items():
            if isinstance(value, dict):
                message += f"  • {key}:\n"
                for sub_key, sub_value in value.items():
                    message += f"    - {sub_key}: {sub_value}\n"
            else:
                message += f"  • {key}: {value}\n"
    
    keyboard = [
        [InlineKeyboardButton("👥 Пользователи", callback_data=f"inbound_action_users_{inbound['uuid']}")],
        [InlineKeyboardButton("🖥️ Серверы", callback_data=f"inbound_action_nodes_{inbound['uuid']}")],
        [InlineKeyboardButton("📊 Статистика", callback_data=f"inbound_action_stats_{inbound['uuid']}")],
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_inbound_{inbound['uuid']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_inbound_users(update: Update, context: ContextTypes.DEFAULT_TYPE, inbound: Dict[str, Any]):
    """Show online count for inbound (без списка пользователей)"""
    from datetime import datetime
    
    message = f"👥 *Пользователи Inbound*\n\n"
    message += f"🏷️ *Тег*: {escape_markdown(inbound['tag'])}\n"
    message += f"🔌 *Тип*: {inbound['type']}\n"
    message += f"🔢 *Порт*: {inbound['port']}\n\n"

    try:
        online_count = await InboundAPI.get_inbound_online_count(inbound)
        message += f"📡 *Онлайн сейчас*: {online_count}\n\n"
        
        # Получим общее количество активных пользователей
        from modules.api.users import UserAPI
        all_users_resp = await UserAPI.get_all_users()
        all_users = []
        if isinstance(all_users_resp, dict) and 'users' in all_users_resp:
            all_users = all_users_resp['users'] or []
        elif isinstance(all_users_resp, list):
            all_users = all_users_resp
        
        active_users = 0
        for user in all_users:
            if InboundAPI._is_active_status(user.get('status')):
                active_users += 1
        
        message += f"📊 *Всего активных пользователей*: {active_users}\n\n"
        # Добавим время обновления чтобы избежать ошибки "Message is not modified"
        current_time = datetime.now().strftime("%H:%M:%S")
        message += f"🕐 *Обновлено*: {current_time}\n"
    except Exception as e:
        logger.error(f"Error getting online count for inbound {inbound['uuid']}: {e}")
        message += f"❌ *Ошибка загрузки данных*\n"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data=f"inbound_action_users_{inbound['uuid']}")],
        [InlineKeyboardButton("⚙️ Конфигурация", callback_data=f"inbound_action_config_{inbound['uuid']}")],
        [InlineKeyboardButton("🖥️ Серверы", callback_data=f"inbound_action_nodes_{inbound['uuid']}")],
        [InlineKeyboardButton("📊 Статистика", callback_data=f"inbound_action_stats_{inbound['uuid']}")],
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_inbound_{inbound['uuid']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        if "Message is not modified" in str(e):
            # Если сообщение не изменилось, просто показываем уведомление
            await update.callback_query.answer("✅ Данные актуальны", show_alert=False)
        else:
            logger.error(f"Error updating message: {e}")
            await update.callback_query.answer("❌ Ошибка обновления", show_alert=True)

async def show_inbound_nodes(update: Update, context: ContextTypes.DEFAULT_TYPE, inbound: Dict[str, Any]):
    """Show nodes associated with inbound"""
    message = f"🖥️ *Серверы Inbound*\n\n"
    message += f"🏷️ *Тег*: {escape_markdown(inbound['tag'])}\n"
    message += f"🔌 *Тип*: {inbound['type']}\n"
    message += f"🔢 *Порт*: {inbound['port']}\n\n"
    
    if 'nodes' in inbound:
        nodes = inbound['nodes']
        message += f"📊 *Статистика серверов:*\n"
        message += f"  • Активных: {nodes.get('enabled', 0)}\n"
        message += f"  • Отключенных: {nodes.get('disabled', 0)}\n"
        message += f"  • Всего: {nodes.get('enabled', 0) + nodes.get('disabled', 0)}\n"
        
        if nodes.get('enabled', 0) > 0:
            message += f"\n✅ *Активные серверы:*\n"
            message += f"  • Серверы активны и обслуживают этот inbound\n"
        
        if nodes.get('disabled', 0) > 0:
            message += f"\n❌ *Отключенные серверы:*\n"
            message += f"  • {nodes.get('disabled', 0)} серверов отключены\n"
    else:
        message += f"❌ *Информация о серверах недоступна*\n"
        message += f"  • Данные не загружены или отсутствуют\n"
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Конфигурация", callback_data=f"inbound_action_config_{inbound['uuid']}")],
        [InlineKeyboardButton("👥 Пользователи", callback_data=f"inbound_action_users_{inbound['uuid']}")],
        [InlineKeyboardButton("📊 Статистика", callback_data=f"inbound_action_stats_{inbound['uuid']}")],
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_inbound_{inbound['uuid']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_inbound_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, inbound: Dict[str, Any]):
    """Show detailed statistics for specific inbound"""
    message = f"📊 *Статистика Inbound*\n\n"
    message += f"🏷️ *Тег*: {escape_markdown(inbound['tag'])}\n"
    message += f"🔌 *Тип*: {inbound['type']}\n"
    message += f"🔢 *Порт*: {inbound['port']}\n\n"
    
    # Basic statistics
    message += f"📈 *Основные показатели:*\n"
    message += f"  • Статус: {'🟢 Активен' if inbound.get('enabled', True) else '🔴 Отключен'}\n"
    message += f"  • Создан: {inbound.get('createdAt', 'Неизвестно')}\n"
    message += f"  • Обновлен: {inbound.get('updatedAt', 'Неизвестно')}\n\n"
    
    # User statistics
    if 'users' in inbound:
        users = inbound['users']
        total_users = users.get('enabled', 0) + users.get('disabled', 0)
        message += f"👥 *Пользователи:*\n"
        message += f"  • Активных: {users.get('enabled', 0)}\n"
        message += f"  • Отключенных: {users.get('disabled', 0)}\n"
        message += f"  • Всего: {total_users}\n"
        if total_users > 0:
            active_percentage = (users.get('enabled', 0) / total_users) * 100
            message += f"  • Активность: {active_percentage:.1f}%\n"
        message += f"\n"
    
    # Node statistics
    if 'nodes' in inbound:
        nodes = inbound['nodes']
        total_nodes = nodes.get('enabled', 0) + nodes.get('disabled', 0)
        message += f"🖥️ *Серверы:*\n"
        message += f"  • Активных: {nodes.get('enabled', 0)}\n"
        message += f"  • Отключенных: {nodes.get('disabled', 0)}\n"
        message += f"  • Всего: {total_nodes}\n"
        if total_nodes > 0:
            active_percentage = (nodes.get('enabled', 0) / total_nodes) * 100
            message += f"  • Активность: {active_percentage:.1f}%\n"
        message += f"\n"
    
    # Additional statistics
    message += f"🔧 *Дополнительная информация:*\n"
    message += f"  • Сеть: {inbound.get('network', 'Не указана')}\n"
    message += f"  • Безопасность: {inbound.get('security', 'Не указана')}\n"
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Конфигурация", callback_data=f"inbound_action_config_{inbound['uuid']}")],
        [InlineKeyboardButton("👥 Пользователи", callback_data=f"inbound_action_users_{inbound['uuid']}")],
        [InlineKeyboardButton("🖥️ Серверы", callback_data=f"inbound_action_nodes_{inbound['uuid']}")],
        [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_inbound_{inbound['uuid']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def list_inbounds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all inbounds with enhanced display"""
    await update.callback_query.edit_message_text(InboundConstants.Messages.LOADING)

    try:
        inbounds = await InboundAPI.get_inbounds()
        
        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                InboundConstants.Messages.NO_INBOUNDS,
                reply_markup=reply_markup
            )
            return INBOUND_MENU

        # Create enhanced keyboard with better formatting
        keyboard = []
        for inbound in inbounds:
            # Create a more descriptive button text
            status_emoji = "🟢" if inbound.get('enabled', True) else "🔴"
            button_text = f"{status_emoji} {inbound['tag']} ({inbound['type']}, :{inbound['port']})"
            callback_data = f"select_inbound_{inbound['uuid']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Create enhanced message
        message = f"🔌 *Список Inbounds* ({len(inbounds)} шт.)\n\n"
        message += f"📊 *Краткая статистика:*\n"
        
        # Count by status
        active_count = sum(1 for i in inbounds if i.get('enabled', True))
        inactive_count = len(inbounds) - active_count
        
        message += f"  • Активных: {active_count}\n"
        message += f"  • Отключенных: {inactive_count}\n\n"
        
        message += f"Выберите Inbound для просмотра подробной информации:"

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error listing inbounds: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            InboundConstants.Messages.ERROR_LOADING,
            reply_markup=reply_markup
        )

    return INBOUND_MENU

async def list_full_inbounds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all inbounds with enhanced full details display"""
    await update.callback_query.edit_message_text(InboundConstants.Messages.LOADING)

    try:
        inbounds = await InboundAPI.get_full_inbounds()

        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                InboundConstants.Messages.NO_INBOUNDS,
                reply_markup=reply_markup
            )
            return INBOUND_MENU

        # Create enhanced keyboard with detailed information
        keyboard = []
        total_users = 0
        total_nodes = 0
        active_inbounds = 0
        
        for inbound in inbounds:
            # Status indicator
            status_emoji = "🟢" if inbound.get('enabled', True) else "🔴"
            if inbound.get('enabled', True):
                active_inbounds += 1
            
            # Get real user statistics from API
            try:
                user_stats = await InboundAPI.get_inbound_users_stats(inbound['uuid'])
                user_info = f"👥 {user_stats['enabled']}/{user_stats['total']}"
                total_users += user_stats['total']
            except Exception as e:
                logger.error(f"Error getting user stats for inbound {inbound['uuid']}: {e}")
                user_info = "👥 ?/?"
            
            # Node statistics (keep existing logic for now)
            node_info = ""
            if 'nodes' in inbound:
                nodes = inbound['nodes']
                enabled_nodes = nodes.get('enabled', 0)
                disabled_nodes = nodes.get('disabled', 0)
                total_nodes += enabled_nodes + disabled_nodes
                node_info = f"🖥️ {enabled_nodes}/{enabled_nodes + disabled_nodes}"
            
            # Create detailed button text
            button_parts = [f"{status_emoji} {inbound['tag']}"]
            button_parts.append(f"{inbound['type']}:{inbound['port']}")
            if user_info:
                button_parts.append(user_info)
            if node_info:
                button_parts.append(node_info)
            
            button_text = " | ".join(button_parts)
            callback_data = f"select_full_inbound_{inbound['uuid']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Create enhanced message with comprehensive statistics
        message = f"🔌 *Детальный список Inbounds* ({len(inbounds)} шт.)\n\n"
        message += f"📊 *Общая статистика:*\n"
        message += f"  • Активных: {active_inbounds}\n"
        message += f"  • Отключенных: {len(inbounds) - active_inbounds}\n"
        message += f"  • Пользователей: {total_users}\n"
        message += f"  • Серверов: {total_nodes}\n\n"
        
        message += f"📋 *Легенда:*\n"
        message += f"  🟢 - Активный inbound\n"
        message += f"  🔴 - Отключенный inbound\n"
        message += f"  👥 - Пользователи (активные/всего)\n"
        message += f"  🖥️ - Серверы (активные/всего)\n\n"
        
        message += f"Выберите Inbound для просмотра подробной информации:"

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error listing full inbounds: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            InboundConstants.Messages.ERROR_LOADING,
            reply_markup=reply_markup
        )

    return INBOUND_MENU

async def show_inbound_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show enhanced inbound details with action buttons"""
    try:
        # Get full inbounds to find the one with matching UUID
        inbounds = await InboundAPI.get_full_inbounds()
        
        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(
                InboundConstants.Messages.NO_INBOUNDS,
                reply_markup=reply_markup
            )
            return INBOUND_MENU
        
        inbound = next((i for i in inbounds if i['uuid'] == uuid), None)
        
        if not inbound:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(
                "❌ Inbound не найден или ошибка при получении данных.",
                reply_markup=reply_markup
            )
            return INBOUND_MENU
        
        # Create enhanced message with better formatting
        message = f"🔌 *Детальная информация об Inbound*\n\n"
        message += f"🏷️ *Тег*: {escape_markdown(inbound['tag'])}\n"
        message += f"🆔 *UUID*: `{inbound['uuid']}`\n"
        message += f"🔌 *Тип*: {inbound['type']}\n"
        message += f"🔢 *Порт*: {inbound['port']}\n"
        
        if inbound.get('network'):
            message += f"🌐 *Сеть*: {inbound['network']}\n"
        
        if inbound.get('security'):
            message += f"🔒 *Безопасность*: {inbound['security']}\n"
        
        # Status information
        status_emoji = "🟢" if inbound.get('enabled', True) else "🔴"
        status_text = "Активен" if inbound.get('enabled', True) else "Отключен"
        message += f"📊 *Статус*: {status_emoji} {status_text}\n\n"
        
        # Node statistics
        if 'nodes' in inbound:
            nodes = inbound['nodes']
            total_nodes = nodes.get('enabled', 0) + nodes.get('disabled', 0)
            message += f"🖥️ *Серверы:*\n"
            message += f"  • Активных: {nodes.get('enabled', 0)}\n"
            message += f"  • Отключенных: {nodes.get('disabled', 0)}\n"
            message += f"  • Всего: {total_nodes}\n"
            if total_nodes > 0:
                active_percentage = (nodes.get('enabled', 0) / total_nodes) * 100
                message += f"  • Активность: {active_percentage:.1f}%\n"
            message += f"\n"
        
        # Additional information
        if inbound.get('createdAt'):
            message += f"📅 *Создан*: {inbound['createdAt']}\n"
        if inbound.get('updatedAt'):
            message += f"🔄 *Обновлен*: {inbound['updatedAt']}\n"
        
        # Create enhanced action buttons
        keyboard = [
            [InlineKeyboardButton("⚙️ Конфигурация", callback_data=f"inbound_action_config_{uuid}")],
            [InlineKeyboardButton("👥 Пользователи", callback_data=f"inbound_action_users_{uuid}")],
            [InlineKeyboardButton("🖥️ Серверы", callback_data=f"inbound_action_nodes_{uuid}")],
            [InlineKeyboardButton("📊 Статистика", callback_data=f"inbound_action_stats_{uuid}")],
            [InlineKeyboardButton("🔙 Назад к списку", callback_data=InboundConstants.CallbackData.LIST_FULL_INBOUNDS)]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error showing inbound details: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=InboundConstants.CallbackData.BACK_TO_INBOUNDS)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            InboundConstants.Messages.ERROR_LOADING,
            reply_markup=reply_markup
        )
    
    return INBOUND_MENU

    # v208: массовые операции с inbound недоступны, удалены вспомогательные обработчики

async def handle_inbound_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Handle pagination for inbound list"""
    try:
        inbounds = await InboundAPI.get_inbounds()
        
        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Inbounds не найдены или ошибка при получении списка.",
                reply_markup=reply_markup
            )
            return INBOUND_MENU

        # Format items for SelectionHelper
        items = []
        for inbound in inbounds:
            items.append({
                'id': inbound['uuid'],
                'name': inbound['tag'],
                'description': f"🔌 {inbound['type']} | 🔢 Порт: {inbound['port']}"
            })

        # Use SelectionHelper for pagination
        helper = SelectionHelper(
            title="🔌 Выберите Inbound",
            items=items,
            callback_prefix="select_inbound",
            back_callback="back_to_inbounds",
            items_per_page=8
        )

        keyboard = helper.get_keyboard(page=page)
        message = helper.get_message(page=page)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error handling inbound pagination: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка Inbounds.",
            reply_markup=reply_markup
        )

    return INBOUND_MENU

async def handle_full_inbound_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    """Handle pagination for full inbound list"""
    try:
        inbounds = await InboundAPI.get_full_inbounds()
        
        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Inbounds не найдены или ошибка при получении списка.",
                reply_markup=reply_markup
            )
            return INBOUND_MENU

        # Format items for SelectionHelper with detailed info
        items = []
        for inbound in inbounds:
            description = f"🔌 {inbound['type']} | 🔢 Порт: {inbound['port']}"
            
            if 'users' in inbound:
                description += f"\n👥 Пользователи: {inbound['users']['enabled']} активных, {inbound['users']['disabled']} отключенных"
            
            if 'nodes' in inbound:
                description += f"\n🖥️ Серверы: {inbound['nodes']['enabled']} активных, {inbound['nodes']['disabled']} отключенных"
            
            items.append({
                'id': inbound['uuid'],
                'name': inbound['tag'],
                'description': description
            })

        # Use SelectionHelper for pagination
        helper = SelectionHelper(
            title="🔌 Выберите Inbound (детальный просмотр)",
            items=items,
            callback_prefix="select_full_inbound",
            back_callback="back_to_inbounds",
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
        logger.error(f"Error handling full inbound pagination: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_inbounds")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка Inbounds.",
            reply_markup=reply_markup
        )

    return INBOUND_MENU


