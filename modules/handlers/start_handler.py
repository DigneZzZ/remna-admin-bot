from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from modules.config import (
    MAIN_MENU, DASHBOARD_SHOW_SYSTEM_STATS, DASHBOARD_SHOW_SERVER_INFO,
    DASHBOARD_SHOW_USERS_COUNT, DASHBOARD_SHOW_NODES_COUNT, 
    DASHBOARD_SHOW_TRAFFIC_STATS, DASHBOARD_SHOW_UPTIME
)
from modules.utils.auth import check_admin
from modules.api.users import UserAPI
from modules.api.nodes import NodeAPI
from modules.api.inbounds import InboundAPI
from modules.api.system import SystemAPI
from modules.utils.formatters import format_bytes, safe_edit_message
import logging

logger = logging.getLogger(__name__)

@check_admin
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler with enhanced welcome"""
    # Clear any existing conversation data
    context.user_data.clear()
    
    # Show main menu
    await show_main_menu(update, context)
    return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show enhanced main menu with comprehensive options and real-time statistics"""
    
    # Enhanced keyboard with better organization
    keyboard = [
        [
            InlineKeyboardButton("👥 Пользователи", callback_data="users"),
            InlineKeyboardButton("🖥️ Серверы", callback_data="nodes")
        ],
        [
            InlineKeyboardButton("🌐 Хосты", callback_data="hosts"),
            InlineKeyboardButton("📡 Inbound'ы", callback_data="inbounds")
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            InlineKeyboardButton("🔧 Массовые операции", callback_data="bulk")
        ],
        [
            InlineKeyboardButton("➕ Создать пользователя", callback_data="create_user"),
            InlineKeyboardButton("🔍 Быстрый поиск", callback_data="search_users_quick")
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="bot_settings"),
            InlineKeyboardButton("📚 Справка", callback_data="help")
        ],
        [
            InlineKeyboardButton("🔄 Обновить", callback_data="refresh_main"),
            InlineKeyboardButton("ℹ️ О боте", callback_data="about")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Get comprehensive system statistics
    stats_text = await get_enhanced_system_stats()
    
    message = "🎛️ *RemnaWave Admin Panel*\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += stats_text + "\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "🎯 Выберите раздел для управления:"

    if update.callback_query:
        await safe_edit_message(update.callback_query, message, reply_markup, "Markdown")
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def get_enhanced_system_stats():
    """Get enhanced system statistics with better error handling"""
    stats_sections = []
    
    try:
        # Real-time system information
        if DASHBOARD_SHOW_SYSTEM_STATS:
            system_stats = await get_system_info_stats()
            if system_stats:
                stats_sections.append(system_stats)
        
        # Users statistics with enhanced details
        if DASHBOARD_SHOW_USERS_COUNT:
            user_stats = await get_enhanced_user_stats()
            if user_stats:
                stats_sections.append(user_stats)
        
        # Nodes statistics with status details
        if DASHBOARD_SHOW_NODES_COUNT:
            node_stats = await get_enhanced_node_stats()
            if node_stats:
                stats_sections.append(node_stats)
        
        # Traffic statistics with real-time data
        if DASHBOARD_SHOW_TRAFFIC_STATS:
            traffic_stats = await get_enhanced_traffic_stats()
            if traffic_stats:
                stats_sections.append(traffic_stats)
        
        # Server/Inbound information
        if DASHBOARD_SHOW_SERVER_INFO:
            server_stats = await get_enhanced_server_stats()
            if server_stats:
                stats_sections.append(server_stats)
        
        # Combine all sections
        if stats_sections:
            return "\n".join(stats_sections)
        else:
            return "📊 *Статистика*\n\nОтображение статистики отключено в настройках."
        
    except Exception as e:
        logger.error(f"Error getting enhanced system stats: {e}")
        return "📊 *Статистика временно недоступна*\n\n⚠️ Проверьте подключение к API"

async def get_system_info_stats():
    """Get system information statistics"""
    try:
        # Try to get from API first
        try:
            system_response = await SystemAPI.get_system_stats()
            if system_response and 'response' in system_response:
                stats = system_response['response']
                
                system_stats = "🖥️ *Система*:\n"
                
                # CPU information
                if 'cpu' in stats:
                    cpu = stats['cpu']
                    cores = cpu.get('cores', 'N/A')
                    usage = cpu.get('usage', 0)
                    system_stats += f"  • CPU: {cores} ядер, {usage:.1f}%\n"
                
                # Memory information
                if 'memory' in stats:
                    mem = stats['memory']
                    total_gb = mem.get('total', 0) / (1024**3)
                    used_gb = mem.get('used', 0) / (1024**3)
                    percent = (mem.get('used', 0) / mem.get('total', 1)) * 100
                    system_stats += f"  • RAM: {used_gb:.1f}/{total_gb:.1f} GB ({percent:.1f}%)\n"
                
                # Uptime information
                if DASHBOARD_SHOW_UPTIME and 'uptime' in stats:
                    uptime_seconds = stats['uptime']
                    days = uptime_seconds // 86400
                    hours = (uptime_seconds % 86400) // 3600
                    minutes = (uptime_seconds % 3600) // 60
                    system_stats += f"  • Uptime: {days}д {hours}ч {minutes}м\n"
                
                return system_stats
        except:
            pass
        
        # Fallback to psutil if available
        try:
            import psutil
            import os
            from datetime import datetime
            
            # Detect if running in Docker
            in_docker = os.path.exists('/.dockerenv')
            
            if in_docker:
                # Docker-specific stats with improved error handling
                cpu_cores, cpu_percent, memory = await get_docker_stats()
            else:
                # Host system stats
                cpu_cores = psutil.cpu_count()
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
            
            system_stats = f"🖥️ *Система*:\n"
            system_stats += f"  • CPU: {cpu_cores} ядер, {cpu_percent:.1f}%\n"
            system_stats += f"  • RAM: {format_bytes(memory.used)}/{format_bytes(memory.total)} ({memory.percent:.1f}%)\n"
            
            if DASHBOARD_SHOW_UPTIME:
                uptime_seconds = psutil.boot_time()
                current_time = datetime.now().timestamp()
                uptime = int(current_time - uptime_seconds)
                uptime_days = uptime // (24 * 3600)
                uptime_hours = (uptime % (24 * 3600)) // 3600
                uptime_minutes = (uptime % 3600) // 60
                system_stats += f"  • Uptime: {uptime_days}д {uptime_hours}ч {uptime_minutes}м\n"
            
            return system_stats
            
        except ImportError:
            logger.warning("psutil not available, skipping local system stats")
        except Exception as e:
            logger.error(f"Error getting local system stats: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting system info stats: {e}")
        return None

async def get_docker_stats():
    """Get Docker container statistics with improved error handling"""
    import psutil
    import os
    
    try:
        # CPU cores detection for Docker
        cpu_cores = psutil.cpu_count()
        cpu_quota_files = [
            '/sys/fs/cgroup/cpu/cpu.cfs_quota_us',
            '/sys/fs/cgroup/cpu.max'
        ]
        cpu_period_files = [
            '/sys/fs/cgroup/cpu/cpu.cfs_period_us',
            None
        ]
        
        for quota_file, period_file in zip(cpu_quota_files, cpu_period_files):
            if os.path.exists(quota_file):
                try:
                    with open(quota_file, 'r') as f:
                        content = f.read().strip()
                    
                    if period_file and os.path.exists(period_file):
                        quota = int(content)
                        with open(period_file, 'r') as f:
                            period = int(f.read().strip())
                        
                        if quota > 0 and period > 0:
                            cpu_cores = max(1, quota // period)
                    elif 'max' not in content:
                        parts = content.split()
                        if len(parts) >= 2:
                            quota = int(parts[0])
                            period = int(parts[1])
                            if quota > 0 and period > 0:
                                cpu_cores = max(1, quota // period)
                    break
                except:
                    continue
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory detection for Docker
        memory_files = [
            ('/sys/fs/cgroup/memory/memory.limit_in_bytes', '/sys/fs/cgroup/memory/memory.usage_in_bytes'),
            ('/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory.current')
        ]
        
        memory_limit = None
        memory_usage = None
        
        for limit_file, usage_file in memory_files:
            if os.path.exists(limit_file) and os.path.exists(usage_file):
                try:
                    with open(limit_file, 'r') as f:
                        limit_content = f.read().strip()
                    
                    with open(usage_file, 'r') as f:
                        memory_usage = int(f.read().strip())
                    
                    if limit_content == 'max':
                        memory_limit = psutil.virtual_memory().total
                    else:
                        memory_limit = int(limit_content)
                    break
                except:
                    continue
        
        if memory_limit is None or memory_usage is None:
            vm = psutil.virtual_memory()
            memory_limit = vm.total
            memory_usage = vm.used
        
        class DockerMemory:
            def __init__(self, total, used):
                self.total = total
                self.used = used
                self.free = total - used
                self.percent = (used / total * 100) if total > 0 else 0
        
        memory = DockerMemory(memory_limit, memory_usage)
        
        return cpu_cores, cpu_percent, memory
        
    except Exception as e:
        logger.warning(f"Error reading Docker cgroup stats, using psutil: {e}")
        return psutil.cpu_count(), psutil.cpu_percent(interval=0.1), psutil.virtual_memory()

async def get_enhanced_user_stats():
    """Get enhanced user statistics"""
    try:
        users_response = await UserAPI.get_all_users()
        if not users_response or 'response' not in users_response:
            return None
        
        users = users_response['response']
        users_count = len(users)
        
        if users_count == 0:
            return "👥 *Пользователи*: 0\n"
        
        # Detailed status breakdown
        status_counts = {}
        total_traffic = 0
        connected_devices = 0
        expired_count = 0
        
        for user in users:
            status = user.get('status', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Traffic statistics
            used_traffic = user.get('usedTrafficBytes', 0)
            if isinstance(used_traffic, (int, float)):
                total_traffic += used_traffic
            
            # Device statistics
            devices = user.get('hwidConnectedDevices', 0)
            if isinstance(devices, (int, float)):
                connected_devices += devices
            
            # Expiration check
            if user.get('status') == 'EXPIRED':
                expired_count += 1
        
        user_stats = f"👥 *Пользователи* ({users_count} всего):\n"
        
        # Status breakdown with emojis
        status_emojis = {
            'ACTIVE': '🟢',
            'DISABLED': '🔴', 
            'EXPIRED': '🟡',
            'LIMITED': '🟠'
        }
        
        status_line = []
        for status, count in status_counts.items():
            if count > 0:
                emoji = status_emojis.get(status, '⚪')
                status_line.append(f"{emoji}{count}")
        
        if status_line:
            user_stats += f"  • Статусы: {' | '.join(status_line)}\n"
        
        # Traffic and devices
        if total_traffic > 0:
            avg_traffic = total_traffic / users_count if users_count > 0 else 0
            user_stats += f"  • Трафик: {format_bytes(total_traffic)} (сред: {format_bytes(avg_traffic)})\n"
        
        if connected_devices > 0:
            user_stats += f"  • Устройств подключено: {connected_devices}\n"
        
        return user_stats
        
    except Exception as e:
        logger.error(f"Error getting enhanced user stats: {e}")
        return None

async def get_enhanced_node_stats():
    """Get enhanced node statistics"""
    try:
        nodes_response = await NodeAPI.get_all_nodes()
        if not nodes_response or 'response' not in nodes_response:
            return None
        
        nodes = nodes_response['response']
        nodes_count = len(nodes)
        
        if nodes_count == 0:
            return "🖥️ *Серверы*: 0\n"
        
        online_nodes = 0
        xray_running = 0
        disabled_nodes = 0
        
        for node in nodes:
            if node.get('isConnected'):
                online_nodes += 1
            if node.get('isXrayRunning'):
                xray_running += 1
            if node.get('isDisabled'):
                disabled_nodes += 1
        
        offline_nodes = nodes_count - online_nodes
        
        node_stats = f"🖥️ *Серверы* ({nodes_count} всего):\n"
        node_stats += f"  • 🟢 Онлайн: {online_nodes} | 🔴 Офлайн: {offline_nodes}\n"
        
        if xray_running != online_nodes:
            node_stats += f"  • ⚡ Xray запущен: {xray_running}/{online_nodes}\n"
        
        if disabled_nodes > 0:
            node_stats += f"  • ❌ Отключено: {disabled_nodes}\n"
        
        return node_stats
        
    except Exception as e:
        logger.error(f"Error getting enhanced node stats: {e}")
        return None

async def get_enhanced_traffic_stats():
    """Get enhanced real-time traffic statistics"""
    try:
        realtime_usage = await NodeAPI.get_nodes_realtime_usage()
        if not realtime_usage or len(realtime_usage) == 0:
            return None
        
        total_download_speed = 0
        total_upload_speed = 0
        total_download_bytes = 0
        total_upload_bytes = 0
        active_nodes = 0
        
        for node_data in realtime_usage:
            download_speed = node_data.get('downloadSpeedBps', 0)
            upload_speed = node_data.get('uploadSpeedBps', 0)
            
            total_download_speed += download_speed
            total_upload_speed += upload_speed
            total_download_bytes += node_data.get('downloadBytes', 0)
            total_upload_bytes += node_data.get('uploadBytes', 0)
            
            if download_speed > 0 or upload_speed > 0:
                active_nodes += 1
        
        total_speed = total_download_speed + total_upload_speed
        total_bytes = total_download_bytes + total_upload_bytes
        
        if total_speed == 0 and total_bytes == 0:
            return None
        
        traffic_stats = f"📊 *Трафик в реальном времени*:\n"
        
        if total_speed > 0:
            traffic_stats += f"  • 🚀 Общая скорость: {format_bytes(total_speed)}/с\n"
            traffic_stats += f"  • ⬇️ Скачивание: {format_bytes(total_download_speed)}/с\n"
            traffic_stats += f"  • ⬆️ Загрузка: {format_bytes(total_upload_speed)}/с\n"
            if active_nodes > 0:
                traffic_stats += f"  • 📡 Активных нод: {active_nodes}\n"
        
        if total_bytes > 0:
            traffic_stats += f"  • 📥 Скачано: {format_bytes(total_download_bytes)}\n"
            traffic_stats += f"  • 📤 Загружено: {format_bytes(total_upload_bytes)}\n"
        
        return traffic_stats
        
    except Exception as e:
        logger.warning(f"Could not get realtime traffic stats: {e}")
        return None

async def get_enhanced_server_stats():
    """Get enhanced server/inbound statistics"""
    try:
        inbounds_response = await InboundAPI.get_inbounds()
        if not inbounds_response or 'response' not in inbounds_response:
            return None
        
        inbounds = inbounds_response['response']
        inbounds_count = len(inbounds)
        
        if inbounds_count == 0:
            return "📡 *Inbound'ы*: 0\n"
        
        # Count by protocol/type
        protocols = {}
        total_users = 0
        
        for inbound in inbounds:
            protocol = inbound.get('type', 'unknown')
            protocols[protocol] = protocols.get(protocol, 0) + 1
            
            # Count users if available
            if 'users' in inbound:
                users_info = inbound['users']
                if isinstance(users_info, dict):
                    total_users += users_info.get('enabled', 0) + users_info.get('disabled', 0)
        
        server_stats = f"📡 *Inbound'ы* ({inbounds_count} всего):\n"
        
        # Protocol breakdown
        if protocols:
            protocol_list = []
            for protocol, count in protocols.items():
                protocol_list.append(f"{protocol}: {count}")
            server_stats += f"  • Протоколы: {' | '.join(protocol_list)}\n"
        
        if total_users > 0:
            server_stats += f"  • Связанных пользователей: {total_users}\n"
        
        return server_stats
        
    except Exception as e:
        logger.error(f"Error getting enhanced server stats: {e}")
        return None

async def get_basic_system_stats():
    """Get basic system statistics (lightweight fallback)"""
    try:
        stats_parts = []
        
        # Basic user count
        try:
            users_response = await UserAPI.get_all_users()
            if users_response and 'response' in users_response:
                users = users_response['response']
                users_count = len(users)
                active_users = sum(1 for user in users if user.get('status') == 'ACTIVE')
                stats_parts.append(f"👥 Пользователи: {active_users}/{users_count}")
        except:
            stats_parts.append(f"👥 Пользователи: N/A")
        
        # Basic node count
        try:
            nodes_response = await NodeAPI.get_all_nodes()
            if nodes_response and 'response' in nodes_response:
                nodes = nodes_response['response']
                nodes_count = len(nodes)
                online_nodes = sum(1 for node in nodes if node.get('isConnected'))
                stats_parts.append(f"🖥️ Серверы: {online_nodes}/{nodes_count}")
        except:
            stats_parts.append(f"🖥️ Серверы: N/A")
        
        # Basic inbound count
        try:
            inbounds_response = await InboundAPI.get_inbounds()
            if inbounds_response and 'response' in inbounds_response:
                inbounds = inbounds_response['response']
                inbounds_count = len(inbounds)
                stats_parts.append(f"📡 Inbound'ы: {inbounds_count}")
        except:
            stats_parts.append(f"📡 Inbound'ы: N/A")
        
        if stats_parts:
            return "📊 *Краткая статистика*:\n" + "\n".join(f"  • {part}" for part in stats_parts) + "\n"
        else:
            return "📊 *Статистика недоступна*\n"
        
    except Exception as e:
        logger.error(f"Error getting basic system stats: {e}")
        return "📊 *Ошибка получения статистики*\n"

# Utility function for other handlers
async def get_welcome_message():
    """Get welcome message for new users"""
    return (
        "🎉 *Добро пожаловать в RemnaWave Admin!*\n\n"
        "🚀 Этот бот предоставляет полный доступ к управлению вашей системой:\n\n"
        "• 👥 Управление пользователями\n"
        "• 🖥️ Мониторинг серверов\n"
        "• 📊 Детальная статистика\n"
        "• 🔧 Массовые операции\n"
        "• 🔍 Мощный поиск\n\n"
        "Используйте /start для доступа к главному меню."
    )

# Export all functions
__all__ = [
    'start',
    'show_main_menu',
    'get_enhanced_system_stats',
    'get_basic_system_stats',
    'get_welcome_message'
]