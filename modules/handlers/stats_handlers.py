import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from modules.config import MAIN_MENU, STATS_MENU
from modules.api.system import SystemAPI
from modules.api.nodes import NodeAPI
from modules.api.users import UserAPI
from modules.utils.formatters import format_system_stats, format_bandwidth_stats, format_bytes
from modules.handlers.start_handler import show_main_menu

logger = logging.getLogger(__name__)

async def show_stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics menu"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Общая статистика", callback_data="system_stats"),
            InlineKeyboardButton("📈 Статистика трафика", callback_data="bandwidth_stats")
        ],
        [
            InlineKeyboardButton("🖥️ Статистика нод", callback_data="nodes_stats"),
            InlineKeyboardButton("👥 Статистика пользователей", callback_data="users_stats")
        ],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "📊 *Статистика системы*\n\n"
    message += "Выберите тип статистики:"

    # Безопасная отправка/редактирование сообщения
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.effective_message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error showing stats menu: {e}")
    
    return STATS_MENU

async def handle_stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle statistics menu selection"""
    if not update.callback_query:
        return STATS_MENU
        
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        if data == "system_stats":
            return await show_system_stats(update, context)
        elif data == "bandwidth_stats":
            return await show_bandwidth_stats(update, context)
        elif data == "nodes_stats":
            return await show_nodes_stats(update, context)
        elif data == "users_stats":
            return await show_users_stats(update, context)
        elif data == "back_to_stats":
            return await show_stats_menu(update, context)
        elif data == "back_to_main":
            return await show_main_menu(update, context)
    except Exception as e:
        logger.error(f"Error in handle_stats_menu: {e}")
        
    return STATS_MENU

async def show_system_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system statistics"""
    await update.callback_query.edit_message_text("📊 Загрузка системной статистики...")

    try:
        # Получаем системную статистику
        stats_response = await SystemAPI.get_system_stats()
        
        if not stats_response or 'response' not in stats_response:
            raise Exception("Не удалось получить системную статистику")
        
        stats = stats_response['response']
        
        # Форматируем статистику
        message = "📊 *Системная статистика*\n\n"
        
        # Информация о системе
        if 'system' in stats:
            sys_info = stats['system']
            message += f"🖥️ *Система:*\n"
            message += f"• OS: `{sys_info.get('os', 'N/A')}`\n"
            message += f"• Arch: `{sys_info.get('arch', 'N/A')}`\n"
            message += f"• Version: `{sys_info.get('version', 'N/A')}`\n\n"
        
        # Использование ресурсов
        if 'memory' in stats:
            mem = stats['memory']
            total_gb = mem.get('total', 0) / (1024**3)
            used_gb = mem.get('used', 0) / (1024**3)
            free_gb = mem.get('free', 0) / (1024**3)
            
            message += f"💾 *Память:*\n"
            message += f"• Всего: `{total_gb:.1f} GB`\n"
            message += f"• Использовано: `{used_gb:.1f} GB`\n"
            message += f"• Свободно: `{free_gb:.1f} GB`\n\n"
        
        if 'cpu' in stats:
            cpu = stats['cpu']
            message += f"⚡ *CPU:*\n"
            message += f"• Использование: `{cpu.get('usage', 0):.1f}%`\n"
            message += f"• Cores: `{cpu.get('cores', 'N/A')}`\n\n"
        
        # Статистика трафика
        if 'traffic' in stats:
            traffic = stats['traffic']
            message += f"📈 *Трафик:*\n"
            message += f"• Входящий: `{format_bytes(traffic.get('inbound', 0))}`\n"
            message += f"• Исходящий: `{format_bytes(traffic.get('outbound', 0))}`\n"
            message += f"• Всего: `{format_bytes(traffic.get('total', 0))}`\n\n"
        
        # Uptime
        if 'uptime' in stats:
            uptime_seconds = stats['uptime']
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            minutes = (uptime_seconds % 3600) // 60
            message += f"⏱️ *Uptime:* `{days}д {hours}ч {minutes}м`\n"
            
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        message = f"❌ Ошибка получения системной статистики:\n`{str(e)}`"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="system_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return STATS_MENU

async def show_bandwidth_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bandwidth statistics"""
    await update.callback_query.edit_message_text("📈 Загрузка статистики трафика...")

    try:
        # Получаем статистику трафика
        bandwidth_response = await SystemAPI.get_bandwidth_stats()
        
        if not bandwidth_response or 'response' not in bandwidth_response:
            raise Exception("Не удалось получить статистику трафика")
        
        stats = bandwidth_response['response']
        
        message = "📈 *Статистика трафика*\n\n"
        
        # Общая статистика
        total_in = stats.get('totalInbound', 0)
        total_out = stats.get('totalOutbound', 0)
        total_traffic = total_in + total_out
        
        message += f"📊 *Общий трафик:*\n"
        message += f"• Входящий: `{format_bytes(total_in)}`\n"
        message += f"• Исходящий: `{format_bytes(total_out)}`\n"
        message += f"• Всего: `{format_bytes(total_traffic)}`\n\n"
        
        # Статистика за период
        if 'daily' in stats:
            daily = stats['daily']
            message += f"📅 *За сегодня:*\n"
            message += f"• Входящий: `{format_bytes(daily.get('inbound', 0))}`\n"
            message += f"• Исходящий: `{format_bytes(daily.get('outbound', 0))}`\n\n"
        
        if 'monthly' in stats:
            monthly = stats['monthly']
            message += f"📆 *За месяц:*\n"
            message += f"• Входящий: `{format_bytes(monthly.get('inbound', 0))}`\n"
            message += f"• Исходящий: `{format_bytes(monthly.get('outbound', 0))}`\n\n"
        
        # Топ пользователей по трафику (если доступно)
        if 'topUsers' in stats:
            top_users = stats['topUsers'][:5]  # Топ 5
            if top_users:
                message += f"🏆 *Топ пользователей:*\n"
                for i, user in enumerate(top_users, 1):
                    username = user.get('username', 'N/A')[:15]
                    traffic = format_bytes(user.get('totalTraffic', 0))
                    message += f"{i}. `{username}` - `{traffic}`\n"
                    
    except Exception as e:
        logger.error(f"Error getting bandwidth stats: {e}")
        message = f"❌ Ошибка получения статистики трафика:\n`{str(e)}`"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="bandwidth_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return STATS_MENU

async def show_nodes_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show nodes statistics"""
    await update.callback_query.edit_message_text("🖥️ Загрузка статистики нод...")

    try:
        # Получаем все ноды
        nodes_response = await NodeAPI.get_all_nodes()
        
        if not nodes_response or 'response' not in nodes_response:
            raise Exception("Не удалось получить список нод")
        
        nodes = nodes_response['response']
        
        if not nodes:
            message = "ℹ️ Ноды не найдены."
        else:
            message = f"🖥️ *Статистика нод* ({len(nodes)}):\n\n"
            
            # Подсчет статусов
            online_count = sum(1 for node in nodes if not node.get('isDisabled', True))
            offline_count = len(nodes) - online_count
            
            message += f"📊 *Общая информация:*\n"
            message += f"• Всего нод: `{len(nodes)}`\n"
            message += f"• Онлайн: `{online_count}` 🟢\n"
            message += f"• Офлайн: `{offline_count}` 🔴\n\n"
            
            # Детали нод
            message += "📋 *Детали нод:*\n"
            for node in nodes[:10]:  # Показываем максимум 10 нод
                name = node.get('name', 'Без названия')[:20]
                status = '🟢' if not node.get('isDisabled', True) else '🔴'
                address = node.get('address', 'N/A')
                port = node.get('port', 'N/A')
                
                message += f"• {status} `{name}`\n"
                message += f"  📍 `{address}:{port}`\n"
                
                # Добавляем статистику трафика если есть
                if 'traffic' in node:
                    traffic = node['traffic']
                    total = traffic.get('total', 0)
                    if total > 0:
                        message += f"  📈 `{format_bytes(total)}`\n"
                message += "\n"
            
            if len(nodes) > 10:
                message += f"... и еще {len(nodes) - 10} нод(ы)\n"
                
    except Exception as e:
        logger.error(f"Error getting nodes stats: {e}")
        message = f"❌ Ошибка получения статистики нод:\n`{str(e)}`"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="nodes_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return STATS_MENU

async def show_users_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show users statistics"""
    await update.callback_query.edit_message_text("👥 Загрузка статистики пользователей...")

    try:
        # Получаем всех пользователей
        users_response = await UserAPI.get_all_users()
        
        if not users_response or 'response' not in users_response:
            raise Exception("Не удалось получить список пользователей")
        
        users = users_response['response']
        
        if not users:
            message = "ℹ️ Пользователи не найдены."
        else:
            message = f"👥 *Статистика пользователей* ({len(users)}):\n\n"
            
            # Подсчет по статусам
            stats = {
                'ACTIVE': 0,
                'EXPIRED': 0,
                'LIMITED': 0,
                'DISABLED': 0,
                'total_traffic': 0
            }
            
            for user in users:
                status = user.get('status', 'UNKNOWN')
                if status in stats:
                    stats[status] += 1
                
                # Суммируем трафик
                used_traffic = user.get('usedTraffic', 0)
                stats['total_traffic'] += used_traffic
            
            message += f"📊 *По статусам:*\n"
            message += f"• Активные: `{stats['ACTIVE']}` 🟢\n"
            message += f"• Истекшие: `{stats['EXPIRED']}` 🟡\n"
            message += f"• Лимит исчерпан: `{stats['LIMITED']}` 🟠\n"
            message += f"• Отключенные: `{stats['DISABLED']}` 🔴\n\n"
            
            message += f"📈 *Общий трафик:*\n"
            message += f"• Использовано: `{format_bytes(stats['total_traffic'])}`\n\n"
            
            # Топ пользователей по трафику
            top_users = sorted(users, key=lambda x: x.get('usedTraffic', 0), reverse=True)[:5]
            if top_users and top_users[0].get('usedTraffic', 0) > 0:
                message += f"🏆 *Топ по трафику:*\n"
                for i, user in enumerate(top_users, 1):
                    username = user.get('username', 'N/A')[:15]
                    traffic = format_bytes(user.get('usedTraffic', 0))
                    status_emoji = {
                        'ACTIVE': '🟢',
                        'EXPIRED': '🟡',
                        'LIMITED': '🟠',
                        'DISABLED': '🔴'
                    }.get(user.get('status'), '⚪')
                    
                    message += f"{i}. {status_emoji} `{username}` - `{traffic}`\n"
                    
    except Exception as e:
        logger.error(f"Error getting users stats: {e}")
        message = f"❌ Ошибка получения статистики пользователей:\n`{str(e)}`"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="users_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return STATS_MENU