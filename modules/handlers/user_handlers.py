from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging

from modules.config import MAIN_MENU, USER_MENU, SELECTING_USER, WAITING_FOR_INPUT, CONFIRM_ACTION
from modules.utils.auth import check_authorization
from modules.utils.formatters import safe_edit_message
from modules.handlers.start_handler import show_main_menu

# Import all user sub-modules
from modules.handlers.users.user_list import list_users, handle_user_selection
from modules.handlers.users.user_details import show_user_details, handle_user_action
from modules.handlers.users.user_search import handle_search_input
from modules.handlers.users.user_edit import start_edit_user, handle_edit_field_selection, handle_edit_field_value
from modules.handlers.users.user_create import start_create_user, handle_create_user_input, finish_create_user
from modules.handlers.users.user_actions import handle_action_confirmation
from modules.handlers.users.user_delete import handle_delete_confirmation
from modules.handlers.users.user_hwid import handle_hwid_input
from modules.handlers.users.user_stats import show_user_stats

logger = logging.getLogger(__name__)

async def show_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show users menu with comprehensive options"""
    keyboard = [
        [
            InlineKeyboardButton("📋 Список пользователей", callback_data="list_users"),
            InlineKeyboardButton("➕ Создать", callback_data="create_user")
        ],
        [
            InlineKeyboardButton("🔍 Поиск по имени", callback_data="search_user"),
            InlineKeyboardButton("📱 Поиск по Telegram ID", callback_data="search_user_telegram")
        ],
        [
            InlineKeyboardButton("📝 Поиск по описанию", callback_data="search_user_description"),
            InlineKeyboardButton("🏷️ Поиск по тегу", callback_data="search_user_tag")
        ],
        [
            InlineKeyboardButton("📊 Статистика пользователей", callback_data="users_statistics"),
            InlineKeyboardButton("🔧 Массовые операции", callback_data="bulk_operations")
        ],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "👥 *Управление пользователями*\n\n"
    message += "🔍 *Доступные варианты поиска:*\n"
    message += "• По имени - частичное совпадение имени\n"
    message += "• По Telegram ID - точный поиск по ID\n"
    message += "• По описанию - поиск в описании\n"
    message += "• По тегу - поиск пользователей с тегом\n\n"
    message += "📊 *Дополнительно:*\n"
    message += "• Общая статистика всех пользователей\n"
    message += "• Массовые операции (включить/отключить/удалить)\n\n"
    message += "Выберите действие:"

    await safe_edit_message(update.callback_query, message, reply_markup, "Markdown")
    return USER_MENU

async def handle_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle users menu selection with all available options"""
    if not check_authorization(update.effective_user):
        await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    data = query.data

    # Basic operations
    if data == "list_users":
        return await list_users(update, context)
    elif data == "create_user":
        return await start_create_user(update, context)
    elif data == "back_to_main":
        return await show_main_menu(update, context)
    
    # Search operations
    elif data.startswith("search_user"):
        return await handle_search_setup(update, context, data)
    
    # Statistics and bulk operations
    elif data == "users_statistics":
        return await show_users_statistics(update, context)
    elif data == "bulk_operations":
        return await show_bulk_operations_menu(update, context)
    
    # Fallback to users menu
    return USER_MENU

async def handle_search_setup(update: Update, context: ContextTypes.DEFAULT_TYPE, search_type: str):
    """Setup search based on type with enhanced options"""
    search_messages = {
        "search_user": ("🔍 Введите часть имени пользователя для поиска:", "username"),
        "search_user_telegram": ("📱 Введите Telegram ID пользователя:", "telegram_id"),
        "search_user_description": ("📝 Введите ключевое слово для поиска в описании:", "description"),
        "search_user_tag": ("🏷️ Введите тег для поиска:", "tag")
    }
    
    message, search_field = search_messages.get(search_type, ("🔍 Введите поисковый запрос:", "username"))
    
    # Add search hints
    hints = {
        "username": "💡 Можно ввести часть имени (минимум 2 символа)",
        "telegram_id": "💡 Введите точный Telegram ID (только цифры)",
        "description": "💡 Поиск по ключевым словам в описании",
        "tag": "💡 Введите тег для поиска пользователей"
    }
    
    full_message = f"{message}\n\n{hints.get(search_field, '')}"
    
    # Add cancel button
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_users")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await safe_edit_message(update.callback_query, full_message, reply_markup, "Markdown")
    context.user_data["search_type"] = search_field
    return WAITING_FOR_INPUT

async def show_users_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show comprehensive users statistics"""
    try:
        from modules.api.users import UserAPI
        from modules.utils.formatters import format_bytes
        
        await update.callback_query.edit_message_text("📊 Загрузка статистики пользователей...")
        
        # Get all users for statistics
        users_response = await UserAPI.get_all_users()
        if not users_response or 'response' not in users_response:
            raise Exception("Не удалось получить список пользователей")
        
        users = users_response['response']
        
        if not users:
            message = "ℹ️ Пользователи не найдены."
        else:
            # Calculate statistics
            total_users = len(users)
            status_counts = {}
            total_traffic = 0
            device_usage = 0
            expired_count = 0
            
            for user in users:
                status = user.get('status', 'UNKNOWN')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Traffic statistics
                total_traffic += user.get('usedTraffic', 0)
                
                # Device statistics
                if user.get('hwidDeviceLimit', 0) > 0:
                    connected = user.get('hwidConnectedDevices', 0)
                    device_usage += connected
                
                # Expiration check
                if user.get('expireAt'):
                    try:
                        from datetime import datetime
                        expire_date = datetime.fromisoformat(user['expireAt'].replace('Z', '+00:00'))
                        if expire_date < datetime.now().astimezone():
                            expired_count += 1
                    except:
                        pass
            
            message = f"📊 *Статистика пользователей*\n\n"
            message += f"👥 *Общее количество:* `{total_users}`\n\n"
            
            # Status breakdown
            message += f"📈 *По статусам:*\n"
            status_emojis = {
                'ACTIVE': '🟢',
                'DISABLED': '🔴',
                'EXPIRED': '🟡',
                'LIMITED': '🟠'
            }
            
            for status, count in status_counts.items():
                emoji = status_emojis.get(status, '⚪')
                percentage = (count / total_users * 100) if total_users > 0 else 0
                message += f"• {emoji} {status}: `{count}` ({percentage:.1f}%)\n"
            
            # Traffic statistics
            message += f"\n📊 *Трафик:*\n"
            message += f"• Общее использование: `{format_bytes(total_traffic)}`\n"
            if total_users > 0:
                avg_traffic = total_traffic / total_users
                message += f"• Среднее на пользователя: `{format_bytes(avg_traffic)}`\n"
            
            # Device statistics
            if device_usage > 0:
                message += f"\n💻 *Устройства:*\n"
                message += f"• Всего подключенных: `{device_usage}`\n"
                if total_users > 0:
                    avg_devices = device_usage / total_users
                    message += f"• Среднее на пользователя: `{avg_devices:.1f}`\n"
            
            # Expiration statistics
            if expired_count > 0:
                message += f"\n⚠️ *Истечения:*\n"
                message += f"• Истекших подписок: `{expired_count}`\n"
                percentage = (expired_count / total_users * 100) if total_users > 0 else 0
                message += f"• Процент истекших: `{percentage:.1f}%`\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="users_statistics")],
            [InlineKeyboardButton("📊 Детальная статистика", callback_data="detailed_users_stats")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return USER_MENU
        
    except Exception as e:
        logger.error(f"Error showing users statistics: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке статистики: {str(e)}",
            reply_markup=reply_markup
        )
        return USER_MENU

async def show_bulk_operations_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bulk operations menu"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Массово включить", callback_data="bulk_enable_users"),
            InlineKeyboardButton("❌ Массово отключить", callback_data="bulk_disable_users")
        ],
        [
            InlineKeyboardButton("🔄 Массово сбросить трафик", callback_data="bulk_reset_traffic"),
            InlineKeyboardButton("📱 Массово сбросить устройства", callback_data="bulk_reset_devices")
        ],
        [
            InlineKeyboardButton("🗑️ Массово удалить", callback_data="bulk_delete_users"),
            InlineKeyboardButton("📅 Массово продлить", callback_data="bulk_extend_users")
        ],
        [
            InlineKeyboardButton("🔍 Фильтр по статусу", callback_data="filter_by_status"),
            InlineKeyboardButton("📊 Фильтр по трафику", callback_data="filter_by_traffic")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = "🔧 *Массовые операции с пользователями*\n\n"
    message += "⚠️ *Внимание!* Массовые операции влияют на множество пользователей одновременно.\n\n"
    message += "📋 *Доступные операции:*\n"
    message += "• Включить/отключить пользователей\n"
    message += "• Сбросить трафик или устройства\n"
    message += "• Удалить неактивных пользователей\n"
    message += "• Продлить срок действия\n\n"
    message += "🔍 *Фильтры помогают выбрать пользователей по критериям*\n\n"
    message += "Выберите операцию:"
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return USER_MENU

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text input with enhanced routing"""
    # Check different input types with proper routing
    if context.user_data.get("waiting_for") == "hwid":
        return await handle_hwid_input(update, context)
    elif context.user_data.get("waiting_for") == "delete_confirmation":
        return await handle_delete_confirmation(update, context)
    elif context.user_data.get("waiting_for") == "edit_field":
        return await handle_edit_field_value(update, context)
    elif context.user_data.get("search_type"):
        return await handle_search_input(update, context)
    elif "create_user_fields" in context.user_data:
        return await handle_create_user_input(update, context)
    elif context.user_data.get("bulk_operation"):
        from modules.handlers.bulk_handlers import handle_bulk_input
        return await handle_bulk_input(update, context)
    else:
        await update.message.reply_text(
            "❌ Неожиданный ввод текста. Используйте кнопки меню для навигации.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 В меню пользователей", callback_data="back_to_users")
            ]])
        )
        return await show_users_menu(update, context)

async def handle_back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back navigation from user operations"""
    query = update.callback_query
    if query:
        await query.answer()
        data = query.data
        
        if data == "back_to_users":
            return await show_users_menu(update, context)
        elif data == "back_to_main":
            return await show_main_menu(update, context)
    
    return USER_MENU

# Additional utility functions for user management

async def get_user_count_by_status(status: str = None):
    """Get count of users by status"""
    try:
        from modules.api.users import UserAPI
        
        users_response = await UserAPI.get_all_users()
        if not users_response or 'response' not in users_response:
            return 0
        
        users = users_response['response']
        
        if status:
            return len([u for u in users if u.get('status') == status])
        else:
            return len(users)
    except:
        return 0

async def format_user_summary(user: dict) -> str:
    """Format user summary for lists"""
    from modules.utils.formatters import format_bytes, escape_markdown
    
    status_emojis = {
        'ACTIVE': '🟢',
        'DISABLED': '🔴',
        'EXPIRED': '🟡',
        'LIMITED': '🟠'
    }
    
    status = user.get('status', 'UNKNOWN')
    emoji = status_emojis.get(status, '⚪')
    username = escape_markdown(user.get('username', 'N/A'))
    
    summary = f"{emoji} {username}"
    
    # Add traffic info if available
    used_traffic = user.get('usedTraffic', 0)
    if used_traffic > 0:
        summary += f" - {format_bytes(used_traffic)}"
    
    # Add device count if applicable
    devices = user.get('hwidConnectedDevices', 0)
    device_limit = user.get('hwidDeviceLimit', 0)
    if device_limit > 0:
        summary += f" - 📱{devices}/{device_limit}"
    
    return summary

async def validate_user_input(input_type: str, value: str) -> tuple[bool, str]:
    """Validate user input for various operations"""
    if input_type == "telegram_id":
        if not value.isdigit():
            return False, "Telegram ID должен содержать только цифры"
        if len(value) < 5 or len(value) > 15:
            return False, "Некорректная длина Telegram ID"
    
    elif input_type == "username":
        if len(value) < 2:
            return False, "Имя пользователя должно содержать минимум 2 символа"
        if len(value) > 50:
            return False, "Имя пользователя слишком длинное"
    
    elif input_type == "description":
        if len(value) < 1:
            return False, "Описание не может быть пустым"
        if len(value) > 200:
            return False, "Описание слишком длинное (максимум 200 символов)"
    
    elif input_type == "tag":
        if len(value) < 1:
            return False, "Тег не может быть пустым"
        if len(value) > 20:
            return False, "Тег слишком длинный (максимум 20 символов)"
    
    return True, "OK"

# Export functions for use in conversation handler
__all__ = [
    'show_users_menu',
    'handle_users_menu', 
    'handle_text_input',
    'handle_search_setup',
    'show_users_statistics',
    'show_bulk_operations_menu',
    'handle_back_navigation',
    'get_user_count_by_status',
    'format_user_summary',
    'validate_user_input'
]