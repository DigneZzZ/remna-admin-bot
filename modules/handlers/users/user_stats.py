from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging

from modules.config import SELECTING_USER
from modules.api.users import UserAPI
from modules.utils.formatters import escape_markdown, format_bytes

logger = logging.getLogger(__name__)

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show detailed user statistics"""
    try:
        # Get user details
        user_response = await UserAPI.get_user_by_uuid(uuid)
        if not user_response or 'response' not in user_response:
            await update.callback_query.edit_message_text("❌ Пользователь не найден.")
            return SELECTING_USER
        
        user = user_response['response']
        
        # Get user statistics (if API supports it)
        try:
            stats_response = await UserAPI.get_user_statistics(uuid)
            stats = stats_response.get('response', {}) if stats_response else {}
        except:
            stats = {}
        
        message = f"📊 *Статистика пользователя*\n\n"
        message += f"👤 Пользователь: `{escape_markdown(user['username'])}`\n"
        message += f"🆔 UUID: `{user['uuid']}`\n\n"
        
        # Basic user info
        message += f"📈 *Основная информация:*\n"
        message += f"• Статус: `{user.get('status', 'N/A')}`\n"
        
        # Traffic information
        used_traffic = user.get('usedTraffic', 0)
        traffic_limit = user.get('trafficLimitBytes', 0)
        
        message += f"• Использовано трафика: `{format_bytes(used_traffic)}`\n"
        message += f"• Лимит трафика: `{format_bytes(traffic_limit)}`\n"
        
        if traffic_limit > 0:
            usage_percent = (used_traffic / traffic_limit) * 100
            message += f"• Использование: `{usage_percent:.1f}%`\n"
        
        # Traffic strategy
        strategy = user.get('trafficLimitStrategy', 'NO_RESET')
        message += f"• Стратегия сброса: `{strategy}`\n"
        
        # Expiration info
        expire_at = user.get('expireAt')
        if expire_at:
            try:
                expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                now = datetime.now(expire_date.tzinfo)
                
                if expire_date > now:
                    days_left = (expire_date - now).days
                    message += f"• Истекает через: `{days_left} дней`\n"
                    message += f"• Дата истечения: `{expire_date.strftime('%Y-%m-%d %H:%M')}`\n"
                else:
                    message += f"• ⚠️ Подписка истекла `{expire_date.strftime('%Y-%m-%d %H:%M')}`\n"
            except:
                message += f"• Дата истечения: `{expire_at[:19]}`\n"
        
        # Device information
        hwid_limit = user.get('hwidDeviceLimit', 0)
        message += f"• Лимит устройств: `{hwid_limit}`\n"
        
        # Additional stats from API (if available)
        if stats:
            message += f"\n📊 *Расширенная статистика:*\n"
            
            if 'connectionsCount' in stats:
                message += f"• Подключений: `{stats['connectionsCount']}`\n"
            
            if 'lastConnection' in stats:
                last_conn = stats['lastConnection'][:19] if stats['lastConnection'] else 'Никогда'
                message += f"• Последнее подключение: `{last_conn}`\n"
            
            if 'totalSessions' in stats:
                message += f"• Всего сессий: `{stats['totalSessions']}`\n"
            
            if 'averageSessionDuration' in stats:
                avg_duration = stats['averageSessionDuration']
                hours = avg_duration // 3600
                minutes = (avg_duration % 3600) // 60
                message += f"• Средняя продолжительность сессии: `{hours}ч {minutes}м`\n"
        
        # Account information
        created_at = user.get('createdAt')
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                account_age = (datetime.now(created_date.tzinfo) - created_date).days
                message += f"\n🕐 *Информация об аккаунте:*\n"
                message += f"• Создан: `{created_date.strftime('%Y-%m-%d %H:%M')}`\n"
                message += f"• Возраст аккаунта: `{account_age} дней`\n"
            except:
                message += f"\n🕐 Создан: `{created_at[:19]}`\n"
        
        # Subscription info
        sub_uuid = user.get('subscriptionUuid')
        if sub_uuid:
            message += f"\n🔗 *Подписка:*\n"
            message += f"• UUID подписки: `{sub_uuid}`\n"
            sub_url = user.get('subscriptionUrl')
            if sub_url:
                # Display full URL in code block to prevent underscore escaping
                message += f"• URL:\n```\n{sub_url}\n```\n"
        
        # Contact information
        contact_info = []
        if user.get('telegramId'):
            contact_info.append(f"• Telegram ID: `{user['telegramId']}`")
        if user.get('email'):
            contact_info.append(f"• Email: `{user['email']}`")
        if user.get('tag'):
            contact_info.append(f"• Тег: `{user['tag']}`")
        
        if contact_info:
            message += f"\n📞 *Контактная информация:*\n"
            message += "\n".join(contact_info) + "\n"
        
        # Description
        description = user.get('description')
        if description:
            display_desc = description[:100] + "..." if len(description) > 100 else description
            message += f"\n📝 *Описание:*\n`{escape_markdown(display_desc)}`\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить статистику", callback_data=f"stats_{uuid}")],
            [InlineKeyboardButton("💻 HWID устройства", callback_data=f"hwid_{uuid}")],
            [InlineKeyboardButton("📊 Детальный анализ", callback_data=f"detailed_stats_{uuid}")],
            [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error showing user stats for {uuid}: {e}")
        
        keyboard = [[InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке статистики: {str(e)}",
            reply_markup=reply_markup
        )
        
        return SELECTING_USER

async def show_detailed_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show detailed analytics for user"""
    try:
        user_response = await UserAPI.get_user_by_uuid(uuid)
        if not user_response or 'response' not in user_response:
            await update.callback_query.edit_message_text("❌ Пользователь не найден.")
            return SELECTING_USER
        
        user = user_response['response']
        
        message = f"📈 *Детальный анализ пользователя*\n\n"
        message += f"👤 `{escape_markdown(user['username'])}`\n\n"
        
        # Traffic analysis
        used_traffic = user.get('usedTraffic', 0)
        traffic_limit = user.get('trafficLimitBytes', 0)
        
        message += f"📊 *Анализ трафика:*\n"
        
        if traffic_limit > 0:
            usage_percent = (used_traffic / traffic_limit) * 100
            remaining_traffic = traffic_limit - used_traffic
            
            # Traffic status indicator
            if usage_percent < 50:
                status_emoji = "🟢"
                status_text = "Низкое использование"
            elif usage_percent < 80:
                status_emoji = "🟡"
                status_text = "Умеренное использование"
            elif usage_percent < 95:
                status_emoji = "🟠"
                status_text = "Высокое использование"
            else:
                status_emoji = "🔴"
                status_text = "Критическое использование"
            
            message += f"• Статус: {status_emoji} {status_text}\n"
            message += f"• Использовано: `{format_bytes(used_traffic)}` ({usage_percent:.1f}%)\n"
            message += f"• Осталось: `{format_bytes(remaining_traffic)}`\n"
            
            # Estimate days until limit
            if usage_percent > 0:
                try:
                    created_at = user.get('createdAt')
                    if created_at:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        account_age_days = (datetime.now(created_date.tzinfo) - created_date).days
                        
                        if account_age_days > 0:
                            daily_usage = used_traffic / account_age_days
                            if daily_usage > 0:
                                days_until_limit = remaining_traffic / daily_usage
                                message += f"• Примерно до лимита: `{days_until_limit:.0f} дней`\n"
                except:
                    pass
        else:
            message += f"• Безлимитный трафик\n"
            message += f"• Использовано: `{format_bytes(used_traffic)}`\n"
        
        # Time analysis
        message += f"\n⏰ *Временной анализ:*\n"
        
        expire_at = user.get('expireAt')
        created_at = user.get('createdAt')
        
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                account_age = (datetime.now(created_date.tzinfo) - created_date).days
                message += f"• Возраст аккаунта: `{account_age} дней`\n"
                
                if account_age > 0 and used_traffic > 0:
                    avg_daily_traffic = used_traffic / account_age
                    message += f"• Средний трафик в день: `{format_bytes(avg_daily_traffic)}`\n"
            except:
                pass
        
        if expire_at:
            try:
                expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                now = datetime.now(expire_date.tzinfo)
                
                if expire_date > now:
                    days_left = (expire_date - now).days
                    hours_left = ((expire_date - now).seconds // 3600)
                    
                    if days_left > 0:
                        message += f"• До истечения: `{days_left} дней {hours_left} часов`\n"
                    else:
                        message += f"• До истечения: `{hours_left} часов`\n"
                        
                    # Calculate subscription progress
                    if created_at:
                        total_subscription_days = (expire_date - created_date).days
                        used_subscription_days = (now - created_date).days
                        if total_subscription_days > 0:
                            subscription_progress = (used_subscription_days / total_subscription_days) * 100
                            message += f"• Прогресс подписки: `{subscription_progress:.1f}%`\n"
                else:
                    days_expired = (now - expire_date).days
                    message += f"• ⚠️ Истекла `{days_expired} дней` назад\n"
            except:
                pass
        
        # Status analysis
        message += f"\n🔍 *Анализ статуса:*\n"
        status = user.get('status', 'UNKNOWN')
        
        status_info = {
            'ACTIVE': '🟢 Активен - пользователь может использовать сервис',
            'DISABLED': '🔴 Отключен - доступ заблокирован администратором',
            'EXPIRED': '🟡 Истек - закончился срок подписки',
            'LIMITED': '🟠 Ограничен - исчерпан лимит трафика'
        }
        
        message += f"• {status_info.get(status, f'❓ {status} - неизвестный статус')}\n"
        
        # Device analysis
        hwid_limit = user.get('hwidDeviceLimit', 0)
        message += f"\n📱 *Анализ устройств:*\n"
        
        if hwid_limit > 0:
            message += f"• Лимит устройств: `{hwid_limit}`\n"
            
            # Try to get device information
            try:
                devices_response = await UserAPI.get_user_hwid_devices(uuid)
                if devices_response and 'response' in devices_response:
                    devices = devices_response['response']
                    active_devices = len(devices)
                    message += f"• Активных устройств: `{active_devices}/{hwid_limit}`\n"
                    
                    if active_devices >= hwid_limit:
                        message += f"• ⚠️ Достигнут лимит устройств\n"
                    elif active_devices > 0:
                        remaining_slots = hwid_limit - active_devices
                        message += f"• Свободных слотов: `{remaining_slots}`\n"
            except:
                message += f"• Информация об устройствах недоступна\n"
        else:
            message += f"• Без ограничений по устройствам\n"
        
        # Recommendations
        message += f"\n💡 *Рекомендации:*\n"
        
        recommendations = []
        
        # Traffic recommendations
        if traffic_limit > 0:
            if usage_percent > 90:
                recommendations.append("🔴 Критически мало трафика - рассмотрите увеличение лимита")
            elif usage_percent > 75:
                recommendations.append("🟡 Трафик на исходе - следите за использованием")
        
        # Expiration recommendations
        if expire_at:
            try:
                expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                now = datetime.now(expire_date.tzinfo)
                days_left = (expire_date - now).days
                
                if days_left < 0:
                    recommendations.append("🔴 Подписка истекла - требуется продление")
                elif days_left < 7:
                    recommendations.append("🟡 Подписка истекает скоро - подготовьте продление")
                elif days_left < 30:
                    recommendations.append("🟠 До истечения подписки меньше месяца")
            except:
                pass
        
        # Device recommendations
        if hwid_limit > 0:
            try:
                devices_response = await UserAPI.get_user_hwid_devices(uuid)
                if devices_response and 'response' in devices_response:
                    devices = devices_response['response']
                    if len(devices) >= hwid_limit:
                        recommendations.append("🟡 Достигнут лимит устройств - новые подключения невозможны")
            except:
                pass
        
        # Status recommendations
        if status != 'ACTIVE':
            if status == 'DISABLED':
                recommendations.append("🔴 Пользователь отключен - проверьте причину блокировки")
            elif status == 'EXPIRED':
                recommendations.append("🟡 Требуется продление подписки")
            elif status == 'LIMITED':
                recommendations.append("🟠 Требуется сброс трафика или увеличение лимита")
        
        if not recommendations:
            recommendations.append("✅ Все показатели в норме")
        
        for i, rec in enumerate(recommendations, 1):
            message += f"{i}. {rec}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить анализ", callback_data=f"detailed_stats_{uuid}")],
            [InlineKeyboardButton("📊 Базовая статистика", callback_data=f"stats_{uuid}")],
            [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error showing detailed user stats for {uuid}: {e}")
        
        keyboard = [[InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке детального анализа: {str(e)}",
            reply_markup=reply_markup
        )
        
        return SELECTING_USER