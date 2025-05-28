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
    """List all hosts"""
    await update.callback_query.edit_message_text("🌐 Загрузка списка хостов...")

    response = await HostAPI.get_all_hosts()
    
    if not response or 'response' not in response:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Хосты не найдены или ошибка при получении списка.",
            reply_markup=reply_markup
        )
        return HOST_MENU

    hosts = response['response']
    
    if not hosts:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "ℹ️ Список хостов пуст.",
            reply_markup=reply_markup
        )
        return HOST_MENU

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

async def show_host_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Show host details"""
    response = await HostAPI.get_host_by_uuid(uuid)
    
    if not response or 'response' not in response:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Хост не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return HOST_MENU
    
    host = response['response']
    
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

async def enable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Enable host"""
    await update.callback_query.answer()
    
    result = await HostAPI.enable_host(uuid)
    
    if result:
        await update.callback_query.edit_message_text("🟢 Хост успешно включен.")
        # Показать обновленные детали
        await show_host_details(update, context, uuid)
    else:
        await update.callback_query.edit_message_text("❌ Не удалось включить хост.")
    
    return HOST_MENU

async def disable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Disable host"""
    await update.callback_query.answer()
    
    result = await HostAPI.disable_host(uuid)
    
    if result:
        await update.callback_query.edit_message_text("🔴 Хост успешно отключен.")
        # Показать обновленные детали
        await show_host_details(update, context, uuid)
    else:
        await update.callback_query.edit_message_text("❌ Не удалось отключить хост.")
    
    return HOST_MENU

async def confirm_delete_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Confirm host deletion"""
    response = await HostAPI.get_host_by_uuid(uuid)
    
    if not response or 'response' not in response:
        await update.callback_query.edit_message_text("❌ Хост не найден.")
        return HOST_MENU
    
    host = response['response']
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{uuid}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"view_host_{uuid}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"⚠️ *Подтверждение удаления*\n\n"
    message += f"Вы действительно хотите удалить хост:\n"
    message += f"📝 Название: `{host.get('remark', 'Без названия')}`\n"
    message += f"🌐 Адрес: `{host.get('address')}:{host.get('port')}`\n\n"
    message += f"❗ Это действие необратимо!"
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return HOST_MENU

async def delete_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Delete host"""
    await update.callback_query.answer()
    
    result = await HostAPI.delete_host(uuid)
    
    keyboard = [[InlineKeyboardButton("🔙 К списку хостов", callback_data="list_hosts")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if result:
        await update.callback_query.edit_message_text(
            "✅ Хост успешно удален.",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ Не удалось удалить хост.",
            reply_markup=reply_markup
        )
    
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
    # Сначала получим список inbound'ов
    inbounds_response = await InboundAPI.get_all_inbounds()
    
    if not inbounds_response or 'response' not in inbounds_response:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Не удалось получить список inbound'ов. Создание хоста невозможно.",
            reply_markup=reply_markup
        )
        return HOST_MENU
    
    inbounds = inbounds_response['response']
    
    if not inbounds:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Нет доступных inbound'ов. Сначала создайте inbound.",
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
    
    message = f"➕ *Создание нового хоста*\n\n"
    message += f"Шаг 1/4: Выберите inbound для хоста:\n\n"
    
    for i, inbound in enumerate(inbounds, 1):
        message += f"{i}. **{inbound.get('remark', 'Без названия')}**\n"
        message += f"   UUID: `{inbound['uuid']}`\n"
        message += f"   Тип: {inbound.get('type', 'N/A')}\n\n"
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return CREATE_HOST

# Дальше добавьте остальные функции для редактирования и создания хостов
# ... (остальная часть файла аналогична предыдущей версии, но с использованием актуальных методов API)

async def start_edit_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Start editing a host"""
    try:
        # Get host details
        response = await HostAPI.get_host_by_uuid(uuid)
        if not response or 'response' not in response:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Хост не найден.",
                reply_markup=reply_markup
            )
            return HOST_MENU
        
        host = response['response']
        
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
        
        message = f"📝 *Редактирование хоста: {host.get('remark', 'Без названия')}*\n\n"
        message += f"📌 Текущие значения:\n"
        message += f"• Название: `{host.get('remark', 'Не указано')}`\n"
        message += f"• Адрес: `{host.get('address', 'Не указан')}`\n"
        message += f"• Порт: `{host.get('port', 'Не указан')}`\n"
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

async def handle_host_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle host edit menu selection"""
    if not update.callback_query:
        return EDIT_HOST
        
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("eh_"):
        parts = data.split("_")
        field_code = parts[1]  # r, a, p, etc.
        uuid = parts[2]
        
        # Map short codes to field names
        field_map = {
            "r": "remark",
            "a": "address", 
            "p": "port",
            "pt": "path",
            "s": "sni",
            "h": "host",
            "al": "alpn",
            "f": "fingerprint",
            "ai": "allowInsecure",
            "sl": "securityLayer"
        }
        
        field = field_map.get(field_code)
        if field:
            return await start_edit_host_field(update, context, uuid, field)
    
    elif data.startswith("view_host_"):
        uuid = data.split("_")[2]
        return await show_host_details(update, context, uuid)
    
    return EDIT_HOST

async def start_edit_host_field(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str, field: str):
    """Start editing a specific host field"""
    try:
        host = context.user_data.get("editing_host")
        if not host:
            # Fallback: get host from API
            response = await HostAPI.get_host_by_uuid(uuid)
            if not response or 'response' not in response:
                await update.callback_query.edit_message_text("❌ Ошибка: данные хоста не найдены.")
                return EDIT_HOST
            host = response['response']
            context.user_data["editing_host"] = host
        
        # Store field being edited
        context.user_data["editing_field"] = field
        
        # Get current value and field info
        field_info = {
            "remark": {
                "title": "Название хоста",
                "current": host.get("remark", ""),
                "example": "Например: Main-Host",
                "validation": "текст (максимум 40 символов)"
            },
            "address": {
                "title": "Адрес хоста",
                "current": host.get("address", ""),
                "example": "Например: 192.168.1.1 или example.com",
                "validation": "IP адрес или домен"
            },
            "port": {
                "title": "Порт хоста",
                "current": str(host.get("port", "")),
                "example": "Например: 443",
                "validation": "число от 1 до 65535"
            },
            "path": {
                "title": "Путь",
                "current": host.get("path", ""),
                "example": "Например: /api/v1",
                "validation": "путь (может быть пустым)"
            },
            "sni": {
                "title": "SNI (Server Name Indication)",
                "current": host.get("sni", ""),
                "example": "Например: example.com",
                "validation": "доменное имя (может быть пустым)"
            },
            "host": {
                "title": "Host заголовок",
                "current": host.get("host", ""),
                "example": "Например: api.example.com",
                "validation": "доменное имя (может быть пустым)"
            },
            "alpn": {
                "title": "ALPN протокол",
                "current": host.get("alpn", ""),
                "example": "h3, h2, http/1.1, h2,http/1.1, h3,h2,http/1.1, h3,h2",
                "validation": "один из поддерживаемых протоколов"
            },
            "fingerprint": {
                "title": "TLS Fingerprint",
                "current": host.get("fingerprint", ""),
                "example": "chrome, firefox, safari, ios, android, edge, qq, random, randomized",
                "validation": "один из поддерживаемых fingerprint'ов"
            },
            "allowInsecure": {
                "title": "Разрешить небезопасные соединения",
                "current": "Да" if host.get("allowInsecure") else "Нет",
                "example": "Введите: да/нет, true/false, 1/0",
                "validation": "логическое значение"
            },
            "securityLayer": {
                "title": "Уровень безопасности",
                "current": host.get("securityLayer", "DEFAULT"),
                "example": "DEFAULT, TLS, NONE",
                "validation": "один из поддерживаемых уровней"
            }
        }
        
        if field not in field_info:
            await update.callback_query.edit_message_text("❌ Неизвестное поле для редактирования.")
            return EDIT_HOST
        
        info = field_info[field]
        
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data=f"ceh_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"📝 *Редактирование: {info['title']}*\n\n"
        message += f"📌 Текущее значение: `{info['current']}`\n\n"
        message += f"💡 {info['example']}\n"
        message += f"✅ Формат: {info['validation']}\n\n"
        message += f"✍️ Введите новое значение:"
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return EDIT_HOST_FIELD
        
    except Exception as e:
        logger.error(f"Error starting field edit: {e}")
        await update.callback_query.edit_message_text("❌ Ошибка при подготовке редактирования.")
        return EDIT_HOST

async def handle_host_field_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle input for host field editing"""
    try:
        host = context.user_data.get("editing_host")
        field = context.user_data.get("editing_field")
        
        if not host or not field:
            await update.message.reply_text("❌ Ошибка: данные редактирования потеряны.")
            return EDIT_HOST
        
        user_input = update.message.text.strip()
        uuid = host["uuid"]
        
        # Validate input using the API validation method
        update_data = {field: user_input if user_input else ""}
        
        # Special handling for different field types
        if field == "port":
            try:
                update_data[field] = int(user_input)
            except ValueError:
                keyboard = [
                    [InlineKeyboardButton("❌ Отмена", callback_data=f"ceh_{uuid}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "❌ Порт должен быть числом.\n\nПопробуйте еще раз:",
                    reply_markup=reply_markup
                )
                return EDIT_HOST_FIELD
        
        elif field == "allowInsecure":
            lower_input = user_input.lower()
            if lower_input in ["да", "yes", "true", "1"]:
                update_data[field] = True
            elif lower_input in ["нет", "no", "false", "0"]:
                update_data[field] = False
            else:
                keyboard = [
                    [InlineKeyboardButton("❌ Отмена", callback_data=f"ceh_{uuid}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "❌ Введите: да/нет, true/false, 1/0\n\nПопробуйте еще раз:",
                    reply_markup=reply_markup
                )
                return EDIT_HOST_FIELD
        
        # Validate data using API validation
        is_valid, error_message = HostAPI.validate_host_data({**host, **update_data})
        
        if not is_valid:
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data=f"ceh_{uuid}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ {error_message}\n\nПопробуйте еще раз:",
                reply_markup=reply_markup
            )
            return EDIT_HOST_FIELD
        
        # Update host via API - добавляем UUID к данным обновления
        update_data['uuid'] = uuid
        result = await HostAPI.update_host(update_data)
        
        if result:
            # Update stored host data
            host[field] = update_data[field]
            context.user_data["editing_host"] = host
            
            # Clear editing state
            context.user_data.pop("editing_field", None)
            
            keyboard = [
                [InlineKeyboardButton("✅ Продолжить редактирование", callback_data=f"edit_host_{uuid}")],
                [InlineKeyboardButton("📋 Показать детали", callback_data=f"view_host_{uuid}")],
                [InlineKeyboardButton("🔙 К списку хостов", callback_data="list_hosts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Поле '{field}' успешно обновлено!",
                reply_markup=reply_markup
            )
            
            return HOST_MENU
        else:
            # Map field names to short codes
            field_to_code = {
                "remark": "r",
                "address": "a",
                "port": "p", 
                "path": "pt",
                "sni": "s",
                "host": "h",
                "alpn": "al",
                "fingerprint": "f",
                "allowInsecure": "ai",
                "securityLayer": "sl"
            }
            
            field_code = field_to_code.get(field, field)
            
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"eh_{field_code}_{uuid}")],
                [InlineKeyboardButton("❌ Отмена", callback_data=f"ceh_{uuid}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Ошибка при обновлении хоста. Проверьте данные и попробуйте снова.",
                reply_markup=reply_markup
            )
            return EDIT_HOST_FIELD
            
    except Exception as e:
        logger.error(f"Error handling host field input: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке ввода.")
        return EDIT_HOST

async def handle_cancel_host_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle canceling host edit"""
    if not update.callback_query:
        return HOST_MENU
        
    query = update.callback_query
    await query.answer()
    
    # Clear editing state
    context.user_data.pop("editing_host", None)
    context.user_data.pop("editing_field", None)
    
    if query.data.startswith("ceh_"):
        uuid = query.data.split("_")[1]
        return await show_host_details(update, context, uuid)
    else:
        return await show_hosts_menu(update, context)