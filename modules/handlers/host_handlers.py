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
    elif data == "back_to_main":
        return await show_main_menu(update, context)
    
    # Handle host actions
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

async def show_host_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show detailed host information"""
    try:
        host = await HostAPI.get_host_by_uuid(uuid)
        if not host:
            await update.callback_query.edit_message_text(
                "❌ Хост не найден.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]])
            )
            return HOST_MENU

        # Format host details
        formatted_details = format_host_details(host)
        
        keyboard = [
            [
                InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_host_{uuid}"),
                InlineKeyboardButton("🔄 Вкл/Выкл", callback_data=f"toggle_host_{uuid}")
            ],
            [
                InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_host_{uuid}"),
            ],
            [InlineKeyboardButton("🔙 К списку хостов", callback_data="list_hosts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=formatted_details,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error showing host details for {uuid}: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при загрузке информации о хосте.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]])
        )

    return HOST_MENU

async def enable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Enable a host"""
    try:
        result = await HostAPI.enable_host(uuid)
        if result:
            await update.callback_query.edit_message_text("✅ Хост успешно включен!")
        else:
            await update.callback_query.edit_message_text("❌ Не удалось включить хост.")
    except Exception as e:
        logger.error(f"Error enabling host {uuid}: {e}")
        await update.callback_query.edit_message_text("❌ Произошла ошибка при включении хоста.")
    
    return HOST_MENU

async def disable_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Disable a host"""
    try:
        result = await HostAPI.disable_host(uuid)
        if result:
            await update.callback_query.edit_message_text("✅ Хост успешно отключен!")
        else:
            await update.callback_query.edit_message_text("❌ Не удалось отключить хост.")
    except Exception as e:
        logger.error(f"Error disabling host {uuid}: {e}")
        await update.callback_query.edit_message_text("❌ Произошла ошибка при отключении хоста.")
    
    return HOST_MENU

async def confirm_delete_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Confirm host deletion"""
    try:
        host = await HostAPI.get_host_by_uuid(uuid)
        if not host:
            await update.callback_query.edit_message_text(
                "❌ Хост не найден.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]])
            )
            return HOST_MENU

        message = f"⚠️ *Подтвердите удаление хоста*\n\n"
        message += f"🌐 *Хост:* {host.get('remark', 'Без названия')}\n"
        message += f"📍 *Адрес:* {host.get('address', 'N/A')}:{host.get('port', 'N/A')}\n\n"
        message += "❗ *Это действие нельзя отменить!*"

        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{uuid}"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"view_host_{uuid}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error confirming delete for host {uuid}: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при подготовке удаления хоста.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]])
        )

    return HOST_MENU

async def delete_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Delete a host"""
    try:
        result = await HostAPI.delete_host(uuid)
        if result:
            await update.callback_query.edit_message_text("✅ Хост успешно удален!")
        else:
            await update.callback_query.edit_message_text("❌ Не удалось удалить хост.")
    except Exception as e:
        logger.error(f"Error deleting host {uuid}: {e}")
        await update.callback_query.edit_message_text("❌ Произошла ошибка при удалении хоста.")
    
    return HOST_MENU

async def show_search_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show host search menu"""
    await update.callback_query.edit_message_text(
        "🔍 *Поиск хостов*\n\nВведите параметр для поиска:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]])
    )
    return HOST_MENU

async def start_create_host(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start host creation process"""
    await update.callback_query.edit_message_text("🔄 Подготовка к созданию хоста...")
    
    try:
        # Get available inbounds
        inbounds = await InboundAPI.get_all_inbounds()
        
        if not inbounds:
            await update.callback_query.edit_message_text(
                "❌ Нет доступных Inbound'ов для создания хоста.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]])
            )
            return HOST_MENU

        # Store creation context
        context.user_data["creating_host"] = {
            "step": "select_inbound",
            "inbounds": inbounds
        }

        message = "➕ *Создание нового хоста*\n\n"
        message += "Выберите Inbound для хоста:"

        keyboard = []
        for inbound in inbounds:
            display_name = f"🔌 {inbound.get('tag', 'Unknown')} ({inbound.get('type', 'Unknown')})"
            keyboard.append([InlineKeyboardButton(display_name, callback_data=f"select_inbound_{inbound['uuid']}")])

        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error starting host creation: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при подготовке создания хоста.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_hosts")]])
        )

    return CREATE_HOST

async def start_edit_host(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Start host editing process"""
    try:
        host = await HostAPI.get_host_by_uuid(uuid)
        if not host:
            await update.callback_query.edit_message_text(
                "❌ Хост не найден.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]])
            )
            return HOST_MENU

        # Store editing context
        context.user_data["editing_host"] = host

        message = f"✏️ *Редактирование хоста*\n\n"
        message += f"🌐 *Текущий хост:* {host.get('remark', 'Без названия')}\n\n"
        message += "Выберите поле для редактирования:"

        keyboard = [
            [InlineKeyboardButton("📝 Название", callback_data="edit_field_remark")],
            [InlineKeyboardButton("🌐 Адрес", callback_data="edit_field_address")],
            [InlineKeyboardButton("🔢 Порт", callback_data="edit_field_port")],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"view_host_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error starting host edit for {uuid}: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ошибка при подготовке редактирования хоста.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="list_hosts")]])
        )

    return EDIT_HOST

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
