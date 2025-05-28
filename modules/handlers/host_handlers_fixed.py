from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import MAIN_MENU, HOST_MENU, EDIT_HOST, EDIT_HOST_FIELD, CREATE_HOST
from modules.api.hosts import HostAPI
from modules.api.inbounds import InboundAPI
from modules.utils.formatters import format_host_details
from modules.handlers.start_handler import show_main_menu

logger = logging.getLogger(__name__)

async def show_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show hosts menu"""
    keyboard = [
        [InlineKeyboardButton("📋 Список всех хостов", callback_data="list_hosts")],
        [InlineKeyboardButton("➕ Создать хост", callback_data="create_host")],
        [InlineKeyboardButton("🔍 Поиск хостов", callback_data="search_hosts")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🌐 *Управление хостами*\n\n"
    message += "Выберите действие:"

    # Проверяем callback_query
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
    
    return HOST_MENU

async def handle_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle hosts menu selection"""
    if not update.callback_query:
        return HOST_MENU
    
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "list_hosts":
        return await list_hosts(update, context)

    elif data == "create_host":
        return await start_create_host(update, context)

    elif data == "search_hosts":
        return await show_search_hosts_menu(update, context)

    elif data == "back_to_hosts":
        return await show_hosts_menu(update, context)

    elif data == "back_to_main":
        return await show_main_menu(update, context)
        
    elif data.startswith("view_host_"):
        uuid = data.split("_")[2]
        return await show_host_details(update, context, uuid)

    elif data.startswith("enable_host_"):
        uuid = data.split("_")[2]
        return await enable_host(update, context, uuid)

    elif data.startswith("disable_host_"):
        uuid = data.split("_")[2]
        return await disable_host(update, context, uuid)

    elif data.startswith("edit_host_"):
        uuid = data.split("_")[2]
        return await start_edit_host(update, context, uuid)

    elif data.startswith("delete_host_"):
        uuid = data.split("_")[2]
        return await confirm_delete_host(update, context, uuid)
    
    elif data.startswith("confirm_delete_"):
        uuid = data.split("_")[2]
        return await delete_host(update, context, uuid)

    return HOST_MENU

async def list_hosts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all hosts with improved response handling"""
    await update.callback_query.edit_message_text("🌐 Загрузка списка хостов...")

    try:
        response = await HostAPI.get_all_hosts()
        
        # Handle different response formats from API
        hosts = None
        if isinstance(response, dict):
            # Check if response is wrapped in 'response' field
            if 'response' in response:
                hosts = response['response']
                logger.debug("Found hosts data in 'response' field")
            # Check if it's a single host object
            elif 'uuid' in response or 'remark' in response:
                hosts = [response]
                logger.debug("Found single host in response")
        elif isinstance(response, list):
            hosts = response
            logger.debug("Found hosts as direct list")
        
        if not hosts:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Хосты не найдены или ошибка при получении списка.",
                reply_markup=reply_markup
            )
            return HOST_MENU

        logger.info(f"Successfully loaded {len(hosts)} hosts")

        message = f"🌐 *Хосты* ({len(hosts)}):\n\n"

        for i, host in enumerate(hosts):
            status_emoji = "🟢" if not host.get("isDisabled", False) else "🔴"
            
            message += f"{i+1}. {status_emoji} *{host.get('remark', 'Без названия')}*\n"
            message += f"   🌐 Адрес: {host.get('address', 'N/A')}:{host.get('port', 'N/A')}\n"
            
            inbound_uuid = host.get('inboundUuid', '')
            if inbound_uuid:
                message += f"   🔌 Inbound: {inbound_uuid[:8]}...\n"
            
            message += "\n"

        # Add action buttons
        keyboard = []
        
        for host in hosts:
            remark = host.get('remark', 'Без названия')
            if len(remark) > 20:
                remark = remark[:17] + "..."
            keyboard.append([
                InlineKeyboardButton(f"👁️ {remark}", callback_data=f"view_host_{host['uuid']}")
            ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        return HOST_MENU
        
    except Exception as e:
        logger.error(f"Error loading hosts list: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке списка хостов.",
            reply_markup=reply_markup
        )
        return HOST_MENU

async def show_host_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show host details with improved response handling"""
    try:
        response = await HostAPI.get_host_by_uuid(uuid)
        
        # Handle different response formats from API
        host = None
        if isinstance(response, dict):
            # Check if response is wrapped in 'response' field
            if 'response' in response:
                host = response['response']
                logger.debug("Found host data in 'response' field")
            # Check if response has host fields directly
            elif 'uuid' in response or 'remark' in response:
                host = response
                logger.debug("Found host data directly in response")
        
        if not host:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Хост не найден или ошибка при получении данных.",
                reply_markup=reply_markup
            )
            return HOST_MENU
        
        # Форматируем детали хоста
        message = f"🌐 *Детали хоста*\n\n"
        message += f"📝 Название: `{host.get('remark', 'Не указано')}`\n"
        message += f"🆔 UUID: `{host.get('uuid', 'N/A')}`\n"
        message += f"🌐 Адрес: `{host.get('address', 'N/A')}`\n"
        message += f"🔌 Порт: `{host.get('port', 'N/A')}`\n"
        
        # Статус
        status = "🟢 Включен" if not host.get("isDisabled", False) else "🔴 Отключен"
        message += f"📊 Статус: {status}\n"
        
        # Inbound UUID
        inbound_uuid = host.get('inboundUuid', '')
        if inbound_uuid:
            message += f"🔗 Inbound: `{inbound_uuid}`\n"
        
        # Дополнительные параметры
        if host.get('path'):
            message += f"🛣️ Путь: `{host['path']}`\n"
        if host.get('sni'):
            message += f"🔒 SNI: `{host['sni']}`\n"
        if host.get('host'):
            message += f"🏠 Host: `{host['host']}`\n"
        if host.get('alpn'):
            message += f"🔄 ALPN: `{host['alpn']}`\n"
        if host.get('fingerprint'):
            message += f"👆 Fingerprint: `{host['fingerprint']}`\n"
        if host.get('securityLayer'):
            message += f"🛡️ Security Layer: `{host['securityLayer']}`\n"
        
        allow_insecure = host.get('allowInsecure', False)
        message += f"🔐 Allow Insecure: `{'Да' if allow_insecure else 'Нет'}`\n"
        
        # Create action buttons
        keyboard = []
        
        if host.get("isDisabled", False):
            keyboard.append([InlineKeyboardButton("🟢 Включить", callback_data=f"enable_host_{uuid}")])
        else:
            keyboard.append([InlineKeyboardButton("🔴 Отключить", callback_data=f"disable_host_{uuid}")])
        
        keyboard.append([InlineKeyboardButton("📝 Редактировать", callback_data=f"edit_host_{uuid}")])
        keyboard.append([InlineKeyboardButton("❌ Удалить", callback_data=f"delete_host_{uuid}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data="list_hosts")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return HOST_MENU
        
    except Exception as e:
        logger.error(f"Error showing host details: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Произошла ошибка при загрузке деталей хоста.",
            reply_markup=reply_markup
        )
        return HOST_MENU

async def enable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Enable host"""
    try:
        result = await HostAPI.enable_host(uuid)
        
        if result:
            await update.callback_query.edit_message_text("✅ Хост успешно включен!")
            return await show_host_details(update, context, uuid)
        else:
            await update.callback_query.edit_message_text("❌ Не удалось включить хост.")
            return await show_host_details(update, context, uuid)
            
    except Exception as e:
        logger.error(f"Error enabling host: {e}")
        await update.callback_query.edit_message_text("❌ Произошла ошибка при включении хоста.")
        return HOST_MENU

async def disable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Disable host"""
    try:
        result = await HostAPI.disable_host(uuid)
        
        if result:
            await update.callback_query.edit_message_text("✅ Хост успешно отключен!")
            return await show_host_details(update, context, uuid)
        else:
            await update.callback_query.edit_message_text("❌ Не удалось отключить хост.")
            return await show_host_details(update, context, uuid)
            
    except Exception as e:
        logger.error(f"Error disabling host: {e}")
        await update.callback_query.edit_message_text("❌ Произошла ошибка при отключении хоста.")
        return HOST_MENU

async def confirm_delete_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Confirm host deletion"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{uuid}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"view_host_{uuid}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "⚠️ *Подтверждение удаления*\n\nВы уверены, что хотите удалить этот хост?\n\n❗ Это действие необратимо!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return HOST_MENU

async def delete_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Delete host"""
    try:
        result = await HostAPI.delete_host(uuid)
        
        if result:
            await update.callback_query.edit_message_text("✅ Хост успешно удален!")
            return await list_hosts(update, context)
        else:
            await update.callback_query.edit_message_text("❌ Не удалось удалить хост.")
            return await show_host_details(update, context, uuid)
            
    except Exception as e:
        logger.error(f"Error deleting host: {e}")
        await update.callback_query.edit_message_text("❌ Произошла ошибка при удалении хоста.")
        return HOST_MENU

async def show_search_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show search hosts menu"""
    keyboard = [
        [InlineKeyboardButton("🔍 По названию", callback_data="search_by_remark")],
        [InlineKeyboardButton("🌐 По адресу", callback_data="search_by_address")],
        [InlineKeyboardButton("🟢 Только включенные", callback_data="filter_enabled")],
        [InlineKeyboardButton("🔴 Только отключенные", callback_data="filter_disabled")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🔍 *Поиск и фильтрация хостов*\n\n"
    message += "Выберите тип поиска:"

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return HOST_MENU

async def start_create_host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start creating a new host"""
    await update.callback_query.edit_message_text("🔄 Подготовка к созданию хоста...")
    
    # Сначала получим список inbound'ов
    try:
        inbounds = await InboundAPI.get_all_inbounds()
        if not inbounds:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Не найдено доступных inbound'ов для создания хоста.",
                reply_markup=reply_markup
            )
            return HOST_MENU
        
        # Инициализируем данные создания хоста
        context.user_data["creating_host"] = {
            "inbounds": inbounds,
            "step": "select_inbound"
        }
        
        # Показываем список inbound'ов для выбора
        keyboard = []
        for inbound in inbounds:
            remark = inbound.get('remark', 'Без названия')
            if len(remark) > 25:
                remark = remark[:22] + "..."
            keyboard.append([
                InlineKeyboardButton(f"🔌 {remark}", callback_data=f"select_inbound_{inbound['uuid']}")
            ])
        
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="back_to_hosts")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "➕ *Создание нового хоста*\n\n"
        message += "🔌 Сначала выберите inbound для хоста:"
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return CREATE_HOST
        
    except Exception as e:
        logger.error(f"Error starting host creation: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Ошибка при подготовке к созданию хоста.",
            reply_markup=reply_markup
        )
        return HOST_MENU

async def start_edit_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Start editing a host"""
    try:
        # Get host details
        response = await HostAPI.get_host_by_uuid(uuid)
        
        # Handle different response formats from API
        host = None
        if isinstance(response, dict):
            # Check if response is wrapped in 'response' field
            if 'response' in response:
                host = response['response']
            # Check if response has host fields directly
            elif 'uuid' in response or 'remark' in response:
                host = response
        
        if not host:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Хост не найден.",
                reply_markup=reply_markup
            )
            return HOST_MENU
        
        # Store host data in context
        context.user_data["editing_host"] = host
        
        # Create edit menu
        keyboard = [
            [InlineKeyboardButton("📝 Название", callback_data=f"eh_r_{uuid}")],
            [InlineKeyboardButton("🌐 Адрес", callback_data=f"eh_a_{uuid}")],
            [InlineKeyboardButton("🔌 Порт", callback_data=f"eh_p_{uuid}")],
            [InlineKeyboardButton("🛣️ Путь", callback_data=f"eh_pt_{uuid}")],
            [InlineKeyboardButton("🔒 SNI", callback_data=f"eh_s_{uuid}")],
            [InlineKeyboardButton("🏠 Host", callback_data=f"eh_h_{uuid}")],
            [InlineKeyboardButton("🔄 ALPN", callback_data=f"eh_al_{uuid}")],
            [InlineKeyboardButton("👆 Fingerprint", callback_data=f"eh_f_{uuid}")],
            [InlineKeyboardButton("🔐 Allow Insecure", callback_data=f"eh_ai_{uuid}")],
            [InlineKeyboardButton("🛡️ Security Layer", callback_data=f"eh_sl_{uuid}")],
            [InlineKeyboardButton("🔙 Назад к деталям", callback_data=f"view_host_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"📝 *Редактирование хоста*\n\n"
        message += f"🌐 *Хост:* {host.get('remark', 'Без названия')}\n"
        message += f"🆔 *UUID:* `{uuid}`\n\n"
        message += f"*Текущие параметры:*\n"
        message += f"• Название: `{host.get('remark', 'Не установлено')}`\n"
        message += f"• Адрес: `{host.get('address', 'Не установлен')}`\n"
        message += f"• Порт: `{host.get('port', 'Не установлен')}`\n"
        message += f"• Путь: `{host.get('path', 'Не установлен')}`\n"
        message += f"• SNI: `{host.get('sni', 'Не установлен')}`\n"
        message += f"• Host: `{host.get('host', 'Не установлен')}`\n"
        message += f"• ALPN: `{host.get('alpn', 'Не установлен')}`\n"
        message += f"• Fingerprint: `{host.get('fingerprint', 'Не установлен')}`\n"
        message += f"• Allow Insecure: `{'Да' if host.get('allowInsecure') else 'Нет'}`\n"
        message += f"• Security Layer: `{host.get('securityLayer', 'DEFAULT')}`\n\n"
        message += "Выберите поле для редактирования:"
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return EDIT_HOST
        
    except Exception as e:
        logger.error(f"Error starting host edit: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Ошибка при загрузке данных хоста.",
            reply_markup=reply_markup
        )
        return HOST_MENU

# Export functions for conversation handler
__all__ = [
    'show_hosts_menu',
    'handle_hosts_menu', 
    'list_hosts',
    'show_host_details',
    'enable_host',
    'disable_host',
    'confirm_delete_host',
    'delete_host',
    'show_search_hosts_menu',
    'start_create_host',
    'start_edit_host'
]
