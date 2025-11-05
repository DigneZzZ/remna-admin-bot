from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import MAIN_MENU, HOST_MENU, EDIT_HOST, EDIT_HOST_FIELD, HOST_PROFILE, HOST_INBOUND, HOST_PARAMS
from modules.api.config_profiles import ConfigProfileAPI
from modules.api.hosts import HostAPI
from modules.utils.formatters import format_host_details
from modules.handlers.core.start import show_main_menu

logger = logging.getLogger(__name__)

async def show_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show hosts menu"""
    keyboard = [
        [InlineKeyboardButton("📋 Список всех хостов", callback_data="list_hosts")],
        [InlineKeyboardButton("➕ Создать хост", callback_data="create_host")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🌐 *Управление хостами*\n\n"
    message += "Выберите действие:"

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle hosts menu selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "list_hosts":
        await list_hosts(update, context)

    elif data == "create_host":
        return await start_create_host(update, context)
    
    elif data.startswith("create_host_profile_"):
        profile_uuid = data.split("_")[-1]
        ch = context.user_data.get("create_host", {})
        ch["configProfileUuid"] = profile_uuid
        context.user_data["create_host"] = ch
        return await choose_host_inbound(update, context)
    
    elif data.startswith("create_host_inbound_"):
        inbound_uuid = data.split("_")[-1]
        ch = context.user_data.get("create_host", {})
        ch["configProfileInboundUuid"] = inbound_uuid
        context.user_data["create_host"] = ch
        return await input_host_params(update, context)

    elif data == "back_to_hosts":
        await show_hosts_menu(update, context)
        return HOST_MENU

    elif data == "back_to_main":
        await show_main_menu(update, context)
        return MAIN_MENU
        
    elif data.startswith("view_host_"):
        uuid = data.split("_")[2]
        await show_host_details(update, context, uuid)

    elif data.startswith("enable_host_"):
        uuid = data.split("_")[2]
        await enable_host(update, context, uuid)
        return HOST_MENU

    elif data.startswith("disable_host_"):
        uuid = data.split("_")[2]
        await disable_host(update, context, uuid)
        return HOST_MENU

    elif data.startswith("edit_host_"):
        uuid = data.split("_")[2]
        await start_edit_host(update, context, uuid)
        return EDIT_HOST

    elif data.startswith("delete_host_"):
        uuid = data.split("_")[2]
        # Ask confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_host_{uuid}"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"view_host_{uuid}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "⚠️ Вы уверены, что хотите удалить этот хост?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return HOST_MENU

    elif data.startswith("confirm_delete_host_"):
        uuid = data.split("_")[3]
        try:
            result = await HostAPI.delete_host(uuid)
            if result:
                message = "✅ Хост успешно удалён."
            else:
                message = "❌ Не удалось удалить хост."
        except Exception:
            message = "❌ Ошибка при удалении хоста."
        keyboard = [[InlineKeyboardButton("🔙 К списку хостов", callback_data="list_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return HOST_MENU

    return HOST_PROFILE
async def start_create_host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start host creation wizard: choose config profile"""
    query = update.callback_query
    await query.answer()
    profiles = await ConfigProfileAPI.get_profiles()
    if not profiles:
        await query.edit_message_text("❌ Не удалось получить список профилей.")
        return HOST_MENU
    keyboard = []
    for p in profiles[:10]:
        name = p.get("name", p.get("uuid", "Profile"))
        keyboard.append([InlineKeyboardButton(name, callback_data=f"create_host_profile_{p.get('uuid')}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data["create_host"] = {}
    await query.edit_message_text(
        text="🆕 Создание хоста\n\nШаг 1/3: выберите профиль конфигурации:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return HOST_INBOUND

async def choose_host_inbound(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2 - choose inbound from selected profile"""
    query = update.callback_query
    ch = context.user_data.get("create_host", {})
    profile_uuid = ch.get("configProfileUuid")
    if not profile_uuid:
        return await start_create_host(update, context)
    inbounds = await ConfigProfileAPI.get_profile_inbounds(profile_uuid)
    if not inbounds:
        await query.edit_message_text("❌ В профиле нет inbound'ов.")
        return HOST_MENU
    keyboard = []
    for inbound in inbounds[:10]:
        name = f"{inbound.get('tag')} ({inbound.get('type')} :{inbound.get('port')})"
        keyboard.append([InlineKeyboardButton(name, callback_data=f"create_host_inbound_{inbound.get('uuid')}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="create_host")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="🆕 Создание хоста\n\nШаг 2/3: выберите inbound из профиля:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return HOST_PARAMS

async def input_host_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3 - ask for host params (remark, address, port)"""
    query = update.callback_query
    await query.edit_message_text(
        text=(
            "🆕 Создание хоста\n\nШаг 3/3: введите параметры в одной строке через пробел:\n"
            "remark address port\n\n"
            "Например: MainHost example.com 443\n\n"
            "После этого я попрошу SNI (можно пропустить)."
        ),
        parse_mode="Markdown"
    )
    context.user_data["host_create_wait_input"] = True
    return HOST_PARAMS

async def handle_host_creation_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for host creation params (remark/address/port then SNI)"""
    text = (update.message.text or "").strip()

    if context.user_data.get("host_create_wait_input"):
        parts = text.split()
        if len(parts) < 3:
            await update.message.reply_text("❌ Формат: remark address port. Пример: MainHost example.com 443")
            return HOST_PARAMS
        remark, address, port_str = parts[0], parts[1], parts[2]
        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                raise ValueError()
        except Exception:
            await update.message.reply_text("❌ Порт должен быть числом 1-65535")
            return HOST_PARAMS

        ch = context.user_data.get("create_host", {})
        ch.update({"remark": remark, "address": address, "port": port})
        context.user_data["create_host"] = ch
        context.user_data.pop("host_create_wait_input", None)
        context.user_data["host_create_wait_sni"] = True
        await update.message.reply_text("🔒 Введите SNI (или '-' чтобы пропустить):")
        return HOST_PARAMS

    if context.user_data.get("host_create_wait_sni"):
        sni = None if text in ("", "-") else text
        ch = context.user_data.get("create_host", {})
        payload = {
            "inbound": {
                "configProfileUuid": ch.get("configProfileUuid"),
                "configProfileInboundUuid": ch.get("configProfileInboundUuid")
            },
            "remark": ch.get("remark"),
            "address": ch.get("address"),
            "port": ch.get("port")
        }
        if sni:
            payload["sni"] = sni
        context.user_data.pop("host_create_wait_sni", None)
        await update.message.reply_text("⏳ Создаю хост...")
        result = await HostAPI.create_host(payload)
        if result and result.get("uuid"):
            uuid = result.get("uuid")
            keyboard = [
                [InlineKeyboardButton("👁️ Просмотр", callback_data=f"view_host_{uuid}")],
                [InlineKeyboardButton("🔙 К списку", callback_data="list_hosts")]
            ]
            await update.message.reply_text("✅ Хост создан", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text("❌ Не удалось создать хост")
        return HOST_MENU

    return HOST_MENU

async def list_hosts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all hosts"""
    await update.callback_query.edit_message_text("🌐 Загрузка списка хостов...")

    hosts = await HostAPI.get_all_hosts()

    if not hosts:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Хосты не найдены или ошибка при получении списка.",
            reply_markup=reply_markup
        )
        return HOST_MENU

    message = f"🌐 *Хосты* ({len(hosts)}):\n\n"

    for i, host in enumerate(hosts):
        status_emoji = "🟢" if not host["isDisabled"] else "🔴"
        
        message += f"{i+1}. {status_emoji} *{host['remark']}*\n"
        message += f"   🌐 Адрес: {host['address']}:{host['port']}\n"
        inbound = host.get('inbound') or {}
        inbound_short = (inbound.get('configProfileInboundUuid') or '—')
        message += f"   🔌 Inbound: {inbound_short[:8]}...\n\n"

    # Add action buttons
    keyboard = []
    
    for i, host in enumerate(hosts):
        keyboard.append([
            InlineKeyboardButton(f"👁️ {host['remark']}", callback_data=f"view_host_{host['uuid']}")
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
    host = await HostAPI.get_host_by_uuid(uuid)
    
    if not host:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Хост не найден или ошибка при получении данных.",
            reply_markup=reply_markup
        )
        return HOST_MENU
    
    message = format_host_details(host)
    
    # Create action buttons
    keyboard = []
    
    if host["isDisabled"]:
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
    
    success = await HostAPI.enable_host(uuid)
    
    if success:
        await update.callback_query.edit_message_text("🟢 Хост успешно включен.")
    else:
        await update.callback_query.edit_message_text("❌ Не удалось включить хост.")
    
    return await show_host_details(update, context, uuid)

async def disable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid):
    """Disable host"""
    await update.callback_query.answer()
    
    success = await HostAPI.disable_host(uuid)
    
    if success:
        await update.callback_query.edit_message_text("🔴 Хост успешно отключен.")
    else:
        await update.callback_query.edit_message_text("❌ Не удалось отключить хост.")
    
    return await show_host_details(update, context, uuid)

async def start_edit_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Start editing a host"""
    try:
        # Get host details
        host = await HostAPI.get_host_by_uuid(uuid)
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
        
        message = f"📝 *Редактирование хоста: {host['remark']}*\n\n"
        message += f"📌 Текущие значения:\n"
        message += f"• Название: `{host['remark']}`\n"
        message += f"• Адрес: `{host['address']}`\n"
        message += f"• Порт: `{host['port']}`\n"
        message += f"• Путь: `{host.get('path', 'Не установлен')}`\n"
        message += f"• SNI: `{host.get('sni', 'Не установлен')}`\n"
        message += f"• Host: `{host.get('host', 'Не установлен')}`\n"
        message += f"• ALPN: `{host.get('alpn', 'Не установлен')}`\n"
        message += f"• Fingerprint: `{host.get('fingerprint', 'Не установлен')}`\n"
        message += f"• Allow Insecure: `{'Да' if host.get('allowInsecure') else 'Нет'}`\n"
        message += f"• Security Layer: `{host.get('securityLayer', 'Не установлен')}`\n\n"
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
            await start_edit_host_field(update, context, uuid, field)
            return EDIT_HOST_FIELD
    
    elif data.startswith("view_host_"):
        uuid = data.split("_")[2]
        await show_host_details(update, context, uuid)
        return HOST_MENU
    
    return EDIT_HOST

async def start_edit_host_field(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str, field: str):
    """Start editing a specific host field"""
    try:
        host = context.user_data.get("editing_host")
        if not host:
            # Fallback: get host from API
            host = await HostAPI.get_host_by_uuid(uuid)
            if not host:
                await update.callback_query.edit_message_text("❌ Ошибка: данные хоста не найдены.")
                return EDIT_HOST
            context.user_data["editing_host"] = host
        
        # Store field being edited
        context.user_data["editing_field"] = field
        
        # Get current value and field info
        field_info = {
            "remark": {
                "title": "Название хоста",
                "current": host.get("remark", ""),
                "example": "Например: Main-Host",
                "validation": "текст"
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
                "example": "Например: h2,http/1.1",
                "validation": "протокол или список протоколов"
            },
            "fingerprint": {
                "title": "TLS Fingerprint",
                "current": host.get("fingerprint", ""),
                "example": "Например: chrome",
                "validation": "тип fingerprint (может быть пустым)"
            },
            "allowInsecure": {
                "title": "Разрешить небезопасные соединения",
                "current": "Да" if host.get("allowInsecure") else "Нет",
                "example": "Введите: да/нет, true/false, 1/0",
                "validation": "логическое значение"
            },
            "securityLayer": {
                "title": "Уровень безопасности",
                "current": host.get("securityLayer", ""),
                "example": "Например: tls, none",
                "validation": "уровень безопасности"
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
        
        # Validate input based on field type
        validated_value = None
        error_message = None
        
        if field == "remark":
            if len(user_input) < 1:
                error_message = "Название не может быть пустым."
            elif len(user_input) > 100:
                error_message = "Название слишком длинное (максимум 100 символов)."
            else:
                validated_value = user_input
        
        elif field == "address":
            if len(user_input) < 1:
                error_message = "Адрес не может быть пустым."
            else:
                validated_value = user_input
        
        elif field == "port":
            try:
                port_num = int(user_input)
                if port_num < 1 or port_num > 65535:
                    error_message = "Порт должен быть от 1 до 65535."
                else:
                    validated_value = port_num
            except ValueError:
                error_message = "Порт должен быть числом."
        
        elif field in ["path", "sni", "host", "alpn", "fingerprint", "securityLayer"]:
            # These fields can be empty
            validated_value = user_input if user_input else ""
        
        elif field == "allowInsecure":
            lower_input = user_input.lower()
            if lower_input in ["да", "yes", "true", "1"]:
                validated_value = True
            elif lower_input in ["нет", "no", "false", "0"]:
                validated_value = False
            else:
                error_message = "Введите: да/нет, true/false, 1/0"
        
        if error_message:
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data=f"ceh_{uuid}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ {error_message}\n\nПопробуйте еще раз:",
                reply_markup=reply_markup
            )
            return EDIT_HOST_FIELD
        
        # Update host via API
        update_data = {field: validated_value}
        
        # Send update to API
        result = await HostAPI.update_host(uuid, update_data)
        
        if result:
            # Update stored host data
            host[field] = validated_value
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
    query = update.callback_query
    await query.answer()
    
    # Clear editing state
    context.user_data.pop("editing_host", None)
    context.user_data.pop("editing_field", None)
    
    if query.data.startswith("ceh_"):
        uuid = query.data.split("_")[1]
        await show_host_details(update, context, uuid)
        return HOST_MENU
    else:
        await show_hosts_menu(update, context)
        return HOST_MENU


