from datetime import datetime

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def safe_edit_message(query, text, reply_markup=None, parse_mode=None):
    """Safely edit message text with error handling for 'Message is not modified'"""
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if "not modified" in error_msg or "message is not modified" in error_msg:
            # Сообщение уже имеет такой же текст, просто отвечаем на callback
            logger.debug("Message content unchanged, skipping update")
            try:
                await query.answer()
            except Exception:
                pass  # Ignore if callback already answered
            return True
        else:
            # Другая ошибка, логируем ее
            logger.error(f"Error editing message: {e}")
            try:
                await query.answer("❌ Ошибка при обновлении сообщения")
            except Exception:
                pass
            return False

def format_bytes(bytes_value):
    """Format bytes to human-readable format"""
    if not bytes_value:
        return "0 B"  # Handle None or empty values
    
    # Если bytes_value строка, попробуем преобразовать в число
    if isinstance(bytes_value, str):
        try:
            bytes_value = float(bytes_value)
        except (ValueError, TypeError):
            return bytes_value  # Если не удалось преобразовать, возвращаем как есть
    
    if bytes_value == 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def create_progress_bar(percentage, length=20):
    """Create a visual progress bar"""
    if percentage < 0:
        percentage = 0
    elif percentage > 100:
        percentage = 100
    
    filled_length = int((percentage / 100) * length)
    bar = "█" * filled_length + "░" * (length - filled_length)
    return bar

def escape_markdown(text):
    """Escape Markdown special characters for Telegram (simplified for text, not URLs)"""
    if text is None:
        return ""
    
    text = str(text)
    
    # Упрощенное экранирование только основных символов для обычного текста
    escape_chars = [
        ('\\', '\\\\'),  # Backslash должен быть первым
        ('_', '\\_'),
        ('*', '\\*'),
        ('[', '\\['),
        (']', '\\]'),
        ('`', '\\`')
    ]
    
    for char, escaped in escape_chars:
        text = text.replace(char, escaped)
    
    return text

def format_user_details(user):
    """Format user details for display with enhanced error handling"""
    try:
        # Форматирование даты истечения
        expire_date = datetime.fromisoformat(user['expireAt'].replace('Z', '+00:00'))
        days_left = (expire_date - datetime.now().astimezone()).days
        expire_status = "🟢" if days_left > 7 else "🟡" if days_left > 0 else "🔴"
        expire_text = f"{user['expireAt'][:10]} ({days_left} дней)"
    except Exception as e:
        expire_status = "📅"
        expire_text = user['expireAt'][:10] if 'expireAt' in user and user['expireAt'] else "Не указано"
    
    # Форматирование статуса
    status_emoji = "✅" if user["status"] == "ACTIVE" else "❌"
    
    try:
        message = f"👤 *Пользователь:* {escape_markdown(user.get('username',''))}\n"
        message += f"🆔 *UUID:* `{user.get('uuid','')}`\n"
        if user.get('shortUuid'):
            message += f"🔑 *Короткий UUID:* `{user.get('shortUuid')}`\n"
        if user.get('subscriptionUuid'):
            message += f"📝 *UUID подписки:* `{user.get('subscriptionUuid')}`\n"
        message += "\n"
        
        # Безопасно форматируем URL подписки
        subscription_url = user.get('subscriptionUrl', '')
        if subscription_url:
            # Используем блок кода Markdown для безопасного отображения URL
            safe_url = escape_markdown(subscription_url)
            message += f"🔗 *URL подписки:*\n`{safe_url}`\n\n"
        else:
            message += f"🔗 *URL подписки:* Не указан\n\n"
        
        message += f"📊 *Статус:* {status_emoji} {user['status']}\n"
        message += f"📈 *Трафик:* {format_bytes(user['usedTrafficBytes'])}/{format_bytes(user['trafficLimitBytes'])}\n"
        message += f"🔄 *Стратегия сброса:* {user['trafficLimitStrategy']}\n"
        message += f"{expire_status} *Истекает:* {expire_text}\n\n"
        
        if user.get('description'):
            message += f"📝 *Описание:* {escape_markdown(str(user['description']))}\n"
        
        if user.get('tag'):
            message += f"🏷️ *Тег:* {escape_markdown(str(user['tag']))}\n"
        
        if user.get('telegramId'):
            message += f"📱 *Telegram ID:* {user['telegramId']}\n"
        
        if user.get('email'):
            message += f"📧 *Email:* {escape_markdown(str(user['email']))}\n"
        
        if user.get('hwidDeviceLimit'):
            message += f"📱 *Лимит устройств:* {user['hwidDeviceLimit']}\n"
        
        if user.get('createdAt'):
            message += f"\n⏱️ *Создан:* {user['createdAt'][:10]}\n"
        if user.get('updatedAt'):
            message += f"🔄 *Обновлен:* {user['updatedAt'][:10]}\n"
        
        return message
    except Exception as e:
        # Fallback форматирование без Markdown
        logger.warning(f"Error in format_user_details: {e}")
        
        message = f"👤 Пользователь: {user.get('username','')}\n"
        message += f"🆔 UUID: {user.get('uuid','')}\n"
        if user.get('shortUuid'):
            message += f"🔑 Короткий UUID: {user.get('shortUuid')}\n"
        if user.get('subscriptionUuid'):
            message += f"📝 UUID подписки: {user.get('subscriptionUuid')}\n\n"
        
        # Добавляем URL подписки в fallback без форматирования
        subscription_url = user.get('subscriptionUrl', '')
        if subscription_url:
            message += f"🔗 URL подписки:\n{subscription_url}\n\n"
        else:
            message += f"🔗 URL подписки: Не указан\n\n"
        
        message += f"📊 Статус: {status_emoji} {user['status']}\n"
        message += f"📈 Трафик: {format_bytes(user['usedTrafficBytes'])}/{format_bytes(user['trafficLimitBytes'])}\n"
        message += f"🔄 Стратегия сброса: {user['trafficLimitStrategy']}\n"
        message += f"{expire_status} Истекает: {expire_text}\n\n"
        
        if user.get('description'):
            message += f"📝 Описание: {user['description']}\n"
        
        if user.get('tag'):
            message += f"🏷️ Тег: {user['tag']}\n"
        
        if user.get('telegramId'):
            message += f"📱 Telegram ID: {user['telegramId']}\n"
        
        if user.get('email'):
            message += f"📧 Email: {user['email']}\n"
        
        if user.get('hwidDeviceLimit'):
            message += f"📱 Лимит устройств: {user['hwidDeviceLimit']}\n"
        
        if user.get('createdAt'):
            message += f"\n⏱️ Создан: {user['createdAt'][:10]}\n"
        if user.get('updatedAt'):
            message += f"🔄 Обновлен: {user['updatedAt'][:10]}\n"
        
        return message

def format_user_details_safe(user):
    """Format user details for display without Markdown (safe fallback)"""
    try:
        # Форматирование даты истечения
        expire_date = datetime.fromisoformat(user['expireAt'].replace('Z', '+00:00'))
        days_left = (expire_date - datetime.now().astimezone()).days
        expire_status = "🟢" if days_left > 7 else "🟡" if days_left > 0 else "🔴"
        expire_text = f"{user['expireAt'][:10]} ({days_left} дней)"
    except Exception as e:
        expire_status = "📅"
        expire_text = user['expireAt'][:10] if 'expireAt' in user and user['expireAt'] else "Не указано"
    
    # Форматирование статуса
    status_emoji = "✅" if user["status"] == "ACTIVE" else "❌"
    
    message = f"👤 Пользователь: {user['username']}\n"
    message += f"🆔 UUID: {user.get('uuid','')}\n"
    if user.get('shortUuid'):
        message += f"🔑 Короткий UUID: {user.get('shortUuid')}\n"
    if user.get('subscriptionUuid'):
        message += f"📝 UUID подписки: {user.get('subscriptionUuid')}\n\n"
    
    # URL подписки без какого-либо форматирования (без <pre> и без блоков кода)
    subscription_url = user.get('subscriptionUrl', '')
    if subscription_url:
        message += f"🔗 URL подписки:\n{subscription_url}\n\n"
    else:
        message += f"🔗 URL подписки: Не указан\n\n"
    
    message += f"📊 Статус: {status_emoji} {user['status']}\n"
    message += f"📈 Трафик: {format_bytes(user['usedTrafficBytes'])}/{format_bytes(user['trafficLimitBytes'])}\n"
    message += f"🔄 Стратегия сброса: {user['trafficLimitStrategy']}\n"
    message += f"{expire_status} Истекает: {expire_text}\n\n"
    
    if user.get('description'):
        message += f"📝 Описание: {user['description']}\n"
    
    if user.get('tag'):
        message += f"🏷️ Тег: {user['tag']}\n"
    
    if user.get('telegramId'):
        message += f"📱 Telegram ID: {user['telegramId']}\n"
    
    if user.get('email'):
        message += f"📧 Email: {user['email']}\n"
    
    if user.get('hwidDeviceLimit'):
        message += f"📱 Лимит устройств: {user['hwidDeviceLimit']}\n"
    
    if user.get('createdAt'):
        message += f"\n⏱️ Создан: {user['createdAt'][:10]}\n"
    if user.get('updatedAt'):
        message += f"🔄 Обновлен: {user['updatedAt'][:10]}\n"
    
    return message

def format_node_details(node):
    """Format node details for display with enhanced system information"""
    status_emoji = "🟢" if node["isConnected"] and not node["isDisabled"] else "🔴"

    message = f"*🖥️ Информация о сервере*\n\n"
    message += f"{status_emoji} *Имя*: {escape_markdown(node['name'])}\n"
    message += f"🆔 *UUID*: `{node['uuid']}`\n"
    message += f"🌐 *Адрес*: {escape_markdown(node['address'])}:{node['port']}\n\n"

    # Enhanced Status Information
    message += f"📊 *Статус сервера*:\n"
    message += f"  • Подключен: {'✅' if node['isConnected'] else '❌'}\n"
    message += f"  • Отключен: {'✅' if node['isDisabled'] else '❌'}\n"
    message += f"  • Онлайн: {'✅' if node['isNodeOnline'] else '❌'}\n"
    message += f"  • Xray запущен: {'✅' if node['isXrayRunning'] else '❌'}\n"
    message += f"  • Отслеживание трафика: {'✅' if node.get('isTrafficTrackingActive', False) else '❌'}\n\n"

    # Version Information
    if node.get("xrayVersion"):
        message += f"📦 *Версии*:\n"
        message += f"  • Xray: {escape_markdown(node['xrayVersion'])}\n"
        if node.get("nodeVersion"):
            message += f"  • Node: {escape_markdown(node['nodeVersion'])}\n"
        message += "\n"

    # Enhanced Uptime Information
    if node.get("xrayUptime"):
        uptime_seconds = int(node['xrayUptime'])
        uptime_days = uptime_seconds // (24 * 3600)
        uptime_hours = (uptime_seconds % (24 * 3600)) // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        
        message += f"⏱️ *Время работы Xray*:\n"
        message += f"  • {uptime_days}д {uptime_hours}ч {uptime_minutes}м\n"
        message += f"  • Всего секунд: {uptime_seconds:,}\n\n"
    
    # Location and Configuration
    message += f"🌍 *Расположение*: {node['countryCode']}\n"
    message += f"📊 *Множитель потребления*: {node['consumptionMultiplier']}x\n"
    if node.get("trafficResetDay"):
        message += f"🔄 *День сброса трафика*: {node['trafficResetDay']}\n"
    message += "\n"

    # Traffic Information with Progress Bar
    if node.get("trafficLimitBytes") is not None:
        used_bytes = node.get('trafficUsedBytes', 0)
        limit_bytes = node['trafficLimitBytes']
        traffic_percent = (used_bytes / limit_bytes) * 100 if limit_bytes > 0 else 0
        
        message += f"📈 *Использование трафика*:\n"
        message += f"  • Использовано: {format_bytes(used_bytes)}\n"
        message += f"  • Лимит: {format_bytes(limit_bytes)}\n"
        message += f"  • Осталось: {format_bytes(limit_bytes - used_bytes)}\n"
        message += f"  • Процент: {traffic_percent:.1f}%\n"
        
        # Traffic usage bar
        traffic_bar = create_progress_bar(traffic_percent, 15)
        message += f"  • Прогресс: `{traffic_bar}` {traffic_percent:.1f}%\n\n"

    # Users Information
    if node.get("usersOnline") is not None:
        users_online = node['usersOnline']
        message += f"👥 *Пользователи*:\n"
        message += f"  • Сейчас онлайн: {users_online}\n"
        if node.get("notifyPercent"):
            message += f"  • Уведомления при: {node['notifyPercent']}% использования\n"
        message += "\n"

    # Enhanced System Information
    if node.get("cpuCount") and node.get("cpuModel"):
        message += f"💻 *Системные ресурсы*:\n"
        message += f"  • CPU: {escape_markdown(node['cpuModel'])} ({node['cpuCount']} ядер)\n"
        if node.get("totalRam"):
            message += f"  • RAM: {escape_markdown(node['totalRam'])}\n"
        message += "\n"

    # Connection Information
    if node.get("lastStatusChange"):
        message += f"🔗 *Последние изменения*:\n"
        message += f"  • Статус изменен: {node['lastStatusChange'][:19]}\n"
        if node.get("lastStatusMessage"):
            message += f"  • Сообщение: {escape_markdown(node['lastStatusMessage'])}\n"
        message += "\n"

    # Health Status
    message += f"🏥 *Состояние сервера*:\n"
    
    # Overall health based on multiple factors
    health_score = 0
    if node.get("isConnected", False):
        health_score += 1
    if node.get("isNodeOnline", False):
        health_score += 1
    if node.get("isXrayRunning", False):
        health_score += 1
    if not node.get("isDisabled", True):
        health_score += 1
    
    if health_score >= 3:
        health_status = "🟢 Отличное"
    elif health_score >= 2:
        health_status = "🟡 Хорошее"
    else:
        health_status = "🔴 Проблемы"
    
    message += f"  • Общее состояние: {health_status}\n"
    
    # Traffic health
    if node.get("trafficLimitBytes") and node.get("trafficUsedBytes"):
        traffic_percent = (node['trafficUsedBytes'] / node['trafficLimitBytes']) * 100
        if traffic_percent > 90:
            traffic_status = "🔴 Критическое"
        elif traffic_percent > 75:
            traffic_status = "🟡 Высокое"
        else:
            traffic_status = "🟢 Нормальное"
        message += f"  • Использование трафика: {traffic_status} ({traffic_percent:.1f}%)\n"

    return message

def format_host_details(host):
    """Format host details for display"""
    status_emoji = "🟢" if not host["isDisabled"] else "🔴"

    message = f"*Информация о хосте*\n\n"
    message += f"{status_emoji} *Название*: {escape_markdown(host['remark'])}\n"
    message += f"🆔 *UUID*: `{host['uuid']}`\n"
    message += f"🌐 *Адрес*: {escape_markdown(host['address'])}:{host['port']}\n\n"
    
    # v208: inbound is an object with configProfileUuid/configProfileInboundUuid
    inbound = host.get('inbound') or {}
    config_profile_uuid = inbound.get('configProfileUuid')
    config_profile_inbound_uuid = inbound.get('configProfileInboundUuid')
    if config_profile_uuid or config_profile_inbound_uuid:
        cp = config_profile_uuid or '—'
        cpi = config_profile_inbound_uuid or '—'
        message += f"🔌 *Inbound*: cp=`{cp}` inbound=`{cpi}`\n"
    
    if host.get("path"):
        message += f"🛣️ *Путь*: {escape_markdown(host['path'])}\n"
    
    if host.get("sni"):
        message += f"🔒 *SNI*: {escape_markdown(host['sni'])}\n"
    
    if host.get("host"):
        message += f"🏠 *Host*: {escape_markdown(host['host'])}\n"
    
    if host.get("alpn"):
        message += f"🔄 *ALPN*: {escape_markdown(host['alpn'])}\n"
    
    if host.get("fingerprint"):
        message += f"👆 *Fingerprint*: {escape_markdown(host['fingerprint'])}\n"
    
    # allowInsecure removed in v208; keep Security Layer
    message += f"🛡️ *Security Layer*: {host.get('securityLayer', 'DEFAULT')}\n"
    
    return message

def format_system_stats(stats):
    """Format system statistics for display with detailed resource information"""
    message = f"*🖥️ Системная статистика*\n\n"

    # CPU Information
    cpu_cores = stats['cpu']['cores']
    physical_cores = stats['cpu']['physicalCores']
    message += f"💻 *Процессор*:\n"
    message += f"  • Ядер: {cpu_cores} ({physical_cores} физических)\n"
    message += f"  • Архитектура: {cpu_cores // physical_cores if physical_cores > 0 else 1} потоков на ядро\n\n"

    # Memory Information with detailed breakdown
    total_mem = stats['memory']['total']
    free_mem = stats['memory']['free']
    available_mem = stats['memory'].get('available', free_mem)
    active_mem = stats['memory'].get('active', 0)
    
    # Correct memory calculation for Linux systems
    # In Linux: used = total - available (not total - free)
    # available = free + buffers + cache
    used_mem = total_mem - available_mem
    cached_mem = available_mem - free_mem
    
    # Calculate percentages based on available memory (more accurate)
    used_percent = (used_mem / total_mem) * 100 if total_mem > 0 else 0
    free_percent = (free_mem / total_mem) * 100 if total_mem > 0 else 0
    available_percent = (available_mem / total_mem) * 100 if total_mem > 0 else 0
    cached_percent = (cached_mem / total_mem) * 100 if total_mem > 0 else 0
    
    message += f"🧠 *Память*:\n"
    message += f"  • Всего: {format_bytes(total_mem)}\n"
    message += f"  • Использовано: {format_bytes(used_mem)} ({used_percent:.1f}%)\n"
    message += f"  • Свободно: {format_bytes(free_mem)} ({free_percent:.1f}%)\n"
    message += f"  • Доступно: {format_bytes(available_mem)} ({available_percent:.1f}%)\n"
    message += f"  • Кэш/Буферы: {format_bytes(cached_mem)} ({cached_percent:.1f}%)\n"
    message += f"  • Активная: {format_bytes(active_mem)}\n"
    
    # Memory usage bar based on actual usage (total - available)
    memory_bar = create_progress_bar(used_percent, 20)
    message += f"  • Использование: `{memory_bar}` {used_percent:.1f}%\n\n"

    # Uptime with more details
    uptime_seconds = int(stats['uptime'])
    uptime_days = uptime_seconds // (24 * 3600)
    uptime_hours = (uptime_seconds % (24 * 3600)) // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime_seconds_remainder = uptime_seconds % 60

    message += f"⏱️ *Время работы*:\n"
    message += f"  • {uptime_days}д {uptime_hours}ч {uptime_minutes}м {uptime_seconds_remainder}с\n"
    message += f"  • Всего секунд: {uptime_seconds:,}\n\n"

    # Users Statistics
    users_data = stats['users']
    total_users = users_data['totalUsers']
    status_counts = users_data.get('statusCounts', {})
    
    message += f"👥 *Пользователи*:\n"
    message += f"  • Всего: {total_users}\n"
    
    # User status breakdown
    if status_counts:
        for status, count in status_counts.items():
            status_emoji = {
                'ACTIVE': '✅',
                'DISABLED': '❌', 
                'LIMITED': '⚠️',
                'EXPIRED': '⏰'
            }.get(status, '❓')
            status_percent = (count / total_users) * 100 if total_users > 0 else 0
            message += f"  • {status_emoji} {status}: {count} ({status_percent:.1f}%)\n"

    # Traffic information
    total_traffic = int(users_data.get('totalTrafficBytes', 0))
    message += f"  • Общий трафик: {format_bytes(total_traffic)}\n\n"

    # Online Statistics
    online_stats = stats['onlineStats']
    message += f"📊 *Активность пользователей*:\n"
    message += f"  • Сейчас онлайн: {online_stats['onlineNow']}\n"
    message += f"  • За последний день: {online_stats['lastDay']}\n"
    message += f"  • За последнюю неделю: {online_stats['lastWeek']}\n"
    message += f"  • Никогда не были онлайн: {online_stats['neverOnline']}\n"
    
    # Online percentage
    if total_users > 0:
        online_percent = (online_stats['onlineNow'] / total_users) * 100
        message += f"  • Онлайн сейчас: {online_percent:.1f}% от всех пользователей\n\n"
    else:
        message += "\n"

    # Nodes Statistics
    if 'nodes' in stats:
        nodes_data = stats['nodes']
        total_online = nodes_data.get('totalOnline', 0)
        message += f"🖥️ *Серверы*:\n"
        message += f"  • Онлайн: {total_online}\n"
        message += f"  • Статус: {'🟢 Все работают' if total_online > 0 else '🔴 Нет активных'}\n\n"

    # System Health Summary
    message += f"🏥 *Состояние системы*:\n"
    
    # Memory health
    if used_percent > 90:
        memory_status = "🔴 Критическое"
    elif used_percent > 75:
        memory_status = "🟡 Высокое"
    else:
        memory_status = "🟢 Нормальное"
    message += f"  • Память: {memory_status} ({used_percent:.1f}%)\n"
    
    # Uptime health
    if uptime_days > 30:
        uptime_status = "🟢 Стабильное"
    elif uptime_days > 7:
        uptime_status = "🟡 Хорошее"
    else:
        uptime_status = "🟡 Недавний перезапуск"
    message += f"  • Стабильность: {uptime_status} ({uptime_days} дней)\n"
    
    # Users health
    active_users = status_counts.get('ACTIVE', 0)
    if total_users > 0:
        active_percent = (active_users / total_users) * 100
        if active_percent > 80:
            users_status = "🟢 Отличное"
        elif active_percent > 60:
            users_status = "🟡 Хорошее"
        else:
            users_status = "🔴 Низкое"
        message += f"  • Пользователи: {users_status} ({active_percent:.1f}% активных)\n"

    return message

def format_bandwidth_stats(stats):
    """Format bandwidth statistics for display"""
    message = f"*Статистика трафика*\n\n"

    message += f"📅 *За последние 2 дня*:\n"
    message += f"  • Текущий: {stats['bandwidthLastTwoDays']['current']}\n"
    message += f"  • Предыдущий: {stats['bandwidthLastTwoDays']['previous']}\n"
    message += f"  • Разница: {stats['bandwidthLastTwoDays']['difference']}\n\n"

    message += f"📆 *За последние 7 дней*:\n"
    message += f"  • Текущий: {stats['bandwidthLastSevenDays']['current']}\n"
    message += f"  • Предыдущий: {stats['bandwidthLastSevenDays']['previous']}\n"
    message += f"  • Разница: {stats['bandwidthLastSevenDays']['difference']}\n\n"

    message += f"📊 *За последние 30 дней*:\n"
    message += f"  • Текущий: {stats['bandwidthLast30Days']['current']}\n"
    message += f"  • Предыдущий: {stats['bandwidthLast30Days']['previous']}\n"
    message += f"  • Разница: {stats['bandwidthLast30Days']['difference']}\n\n"

    message += f"📈 *За текущий месяц*:\n"
    message += f"  • Текущий: {stats['bandwidthCalendarMonth']['current']}\n"
    message += f"  • Предыдущий: {stats['bandwidthCalendarMonth']['previous']}\n"
    message += f"  • Разница: {stats['bandwidthCalendarMonth']['difference']}\n\n"

    message += f"📉 *За текущий год*:\n"
    message += f"  • Текущий: {stats['bandwidthCurrentYear']['current']}\n"
    message += f"  • Предыдущий: {stats['bandwidthCurrentYear']['previous']}\n"
    message += f"  • Разница: {stats['bandwidthCurrentYear']['difference']}\n"

    return message

def format_nodes_stats(nodes_data):
    """Format nodes statistics with system resources"""
    if not nodes_data or len(nodes_data) == 0:
        return "*🖥️ Статистика серверов*\n\n❌ Нет данных о серверах"
    
    message = f"*🖥️ Статистика серверов*\n\n"
    
    # Summary statistics
    total_nodes = len(nodes_data)
    connected_nodes = sum(1 for node in nodes_data if node.get('isConnected', False))
    online_nodes = sum(1 for node in nodes_data if node.get('isNodeOnline', False))
    running_xray = sum(1 for node in nodes_data if node.get('isXrayRunning', False))
    disabled_nodes = sum(1 for node in nodes_data if node.get('isDisabled', False))
    
    message += f"📊 *Общая статистика*:\n"
    message += f"  • Всего серверов: {total_nodes}\n"
    message += f"  • Подключено: {connected_nodes} ({connected_nodes/total_nodes*100:.1f}%)\n"
    message += f"  • Онлайн: {online_nodes} ({online_nodes/total_nodes*100:.1f}%)\n"
    message += f"  • Xray работает: {running_xray} ({running_xray/total_nodes*100:.1f}%)\n"
    message += f"  • Отключено: {disabled_nodes} ({disabled_nodes/total_nodes*100:.1f}%)\n\n"
    
    # System resources summary
    total_ram = 0
    total_cpu_cores = 0
    total_traffic_used = 0
    total_traffic_limit = 0
    total_users_online = 0
    
    for node in nodes_data:
        if node.get('totalRam'):
            try:
                # Parse RAM string like "1.01 GB"
                ram_str = node['totalRam'].replace(' GB', '').replace(' MB', '')
                if 'GB' in node['totalRam']:
                    total_ram += float(ram_str) * 1024  # Convert GB to MB
                elif 'MB' in node['totalRam']:
                    total_ram += float(ram_str)
            except:
                pass
        
        if node.get('cpuCount'):
            total_cpu_cores += node['cpuCount']
        
        if node.get('trafficUsedBytes'):
            total_traffic_used += node['trafficUsedBytes']
        
        if node.get('trafficLimitBytes'):
            total_traffic_limit += node['trafficLimitBytes']
        
        if node.get('usersOnline'):
            total_users_online += node['usersOnline']
    
    if total_ram > 0:
        message += f"💻 *Системные ресурсы*:\n"
        message += f"  • Общая RAM: {total_ram/1024:.1f} GB\n"
        message += f"  • Общие CPU ядра: {total_cpu_cores}\n"
        message += f"  • Пользователей онлайн: {total_users_online}\n\n"
    
    if total_traffic_limit > 0:
        traffic_percent = (total_traffic_used / total_traffic_limit) * 100
        message += f"📈 *Общий трафик*:\n"
        message += f"  • Использовано: {format_bytes(total_traffic_used)}\n"
        message += f"  • Лимит: {format_bytes(total_traffic_limit)}\n"
        message += f"  • Осталось: {format_bytes(total_traffic_limit - total_traffic_used)}\n"
        message += f"  • Процент: {traffic_percent:.1f}%\n"
        
        # Overall traffic bar
        traffic_bar = create_progress_bar(traffic_percent, 20)
        message += f"  • Прогресс: `{traffic_bar}` {traffic_percent:.1f}%\n\n"
    
    # Individual node details
    message += f"🖥️ *Детали серверов*:\n"
    
    for i, node in enumerate(nodes_data, 1):
        status_emoji = "🟢" if node.get('isConnected', False) and not node.get('isDisabled', False) else "🔴"
        
        message += f"\n{i}. {status_emoji} *{escape_markdown(node.get('name', 'Unknown'))}*\n"
        message += f"   • Адрес: {escape_markdown(node.get('address', 'N/A'))}:{node.get('port', 'N/A')}\n"
        message += f"   • Статус: {'Подключен' if node.get('isConnected', False) else 'Отключен'}\n"
        message += f"   • Xray: {'Запущен' if node.get('isXrayRunning', False) else 'Остановлен'}\n"
        
        if node.get('usersOnline') is not None:
            message += f"   • Пользователей онлайн: {node['usersOnline']}\n"
        
        if node.get('totalRam'):
            message += f"   • RAM: {escape_markdown(node['totalRam'])}\n"
        
        if node.get('cpuCount'):
            message += f"   • CPU: {node['cpuCount']} ядер\n"
        
        if node.get('trafficLimitBytes') and node.get('trafficUsedBytes'):
            used = node['trafficUsedBytes']
            limit = node['trafficLimitBytes']
            percent = (used / limit) * 100 if limit > 0 else 0
            message += f"   • Трафик: {format_bytes(used)}/{format_bytes(limit)} ({percent:.1f}%)\n"
    
    return message

def format_inbound_details(inbound):
    """Format inbound details for display with enhanced formatting"""
    message = f"🔌 *Детальная информация об Inbound*\n\n"
    
    # Basic information
    message += f"📋 *Основные данные:*\n"
    message += f"  🏷️ *Тег*: {escape_markdown(inbound['tag'])}\n"
    message += f"  🆔 *UUID*: `{inbound['uuid']}`\n"
    message += f"  🔌 *Тип*: {inbound['type']}\n"
    message += f"  🔢 *Порт*: {inbound['port']}\n"
    
    # Status information
    status_emoji = "🟢" if inbound.get('enabled', True) else "🔴"
    status_text = "Активен" if inbound.get('enabled', True) else "Отключен"
    message += f"  📊 *Статус*: {status_emoji} {status_text}\n"
    
    # Network and security
    if inbound.get('network'):
        message += f"  🌐 *Сеть*: {inbound['network']}\n"
    
    if inbound.get('security'):
        message += f"  🔒 *Безопасность*: {inbound['security']}\n"
    
    # User statistics
    if 'users' in inbound:
        users = inbound['users']
        total_users = users.get('enabled', 0) + users.get('disabled', 0)
        message += f"\n👥 *Пользователи*:\n"
        message += f"  • Активных: {users.get('enabled', 0)}\n"
        message += f"  • Отключенных: {users.get('disabled', 0)}\n"
        message += f"  • Всего: {total_users}\n"
        if total_users > 0:
            active_percentage = (users.get('enabled', 0) / total_users) * 100
            message += f"  • Активность: {active_percentage:.1f}%\n"
    
    # Node statistics
    if 'nodes' in inbound:
        nodes = inbound['nodes']
        total_nodes = nodes.get('enabled', 0) + nodes.get('disabled', 0)
        message += f"\n🖥️ *Серверы*:\n"
        message += f"  • Активных: {nodes.get('enabled', 0)}\n"
        message += f"  • Отключенных: {nodes.get('disabled', 0)}\n"
        message += f"  • Всего: {total_nodes}\n"
        if total_nodes > 0:
            active_percentage = (nodes.get('enabled', 0) / total_nodes) * 100
            message += f"  • Активность: {active_percentage:.1f}%\n"
    
    # Additional information
    if inbound.get('createdAt'):
        message += f"\n📅 *Создан*: {inbound['createdAt']}\n"
    if inbound.get('updatedAt'):
        message += f"🔄 *Обновлен*: {inbound['updatedAt']}\n"
    
    # Configuration details
    if inbound.get('settings'):
        message += f"\n⚙️ *Настройки конфигурации:*\n"
        for key, value in inbound['settings'].items():
            if isinstance(value, dict):
                message += f"  • {key}:\n"
                for sub_key, sub_value in value.items():
                    message += f"    - {sub_key}: {sub_value}\n"
            else:
                message += f"  • {key}: {value}\n"
    
    return message
