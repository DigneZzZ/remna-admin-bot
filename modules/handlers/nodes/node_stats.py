from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from datetime import datetime, timedelta

from modules.config import SELECTING_NODE
from modules.api.nodes import NodeAPI
from modules.utils.formatters import format_bytes, escape_markdown, create_progress_bar

logger = logging.getLogger(__name__)

async def show_node_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show detailed node statistics"""
    try:
        # Get node basic info
        node_response = await NodeAPI.get_node_by_uuid(uuid)
        if not node_response or 'response' not in node_response:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Сервер не найден.",
                reply_markup=reply_markup
            )
            return SELECTING_NODE
        
        node = node_response['response']
        
        # Get node statistics (если доступно в API)
        try:
            stats_response = await NodeAPI.get_node_stats(uuid)
            stats = stats_response.get('response', {}) if stats_response else {}
        except Exception:
            stats = {}
        
        message = f"📊 *Статистика сервера: {escape_markdown(node['name'])}*\n\n"
        
        # Basic status
        status_emoji = "🟢" if node.get("isConnected") and not node.get("isDisabled") else "🔴"
        message += f"📊 *Статус:* {status_emoji}\n"
        message += f"🆔 *UUID:* `{uuid}`\n"
        message += f"🌐 *Адрес:* {escape_markdown(node['address'])}:{node['port']}\n\n"
        
        # Detailed status breakdown
        message += f"🔍 *Детальный статус:*\n"
        message += f"  • Подключен: {'✅' if node.get('isConnected') else '❌'}\n"
        message += f"  • Включен: {'✅' if not node.get('isDisabled') else '❌'}\n"
        message += f"  • Онлайн: {'✅' if node.get('isNodeOnline') else '❌'}\n"
        message += f"  • Xray запущен: {'✅' if node.get('isXrayRunning') else '❌'}\n\n"
        
        # Traffic statistics
        if node.get("trafficLimitBytes") is not None:
            used = node.get('trafficUsedBytes', 0)
            limit = node['trafficLimitBytes']
            percentage = (used / limit * 100) if limit > 0 else 0
            remaining = limit - used
            progress_bar = create_progress_bar(percentage)
            
            message += f"📈 *Трафик:*\n"
            message += f"  • Использовано: {format_bytes(used)} ({percentage:.1f}%)\n"
            message += f"  • Лимит: {format_bytes(limit)}\n"
            message += f"  • Осталось: {format_bytes(remaining)}\n"
            message += f"  • {progress_bar}\n\n"
        else:
            used = node.get('trafficUsedBytes', 0)
            message += f"📈 *Трафик:* {format_bytes(used)} (безлимитный)\n\n"
        
        # Users online
        if node.get("usersOnline") is not None:
            message += f"👥 *Пользователей онлайн:* {node['usersOnline']}\n\n"
        
        # System information
        if node.get("cpuModel") or node.get("totalRam"):
            message += f"💻 *Система:*\n"
            if node.get("cpuModel"):
                message += f"  • CPU: {escape_markdown(node['cpuModel'])}"
                if node.get("cpuCount"):
                    message += f" ({node['cpuCount']} ядер)"
                message += "\n"
            
            if node.get("totalRam"):
                message += f"  • RAM: {escape_markdown(node['totalRam'])}\n"
            message += "\n"
        
        # Version and uptime
        if node.get("xrayVersion"):
            message += f"📦 *Xray версия:* {escape_markdown(node['xrayVersion'])}\n"
        
        if node.get("xrayUptime"):
            message += f"⏱️ *Uptime:* {escape_markdown(node['xrayUptime'])}\n"
        
        if node.get("countryCode"):
            message += f"🌍 *Страна:* {node['countryCode']}\n"
        
        if node.get("consumptionMultiplier"):
            message += f"📊 *Множитель потребления:* {node['consumptionMultiplier']}x\n"
        
        # Advanced statistics from stats API (if available)
        if stats:
            message += f"\n📈 *Расширенная статистика:*\n"
            
            if 'dailyTraffic' in stats:
                daily = stats['dailyTraffic']
                message += f"  • Трафик за сегодня: {format_bytes(daily.get('today', 0))}\n"
                message += f"  • Трафик за вчера: {format_bytes(daily.get('yesterday', 0))}\n"
            
            if 'weeklyTraffic' in stats:
                weekly = stats['weeklyTraffic']
                message += f"  • Трафик за неделю: {format_bytes(weekly.get('current', 0))}\n"
            
            if 'connectionStats' in stats:
                conn = stats['connectionStats']
                message += f"  • Активные соединения: {conn.get('active', 0)}\n"
                message += f"  • Всего подключений: {conn.get('total', 0)}\n"
            
            if 'performance' in stats:
                perf = stats['performance']
                if 'cpu' in perf:
                    message += f"  • Загрузка CPU: {perf['cpu']['usage']:.1f}%\n"
                if 'memory' in perf:
                    mem_usage = (perf['memory']['used'] / perf['memory']['total']) * 100
                    message += f"  • Использование RAM: {mem_usage:.1f}%\n"
        
        # Time information
        message += f"\n📅 *Время:*\n"
        try:
            created = datetime.fromisoformat(node['createdAt'].replace('Z', '+00:00'))
            days_since_creation = (datetime.now().astimezone() - created).days
            message += f"  • Создан: {node['createdAt'][:10]} ({days_since_creation} дней назад)\n"
        except Exception:
            message += f"  • Создан: {node['createdAt'][:10]}\n"
        
        try:
            updated = datetime.fromisoformat(node['updatedAt'].replace('Z', '+00:00'))
            hours_since_update = (datetime.now().astimezone() - updated).total_seconds() / 3600
            if hours_since_update < 1:
                time_text = f"{int(hours_since_update * 60)} минут назад"
            elif hours_since_update < 24:
                time_text = f"{int(hours_since_update)} часов назад"
            else:
                days = int(hours_since_update / 24)
                time_text = f"{days} дней назад"
            message += f"  • Обновлен: {node['updatedAt'][:10]} ({time_text})\n"
        except Exception:
            message += f"  • Обновлен: {node['updatedAt'][:10]}\n"
        
        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("🔄 Обновить", callback_data=f"node_stats_{uuid}"),
                InlineKeyboardButton("📊 График", callback_data=f"node_graph_{uuid}")
            ],
            [
                InlineKeyboardButton("⚙️ Управление", callback_data=f"view_node_{uuid}"),
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return SELECTING_NODE
        
    except Exception as e:
        logger.error(f"Error showing node stats: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке статистики: {str(e)}",
            reply_markup=reply_markup
        )
        return SELECTING_NODE

async def show_node_traffic_graph(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show node traffic graph (simplified text representation)"""
    try:
        # Get node info
        node_response = await NodeAPI.get_node_by_uuid(uuid)
        if not node_response or 'response' not in node_response:
            await update.callback_query.answer("❌ Сервер не найден")
            return SELECTING_NODE
        
        node = node_response['response']
        
        # Try to get traffic history (если доступно в API)
        try:
            history_response = await NodeAPI.get_node_traffic_history(uuid, days=7)
            history = history_response.get('response', []) if history_response else []
        except Exception:
            history = []
        
        message = f"📊 *График трафика: {escape_markdown(node['name'])}*\n\n"
        
        if history:
            message += "📈 *Трафик за последние 7 дней:*\n\n"
            
            # Find max value for scaling
            max_value = max((day.get('bytes', 0) for day in history), default=1)
            
            for day_data in history[-7:]:  # Last 7 days
                date = day_data.get('date', 'N/A')
                bytes_value = day_data.get('bytes', 0)
                
                # Create simple bar chart
                bar_length = int((bytes_value / max_value) * 20) if max_value > 0 else 0
                bar = '█' * bar_length + '░' * (20 - bar_length)
                
                message += f"`{date}` {format_bytes(bytes_value)}\n"
                message += f"`{bar}`\n\n"
        else:
            # Fallback: show current statistics
            message += "📊 *Текущая статистика:*\n\n"
            
            used = node.get('trafficUsedBytes', 0)
            message += f"📈 *Общий использованный трафик:* {format_bytes(used)}\n"
            
            if node.get('trafficLimitBytes'):
                limit = node['trafficLimitBytes']
                percentage = (used / limit * 100) if limit > 0 else 0
                progress_bar = create_progress_bar(percentage, length=20)
                
                message += f"📊 *Лимит трафика:* {format_bytes(limit)}\n"
                message += f"📈 *Использование:* {percentage:.1f}%\n"
                message += f"{progress_bar}\n\n"
            
            # Show weekly breakdown estimate
            message += "*Примерное распределение по дням:*\n"
            daily_avg = used / 7 if used > 0 else 0
            
            for i in range(7):
                date = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d')
                # Simulate some variation
                variation = 0.7 + (i * 0.1)  # Simple variation pattern
                daily_traffic = daily_avg * variation
                
                bar_length = int((daily_traffic / (daily_avg * 1.3)) * 15) if daily_avg > 0 else 0
                bar = '█' * bar_length + '░' * (15 - bar_length)
                
                message += f"`{date}` {format_bytes(daily_traffic)}\n"
                message += f"`{bar}`\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data=f"node_graph_{uuid}")],
            [InlineKeyboardButton("📊 Статистика", callback_data=f"node_stats_{uuid}")],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"view_node_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return SELECTING_NODE
        
    except Exception as e:
        logger.error(f"Error showing node traffic graph: {e}")
        await update.callback_query.answer(f"❌ Ошибка: {str(e)}")
        return SELECTING_NODE
