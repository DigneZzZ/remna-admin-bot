from datetime import datetime
import logging
import re

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
        return "0 B"
    
    if isinstance(bytes_value, str):
        try:
            bytes_value = float(bytes_value)
        except (ValueError, TypeError):
            return bytes_value
    
    if bytes_value == 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def parse_bytes(value_str):
    """Parse human-readable bytes format to bytes integer"""
    if not value_str:
        return 0
    
    if isinstance(value_str, (int, float)):
        return int(value_str)
    
    value_str = str(value_str).strip().upper()
    
    # Extract number and unit
    match = re.match(r'^([\d.]+)\s*([KMGT]?B?)$', value_str)
    if not match:
        try:
            return int(float(value_str))
        except (ValueError, TypeError):
            return 0
    
    number, unit = match.groups()
    number = float(number)
    
    # Convert to bytes
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
        'K': 1024,
        'M': 1024 ** 2,
        'G': 1024 ** 3,
        'T': 1024 ** 4
    }
    
    return int(number * multipliers.get(unit, 1))

def escape_markdown(text):
    """Escape Markdown special characters for Telegram"""
    if text is None:
        return ""
    
    text = str(text)
    escape_chars = [
        ('\\', '\\\\'),
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
    except Exception:
        expire_status = "📅"
        expire_text = user['expireAt'][:10] if 'expireAt' in user and user['expireAt'] else "Не указано"
    
    # Статус пользователя
    status_map = {
        'ACTIVE': '🟢 Активен',
        'DISABLED': '🔴 Отключен',
        'EXPIRED': '🟡 Истек',
        'LIMITED': '🟠 Лимит исчерпан'
    }
    status_text = status_map.get(user.get('status'), f"❓ {user.get('status', 'Неизвестно')}")
    
    # Расчет процента использования трафика
    used_traffic = user.get('usedTrafficBytes', 0)
    limit_traffic = user.get('trafficLimitBytes', 0)
    traffic_percentage = 0
    if limit_traffic > 0:
        traffic_percentage = (used_traffic / limit_traffic) * 100
    
    # Прогресс-бар трафика
    progress_bar = create_progress_bar(traffic_percentage)
    
    try:
        message = f"👤 *Пользователь:* {escape_markdown(user['username'])}\n"
        message += f"🆔 *UUID:* `{user['uuid']}`\n"
        message += f"🔑 *Короткий UUID:* `{user['shortUuid']}`\n"
        message += f"📝 *UUID подписки:* `{user['subscriptionUuid']}`\n\n"
        
        # URL подписки в блоке кода
        subscription_url = user.get('subscriptionUrl', '')
        if subscription_url:
            message += f"🔗 *URL подписки:* `{subscription_url}`\n\n"
        else:
            message += f"🔗 *URL подписки:* Не указан\n\n"
        
        message += f"📊 *Статус:* {status_text}\n"
        message += f"📈 *Трафик:* {format_bytes(used_traffic)}/{format_bytes(limit_traffic)} ({traffic_percentage:.1f}%)\n"
        message += f"     {progress_bar}\n"
        message += f"🔄 *Стратегия сброса:* {user.get('trafficLimitStrategy', 'NO_RESET')}\n"
        message += f"{expire_status} *Истекает:* {expire_text}\n\n"
        
        # Дополнительная информация
        if user.get('description'):
            desc = user['description'][:100] + "..." if len(user['description']) > 100 else user['description']
            message += f"📝 *Описание:* {escape_markdown(desc)}\n"
        
        if user.get('tag'):
            message += f"🏷️ *Тег:* {escape_markdown(str(user['tag']))}\n"
        
        if user.get('telegramId'):
            message += f"📱 *Telegram ID:* {user['telegramId']}\n"
        
        if user.get('email'):
            message += f"📧 *Email:* {escape_markdown(str(user['email']))}\n"
        
        if user.get('hwidDeviceLimit'):
            device_count = user.get('hwidConnectedDevices', 0)
            message += f"📱 *Устройства:* {device_count}/{user['hwidDeviceLimit']}\n"
        
        # Статистика активности
        if user.get('lastActiveAt'):
            try:
                last_active = datetime.fromisoformat(user['lastActiveAt'].replace('Z', '+00:00'))
                days_ago = (datetime.now().astimezone() - last_active).days
                if days_ago == 0:
                    active_text = "Сегодня"
                elif days_ago == 1:
                    active_text = "Вчера"
                else:
                    active_text = f"{days_ago} дней назад"
                message += f"🕐 *Последняя активность:* {active_text}\n"
            except Exception:
                message += f"🕐 *Последняя активность:* {user['lastActiveAt'][:10]}\n"
        
        message += f"\n⏱️ *Создан:* {user['createdAt'][:10]}\n"
        message += f"🔄 *Обновлен:* {user['updatedAt'][:10]}\n"
        
        return message
        
    except Exception as e:
        logger.warning(f"Error in format_user_details: {e}")
        return format_user_details_safe(user)

def format_user_details_safe(user):
    """Format user details without Markdown (safe fallback)"""
    try:
        expire_date = datetime.fromisoformat(user['expireAt'].replace('Z', '+00:00'))
        days_left = (expire_date - datetime.now().astimezone()).days
        expire_status = "🟢" if days_left > 7 else "🟡" if days_left > 0 else "🔴"
        expire_text = f"{user['expireAt'][:10]} ({days_left} дней)"
    except Exception:
        expire_status = "📅"
        expire_text = user['expireAt'][:10] if 'expireAt' in user and user['expireAt'] else "Не указано"
    
    status_map = {
        'ACTIVE': '🟢 Активен',
        'DISABLED': '🔴 Отключен',
        'EXPIRED': '🟡 Истек',
        'LIMITED': '🟠 Лимит исчерпан'
    }
    status_text = status_map.get(user.get('status'), f"❓ {user.get('status', 'Неизвестно')}")
    
    message = f"👤 Пользователь: {user['username']}\n"
    message += f"🆔 UUID: {user['uuid']}\n"
    message += f"🔑 Короткий UUID: {user['shortUuid']}\n"
    message += f"📝 UUID подписки: {user['subscriptionUuid']}\n\n"
    
    subscription_url = user.get('subscriptionUrl', '')
    if subscription_url:
        message += f"🔗 URL подписки:\n`{subscription_url}`\n\n"
    else:
        message += f"🔗 URL подписки: Не указан\n\n"
    
    message += f"📊 Статус: {status_text}\n"
    message += f"📈 Трафик: {format_bytes(user.get('usedTrafficBytes', 0))}/{format_bytes(user.get('trafficLimitBytes', 0))}\n"
    message += f"🔄 Стратегия сброса: {user.get('trafficLimitStrategy', 'NO_RESET')}\n"
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
        device_count = user.get('hwidConnectedDevices', 0)
        message += f"📱 Устройства: {device_count}/{user['hwidDeviceLimit']}\n"
    
    message += f"\n⏱️ Создан: {user['createdAt'][:10]}\n"
    message += f"🔄 Обновлен: {user['updatedAt'][:10]}\n"
    
    return message

def create_progress_bar(percentage, length=10):
    """Create a visual progress bar"""
    filled_length = int(length * percentage // 100)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"`{bar}`"

def format_node_details(node):
    """Format node details for display"""
    status_emoji = "🟢" if node.get("isConnected") and not node.get("isDisabled") else "🔴"
    
    message = f"🖥️ *Сервер: {escape_markdown(node['name'])}*\n\n"
    message += f"🆔 *UUID:* `{node['uuid']}`\n"
    message += f"🌐 *Адрес:* {escape_markdown(node['address'])}:{node['port']}\n"
    message += f"📊 *Статус:* {status_emoji}\n\n"
    
    # Детальный статус
    message += f"🔍 *Детальный статус:*\n"
    message += f"  • Подключен: {'✅' if node.get('isConnected') else '❌'}\n"
    message += f"  • Включен: {'✅' if not node.get('isDisabled') else '❌'}\n"
    message += f"  • Онлайн: {'✅' if node.get('isNodeOnline') else '❌'}\n"
    message += f"  • Xray запущен: {'✅' if node.get('isXrayRunning') else '❌'}\n\n"
    
    # Система
    if node.get("xrayVersion"):
        message += f"📦 *Xray версия:* {escape_markdown(node['xrayVersion'])}\n"
    
    if node.get("xrayUptime"):
        message += f"⏱️ *Uptime:* {escape_markdown(node['xrayUptime'])}\n"
    
    if node.get("countryCode"):
        message += f"🌍 *Страна:* {node['countryCode']}\n"
    
    if node.get("consumptionMultiplier"):
        message += f"📊 *Множитель потребления:* {node['consumptionMultiplier']}x\n"
    
    # Трафик
    if node.get("trafficLimitBytes") is not None:
        used = node.get('trafficUsedBytes', 0)
        limit = node['trafficLimitBytes']
        percentage = (used / limit * 100) if limit > 0 else 0
        progress_bar = create_progress_bar(percentage)
        
        message += f"\n📈 *Трафик:* {format_bytes(used)}/{format_bytes(limit)} ({percentage:.1f}%)\n"
        message += f"     {progress_bar}\n"
    
    # Пользователи
    if node.get("usersOnline") is not None:
        message += f"👥 *Пользователей онлайн:* {node['usersOnline']}\n"
    
    # Система
    if node.get("cpuModel"):
        message += f"\n💻 *Система:*\n"
        message += f"  • CPU: {escape_markdown(node['cpuModel'])}"
        if node.get("cpuCount"):
            message += f" ({node['cpuCount']} ядер)"
        message += "\n"
        
        if node.get("totalRam"):
            message += f"  • RAM: {escape_markdown(node['totalRam'])}\n"
    
    return message

def format_host_details(host):
    """Format host details for display"""
    status_emoji = "🟢" if not host.get("isDisabled") else "🔴"
    
    message = f"🌐 *Хост: {escape_markdown(host.get('remark', 'Без названия'))}*\n\n"
    message += f"🆔 *UUID:* `{host['uuid']}`\n"
    message += f"🌐 *Адрес:* {escape_markdown(host['address'])}:{host['port']}\n"
    message += f"📊 *Статус:* {status_emoji}\n\n"
    
    message += f"🔌 *Inbound UUID:* `{host['inboundUuid']}`\n"
    
    # Дополнительные параметры
    params = []
    if host.get("path"):
        params.append(f"🛣️ Путь: {escape_markdown(host['path'])}")
    if host.get("sni"):
        params.append(f"🔒 SNI: {escape_markdown(host['sni'])}")
    if host.get("host"):
        params.append(f"🏠 Host: {escape_markdown(host['host'])}")
    if host.get("alpn"):
        params.append(f"🔄 ALPN: {escape_markdown(host['alpn'])}")
    if host.get("fingerprint"):
        params.append(f"👆 Fingerprint: {escape_markdown(host['fingerprint'])}")
    
    if params:
        message += "\n📋 *Параметры:*\n"
        for param in params:
            message += f"  • {param}\n"
    
    message += f"\n🔐 *Allow Insecure:* {'✅' if host.get('allowInsecure') else '❌'}\n"
    message += f"🛡️ *Security Layer:* {host.get('securityLayer', 'DEFAULT')}\n"
    
    return message

def format_inbound_details(inbound):
    """Format inbound details for display"""
    message = f"📡 *Inbound: {escape_markdown(inbound.get('remark', inbound.get('tag', 'Без названия')))}*\n\n"
    message += f"🆔 *UUID:* `{inbound['uuid']}`\n"
    message += f"🏷️ *Тег:* {escape_markdown(inbound['tag'])}\n"
    message += f"🔌 *Тип:* {inbound['type']}\n"
    message += f"🔢 *Порт:* {inbound['port']}\n\n"
    
    # Настройки сети
    if inbound.get('network'):
        message += f"🌐 *Сеть:* {inbound['network']}\n"
    
    if inbound.get('security'):
        message += f"🔒 *Безопасность:* {inbound['security']}\n"
    
    # Дополнительные параметры
    if inbound.get('path'):
        message += f"🛣️ *Путь:* {escape_markdown(inbound['path'])}\n"
    
    if inbound.get('host'):
        message += f"🏠 *Host:* {escape_markdown(inbound['host'])}\n"
    
    # Статистика пользователей и нод
    if 'users' in inbound:
        users = inbound['users']
        total_users = users.get('enabled', 0) + users.get('disabled', 0)
        message += f"\n👥 *Пользователи:* {total_users} всего\n"
        message += f"  • Активные: {users.get('enabled', 0)}\n"
        message += f"  • Отключенные: {users.get('disabled', 0)}\n"
    
    if 'nodes' in inbound:
        nodes = inbound['nodes']
        total_nodes = nodes.get('enabled', 0) + nodes.get('disabled', 0)
        message += f"\n🖥️ *Серверы:* {total_nodes} всего\n"
        message += f"  • Активные: {nodes.get('enabled', 0)}\n"
        message += f"  • Отключенные: {nodes.get('disabled', 0)}\n"
    
    return message

def format_system_stats(stats):
    """Format system statistics for display"""
    message = f"📊 *Системная статистика*\n\n"
    
    # Система
    if 'system' in stats:
        sys_info = stats['system']
        message += f"🖥️ *Система:*\n"
        message += f"  • OS: {sys_info.get('os', 'N/A')}\n"
        message += f"  • Arch: {sys_info.get('arch', 'N/A')}\n"
        if sys_info.get('version'):
            message += f"  • Version: {sys_info['version']}\n"
        message += "\n"
    
    # CPU и память
    if 'cpu' in stats:
        cpu = stats['cpu']
        message += f"⚡ *CPU:*\n"
        message += f"  • Использование: {cpu.get('usage', 0):.1f}%\n"
        if cpu.get('cores'):
            message += f"  • Ядра: {cpu['cores']}\n"
        message += "\n"
    
    if 'memory' in stats:
        mem = stats['memory']
        total_gb = mem.get('total', 0) / (1024**3)
        used_gb = mem.get('used', 0) / (1024**3)
        usage_percent = (mem.get('used', 0) / mem.get('total', 1)) * 100
        
        message += f"💾 *Память:*\n"
        message += f"  • Всего: {total_gb:.1f} GB\n"
        message += f"  • Использовано: {used_gb:.1f} GB ({usage_percent:.1f}%)\n"
        message += f"  • {create_progress_bar(usage_percent)}\n\n"
    
    # Uptime
    if 'uptime' in stats:
        uptime_seconds = stats['uptime']
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        message += f"⏱️ *Uptime:* {days}д {hours}ч {minutes}м\n\n"
    
    # Пользователи
    if 'users' in stats:
        users = stats['users']
        message += f"👥 *Пользователи:*\n"
        message += f"  • Всего: {users.get('totalUsers', 0)}\n"
        
        if 'statusCounts' in users:
            for status, count in users['statusCounts'].items():
                status_emoji = {
                    'ACTIVE': '🟢',
                    'DISABLED': '🔴',
                    'EXPIRED': '🟡',
                    'LIMITED': '🟠'
                }.get(status, '⚪')
                message += f"  • {status_emoji} {status}: {count}\n"
        
        total_traffic = users.get('totalTrafficBytes', 0)
        message += f"  • Общий трафик: {format_bytes(total_traffic)}\n\n"
    
    # Онлайн статистика
    if 'onlineStats' in stats:
        online = stats['onlineStats']
        message += f"📈 *Активность:*\n"
        message += f"  • Сейчас онлайн: {online.get('onlineNow', 0)}\n"
        message += f"  • За день: {online.get('lastDay', 0)}\n"
        message += f"  • За неделю: {online.get('lastWeek', 0)}\n"
        message += f"  • Никогда не заходили: {online.get('neverOnline', 0)}\n"
    
    return message

def format_bandwidth_stats(stats):
    """Format bandwidth statistics for display"""
    message = f"📈 *Статистика трафика*\n\n"
    
    periods = [
        ('bandwidthLastTwoDays', '📅 За последние 2 дня'),
        ('bandwidthLastSevenDays', '📆 За последние 7 дней'),
        ('bandwidthLast30Days', '📊 За последние 30 дней'),
        ('bandwidthCalendarMonth', '📅 За текущий месяц'),
        ('bandwidthCurrentYear', '📊 За текущий год')
    ]
    
    for key, title in periods:
        if key in stats:
            data = stats[key]
            current = format_bytes(data.get('current', 0))
            previous = format_bytes(data.get('previous', 0))
            difference = data.get('difference', 0)
            
            # Определяем тренд
            if difference > 0:
                trend = f"📈 +{format_bytes(difference)}"
            elif difference < 0:
                trend = f"📉 {format_bytes(difference)}"
            else:
                trend = "📊 Без изменений"
            
            message += f"{title}:\n"
            message += f"  • Текущий: {current}\n"
            message += f"  • Предыдущий: {previous}\n"
            message += f"  • {trend}\n\n"
    
    return message

def format_user_stats(user, stats=None):
    """Format comprehensive user statistics"""
    message = f"📊 *Статистика пользователя: {escape_markdown(user['username'])}*\n\n"
    
    # Основная информация
    status_map = {
        'ACTIVE': '🟢 Активен',
        'DISABLED': '🔴 Отключен', 
        'EXPIRED': '🟡 Истек',
        'LIMITED': '🟠 Лимит исчерпан'
    }
    status_text = status_map.get(user.get('status'), f"❓ {user.get('status', 'Неизвестно')}")
    message += f"📊 *Статус:* {status_text}\n"
    
    # Трафик
    used_traffic = user.get('usedTrafficBytes', 0)
    limit_traffic = user.get('trafficLimitBytes', 0)
    
    if limit_traffic > 0:
        percentage = (used_traffic / limit_traffic) * 100
        remaining = limit_traffic - used_traffic
        progress_bar = create_progress_bar(percentage)
        
        message += f"📈 *Трафик:*\n"
        message += f"  • Использовано: {format_bytes(used_traffic)} ({percentage:.1f}%)\n"
        message += f"  • Лимит: {format_bytes(limit_traffic)}\n"
        message += f"  • Осталось: {format_bytes(remaining)}\n"
        message += f"  • {progress_bar}\n\n"
    else:
        message += f"📈 *Трафик:* {format_bytes(used_traffic)} (безлимитный)\n\n"
    
    # Устройства
    if user.get('hwidDeviceLimit'):
        connected = user.get('hwidConnectedDevices', 0)
        limit = user['hwidDeviceLimit']
        device_percentage = (connected / limit * 100) if limit > 0 else 0
        device_bar = create_progress_bar(device_percentage)
        
        message += f"📱 *Устройства:*\n"
        message += f"  • Подключено: {connected}/{limit}\n"
        message += f"  • {device_bar}\n\n"
    
    # Временная информация
    try:
        created = datetime.fromisostring(user['createdAt'].replace('Z', '+00:00'))
        days_since_creation = (datetime.now().astimezone() - created).days
        message += f"📅 *Время существования:* {days_since_creation} дней\n"
        
        if user.get('expireAt'):
            expire_date = datetime.fromisostring(user['expireAt'].replace('Z', '+00:00'))
            days_left = (expire_date - datetime.now().astimezone()).days
            if days_left > 0:
                message += f"⏰ *До истечения:* {days_left} дней\n"
            else:
                message += f"⏰ *Истек:* {abs(days_left)} дней назад\n"
        
        if user.get('lastActiveAt'):
            last_active = datetime.fromisostring(user['lastActiveAt'].replace('Z', '+00:00'))
            days_ago = (datetime.now().astimezone() - last_active).days
            if days_ago == 0:
                message += f"🕐 *Последняя активность:* Сегодня\n"
            elif days_ago == 1:
                message += f"🕐 *Последняя активность:* Вчера\n"
            else:
                message += f"🕐 *Последняя активность:* {days_ago} дней назад\n"
    except Exception:
        pass
    
    # Дополнительная статистика (если передана)
    if stats:
        if 'sessionsCount' in stats:
            message += f"🔗 *Сессий подключений:* {stats['sessionsCount']}\n"
        
        if 'avgDailyTraffic' in stats:
            message += f"📊 *Средний дневной трафик:* {format_bytes(stats['avgDailyTraffic'])}\n"
    
    return message