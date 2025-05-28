from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging

from modules.config import (
    MAIN_MENU, USER_MENU, NODE_MENU, STATS_MENU, HOST_MENU, INBOUND_MENU, 
    BULK_MENU, CREATE_USER, CREATE_USER_FIELD, SELECTING_USER, WAITING_FOR_INPUT,
    SEARCH_USERS, SEARCH_NODES, SEARCH_HOSTS, SEARCH_INBOUNDS
)
from modules.utils.auth import check_authorization
from modules.utils.formatters import safe_edit_message

# Import handlers
from modules.handlers.user_handlers import show_users_menu
from modules.handlers.users.user_create import start_create_user
from modules.handlers.users.user_details import show_user_details
from modules.handlers.node_handlers import show_nodes_menu
from modules.handlers.stats_handlers import show_stats_menu
from modules.handlers.host_handlers import show_hosts_menu
from modules.handlers.inbound_handlers import show_inbounds_menu
from modules.handlers.bulk_handlers import show_bulk_menu
from modules.handlers.start_handler import show_main_menu

logger = logging.getLogger(__name__)

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selection with comprehensive routing"""
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        # Main menu sections
        if data in ["users", "menu_users"]:
            return await show_users_menu(update, context)

        elif data in ["nodes", "menu_nodes"]:
            return await show_nodes_menu(update, context)

        elif data in ["stats", "menu_stats"]:
            return await show_stats_menu(update, context)

        elif data in ["hosts", "menu_hosts"]:
            return await show_hosts_menu(update, context)

        elif data in ["inbounds", "menu_inbounds"]:
            return await show_inbounds_menu(update, context)

        elif data in ["bulk", "menu_bulk"]:
            return await show_bulk_menu(update, context)

        # User operations
        elif data in ["create_user", "menu_create_user"]:
            return await start_create_user(update, context)

        elif data.startswith("view_"):
            uuid = data.split("_", 1)[1]
            return await show_user_details(update, context, uuid)

        # Quick actions from main menu
        elif data == "quick_user_stats":
            return await show_quick_user_stats(update, context)

        elif data == "quick_system_info":
            return await show_quick_system_info(update, context)

        elif data == "quick_recent_users":
            return await show_quick_recent_users(update, context)

        # Search shortcuts
        elif data == "search_users_quick":
            return await setup_quick_search(update, context, "users")

        elif data == "search_nodes_quick":
            return await setup_quick_search(update, context, "nodes")

        # Navigation
        elif data == "back_to_main":
            return await show_main_menu(update, context)

        elif data == "refresh_main":
            return await refresh_main_menu(update, context)

        # Settings and configuration
        elif data == "bot_settings":
            return await show_bot_settings(update, context)

        elif data == "admin_tools":
            return await show_admin_tools(update, context)

        # Help and information
        elif data == "help":
            return await show_help_menu(update, context)

        elif data == "about":
            return await show_about_info(update, context)

        # Default fallback
        else:
            logger.warning(f"Unknown menu selection: {data}")
            return await show_main_menu(update, context)

    except Exception as e:
        logger.error(f"Error in menu selection for {data}: {e}")
        await query.answer("❌ Произошла ошибка при обработке запроса", show_alert=True)
        return await show_main_menu(update, context)

async def show_quick_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show quick user statistics overlay"""
    try:
        from modules.api.users import UserAPI
        from modules.utils.formatters import format_bytes
        
        await update.callback_query.edit_message_text("📊 Загрузка статистики...")
        
        users_response = await UserAPI.get_all_users()
        if not users_response or 'response' not in users_response:
            raise Exception("Не удалось получить данные пользователей")
        
        users = users_response['response']
        
        # Quick stats
        total_users = len(users)
        active_users = len([u for u in users if u.get('status') == 'ACTIVE'])
        total_traffic = sum(u.get('usedTraffic', 0) for u in users)
        
        message = f"⚡ *Быстрая статистика*\n\n"
        message += f"👥 Всего пользователей: `{total_users}`\n"
        message += f"🟢 Активных: `{active_users}`\n"
        message += f"📊 Общий трафик: `{format_bytes(total_traffic)}`\n"
        
        if total_users > 0:
            avg_traffic = total_traffic / total_users
            message += f"📈 Средний трафик: `{format_bytes(avg_traffic)}`"
        
        keyboard = [
            [InlineKeyboardButton("📊 Подробная статистика", callback_data="menu_stats")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"Error showing quick user stats: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при загрузке статистики",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]])
        )
        return MAIN_MENU

async def show_quick_system_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show quick system information"""
    try:
        from modules.api.system import SystemAPI
        from modules.utils.formatters import format_bytes
        
        await update.callback_query.edit_message_text("🖥️ Загрузка системной информации...")
        
        stats_response = await SystemAPI.get_system_stats()
        if not stats_response or 'response' not in stats_response:
            raise Exception("Не удалось получить системную информацию")
        
        stats = stats_response['response']
        
        message = f"🖥️ *Системная информация*\n\n"
        
        # System info
        if 'system' in stats:
            sys_info = stats['system']
            message += f"💻 ОС: `{sys_info.get('os', 'N/A')}`\n"
            message += f"🏗️ Архитектура: `{sys_info.get('arch', 'N/A')}`\n"
        
        # Memory info
        if 'memory' in stats:
            mem = stats['memory']
            total_gb = mem.get('total', 0) / (1024**3)
            used_gb = mem.get('used', 0) / (1024**3)
            usage_percent = (mem.get('used', 0) / mem.get('total', 1)) * 100
            
            message += f"💾 Память: `{used_gb:.1f}/{total_gb:.1f} GB ({usage_percent:.1f}%)`\n"
        
        # CPU info
        if 'cpu' in stats:
            cpu = stats['cpu']
            message += f"⚡ CPU: `{cpu.get('usage', 0):.1f}%`\n"
        
        # Uptime
        if 'uptime' in stats:
            uptime_seconds = stats['uptime']
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            message += f"⏱️ Uptime: `{days}д {hours}ч`"
        
        keyboard = [
            [InlineKeyboardButton("📊 Полная статистика", callback_data="menu_stats")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"Error showing system info: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при загрузке системной информации",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]])
        )
        return MAIN_MENU

async def show_quick_recent_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recently created or active users"""
    try:
        from modules.api.users import UserAPI
        from datetime import datetime, timedelta
        
        await update.callback_query.edit_message_text("👥 Загрузка последних пользователей...")
        
        users_response = await UserAPI.get_all_users()
        if not users_response or 'response' not in users_response:
            raise Exception("Не удалось получить данные пользователей")
        
        users = users_response['response']
        
        # Sort by creation date (newest first)
        sorted_users = sorted(users, key=lambda x: x.get('createdAt', ''), reverse=True)
        recent_users = sorted_users[:5]  # Last 5 users
        
        message = f"👥 *Последние пользователи*\n\n"
        
        if not recent_users:
            message += "ℹ️ Пользователи не найдены"
        else:
            for i, user in enumerate(recent_users, 1):
                status_emoji = {
                    'ACTIVE': '🟢',
                    'DISABLED': '🔴',
                    'EXPIRED': '🟡',
                    'LIMITED': '🟠'
                }.get(user.get('status'), '⚪')
                
                username = user.get('username', 'N/A')[:20]
                created_date = user.get('createdAt', '')[:10]
                
                message += f"{i}. {status_emoji} `{username}` - {created_date}\n"
        
        keyboard = [
            [InlineKeyboardButton("👥 Все пользователи", callback_data="menu_users")],
            [InlineKeyboardButton("➕ Создать пользователя", callback_data="create_user")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return MAIN_MENU
        
    except Exception as e:
        logger.error(f"Error showing recent users: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при загрузке пользователей",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]])
        )
        return MAIN_MENU

async def setup_quick_search(update: Update, context: ContextTypes.DEFAULT_TYPE, search_type: str):
    """Setup quick search for different object types"""
    search_configs = {
        "users": {
            "title": "👥 Быстрый поиск пользователей",
            "prompt": "🔍 Введите имя пользователя или Telegram ID:",
            "hint": "💡 Можно ввести часть имени или точный ID",
            "state": SEARCH_USERS
        },
        "nodes": {
            "title": "🖥️ Быстрый поиск серверов",
            "prompt": "🔍 Введите название или адрес сервера:",
            "hint": "💡 Можно ввести часть названия или IP адрес",
            "state": SEARCH_NODES
        }
    }
    
    config = search_configs.get(search_type)
    if not config:
        return await show_main_menu(update, context)
    
    message = f"{config['title']}\n\n{config['prompt']}\n\n{config['hint']}"
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup
    )
    
    context.user_data["quick_search_type"] = search_type
    return config["state"]

async def refresh_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Refresh main menu with updated data"""
    # Clear any cached data
    context.user_data.clear()
    
    await update.callback_query.edit_message_text("🔄 Обновление...")
    return await show_main_menu(update, context)

async def show_bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot settings and configuration"""
    from modules.config import ADMIN_USER_IDS, API_BASE_URL
    
    message = f"⚙️ *Настройки бота*\n\n"
    message += f"🔧 API URL: `{API_BASE_URL}`\n"
    message += f"👥 Админов: `{len(ADMIN_USER_IDS)}`\n"
    message += f"🤖 Версия: `1.6.5`\n\n"
    message += "Здесь будут настройки бота (в разработке)"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Перезагрузить конфиг", callback_data="reload_config")],
        [InlineKeyboardButton("📊 Логи бота", callback_data="show_bot_logs")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return MAIN_MENU

async def show_admin_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show administrative tools"""
    message = f"🛠️ *Инструменты администратора*\n\n"
    message += "Специальные инструменты для администрирования системы"
    
    keyboard = [
        [
            InlineKeyboardButton("🗃️ Бекап данных", callback_data="backup_data"),
            InlineKeyboardButton("🔄 Синхронизация", callback_data="sync_data")
        ],
        [
            InlineKeyboardButton("🔍 Диагностика", callback_data="run_diagnostics"),
            InlineKeyboardButton("🧹 Очистка", callback_data="cleanup_data")
        ],
        [
            InlineKeyboardButton("📊 Системная статистика", callback_data="detailed_system_stats"),
            InlineKeyboardButton("⚡ Производительность", callback_data="performance_stats")
        ],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return MAIN_MENU

async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help and documentation"""
    message = f"📚 *Справка по боту*\n\n"
    message += "🎯 *Основные разделы:*\n"
    message += "• 👥 Пользователи - управление учетными записями\n"
    message += "• 🖥️ Серверы - управление нодами\n"
    message += "• 🌐 Хосты - настройка подключений\n"
    message += "• 📡 Inbound'ы - входящие соединения\n"
    message += "• 📊 Статистика - аналитика и отчеты\n\n"
    message += "🔍 *Поиск работает по частичному совпадению*\n"
    message += "🔧 *Массовые операции доступны для пользователей*\n"
    message += "⚡ *Быстрые действия через главное меню*"
    
    keyboard = [
        [InlineKeyboardButton("📖 Документация API", callback_data="api_docs")],
        [InlineKeyboardButton("🎥 Видео-гайд", callback_data="video_guide")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return MAIN_MENU

async def show_about_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show about information"""
    message = f"ℹ️ *О боте*\n\n"
    message += f"🤖 **RemnaWave Admin Bot**\n"
    message += f"📦 Версия: `1.6.5`\n"
    message += f"🔧 API версия: `v1.6.5`\n"
    message += f"🐍 Python: `3.9+`\n"
    message += f"📡 python-telegram-bot: `20.x`\n\n"
    message += f"📋 *Возможности:*\n"
    message += f"• Полное управление пользователями\n"
    message += f"• Управление серверами и нодами\n"
    message += f"• Настройка хостов и inbound'ов\n"
    message += f"• Подробная статистика\n"
    message += f"• Массовые операции\n"
    message += f"• Поиск и фильтрация\n\n"
    message += f"💼 Создано для администрирования RemnaWave"
    
    keyboard = [
        [InlineKeyboardButton("🐛 Сообщить об ошибке", callback_data="report_bug")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return MAIN_MENU

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu with authorization check and cleanup"""
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END
    
    # Очищаем временные данные
    temp_keys = ['search_type', 'editing_user', 'editing_field', 'create_user', 'bulk_operation']
    for key in temp_keys:
        context.user_data.pop(key, None)
    
    # Показываем главное меню
    return await show_main_menu(update, context)

# Export all functions for use in other modules
__all__ = [
    'handle_menu_selection',
    'back_to_main_menu',
    'show_quick_user_stats',
    'show_quick_system_info',
    'show_quick_recent_users',
    'setup_quick_search',
    'refresh_main_menu',
    'show_bot_settings',
    'show_admin_tools',
    'show_help_menu',
    'show_about_info'
]