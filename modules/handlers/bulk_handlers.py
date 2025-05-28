from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import MAIN_MENU, BULK_MENU, BULK_ACTION, BULK_CONFIRM
from modules.api.bulk import BulkAPI
from modules.api.users import UserAPI
from modules.utils.selection_helpers import SelectionHelper
from modules.handlers.start_handler import show_main_menu

logger = logging.getLogger(__name__)

async def show_bulk_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bulk operations menu"""
    keyboard = [
        [
            InlineKeyboardButton("👥 Операции с пользователями", callback_data="bulk_users_menu"),
            InlineKeyboardButton("📡 Операции с inbound'ами", callback_data="bulk_inbounds_menu")
        ],
        [
            InlineKeyboardButton("🖥️ Операции с нодами", callback_data="bulk_nodes_menu"),
            InlineKeyboardButton("🌐 Операции с хостами", callback_data="bulk_hosts_menu")
        ],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🔄 *Массовые операции*\n\n"
    message += "⚠️ Внимание! Эти операции затрагивают множество объектов одновременно.\n\n"
    message += "Выберите категорию операций:"

    # Определяем chat_id
    chat_id = update.effective_chat.id if update.effective_chat else None
    
    if not chat_id:
        logger.error("Cannot determine chat_id")
        return BULK_MENU

    # Пытаемся отредактировать существующее сообщение, если это callback
    if update.callback_query and update.callback_query.message:
        try:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return BULK_MENU
        except Exception as e:
            logger.warning(f"Failed to edit message: {e}")
    
    # Отправляем новое сообщение
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        # Fallback без Markdown
        await context.bot.send_message(
            chat_id=chat_id,
            text="🔄 Массовые операции\n\nВыберите категорию операций:",
            reply_markup=reply_markup
        )
    
    return BULK_MENU

async def show_bulk_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bulk users operations menu"""
    
    if not update.callback_query:
        logger.warning("show_bulk_users_menu called without callback_query")
        return BULK_MENU
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 Сбросить трафик всем", callback_data="bulk_reset_all_traffic"),
            InlineKeyboardButton("❌ Отозвать подписки всем", callback_data="bulk_revoke_all_subs")
        ],
        [
            InlineKeyboardButton("🔄 Сбросить трафик с исчерпанным лимитом", callback_data="bulk_reset_limited_traffic"),
            InlineKeyboardButton("❌ Удалить истекших", callback_data="bulk_delete_expired")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_bulk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "👥 *Массовые операции с пользователями*\n\n"
    message += "Выберите действие:"

    try:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in show_bulk_users_menu: {e}")
    
    return BULK_MENU

async def show_bulk_inbounds_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bulk inbounds operations menu"""
    
    if not update.callback_query:
        return BULK_MENU
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Включить все inbound'ы", callback_data="bulk_enable_all_inbounds"),
            InlineKeyboardButton("❌ Отключить все inbound'ы", callback_data="bulk_disable_all_inbounds")
        ],
        [
            InlineKeyboardButton("🔄 Перезапустить все inbound'ы", callback_data="bulk_restart_all_inbounds"),
            InlineKeyboardButton("❌ Удалить все inbound'ы", callback_data="bulk_delete_all_inbounds")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_bulk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "📡 *Массовые операции с inbound'ами*\n\n"
    message += "Выберите действие:"

    try:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in show_bulk_inbounds_menu: {e}")
    
    return BULK_MENU

async def show_bulk_nodes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bulk nodes operations menu"""
    
    if not update.callback_query:
        return BULK_MENU
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Включить все ноды", callback_data="bulk_enable_all_nodes"),
            InlineKeyboardButton("❌ Отключить все ноды", callback_data="bulk_disable_all_nodes")
        ],
        [
            InlineKeyboardButton("🔄 Перезапустить все ноды", callback_data="bulk_restart_all_nodes"),
            InlineKeyboardButton("❌ Удалить все ноды", callback_data="bulk_delete_all_nodes")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_bulk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🖥️ *Массовые операции с нодами*\n\n"
    message += "Выберите действие:"

    try:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in show_bulk_nodes_menu: {e}")
    
    return BULK_MENU

async def show_bulk_hosts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bulk hosts operations menu"""
    
    if not update.callback_query:
        return BULK_MENU
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Включить все хосты", callback_data="bulk_enable_all_hosts"),
            InlineKeyboardButton("❌ Отключить все хосты", callback_data="bulk_disable_all_hosts")
        ],
        [
            InlineKeyboardButton("❌ Удалить все хосты", callback_data="bulk_delete_all_hosts")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_bulk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🌐 *Массовые операции с хостами*\n\n"
    message += "Выберите действие:"

    try:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in show_bulk_hosts_menu: {e}")
    
    return BULK_MENU

async def handle_bulk_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bulk operations menu selection"""
    if not update.callback_query:
        logger.warning("handle_bulk_menu called without callback_query")
        return BULK_MENU
    
    query = update.callback_query
    await query.answer()
    data = query.data

    # Навигация по меню
    if data == "bulk_users_menu":
        return await show_bulk_users_menu(update, context)
    elif data == "bulk_inbounds_menu":
        return await show_bulk_inbounds_menu(update, context)
    elif data == "bulk_nodes_menu":
        return await show_bulk_nodes_menu(update, context)
    elif data == "bulk_hosts_menu":
        return await show_bulk_hosts_menu(update, context)
    elif data == "back_to_bulk":
        return await show_bulk_menu(update, context)
    elif data == "back_to_main":
        return await show_main_menu(update, context)

    # Операции с пользователями - подтверждение
    elif data == "bulk_reset_all_traffic":
        return await show_confirmation(query, "Сбросить трафик ВСЕМ пользователям?", "confirm_reset_all_traffic")
    elif data == "bulk_revoke_all_subs":
        return await show_confirmation(query, "Отозвать подписки у ВСЕХ пользователей?", "confirm_revoke_all_subs")
    elif data == "bulk_reset_limited_traffic":
        return await show_confirmation(query, "Сбросить трафик пользователям с исчерпанным лимитом?", "confirm_reset_limited_traffic")
    elif data == "bulk_delete_expired":
        return await show_confirmation(query, "Удалить пользователей с истекшим сроком?", "confirm_delete_expired")

    # Операции с inbound'ами - подтверждение
    elif data == "bulk_enable_all_inbounds":
        return await show_confirmation(query, "Включить ВСЕ inbound'ы?", "confirm_enable_all_inbounds")
    elif data == "bulk_disable_all_inbounds":
        return await show_confirmation(query, "Отключить ВСЕ inbound'ы?", "confirm_disable_all_inbounds")
    elif data == "bulk_restart_all_inbounds":
        return await show_confirmation(query, "Перезапустить ВСЕ inbound'ы?", "confirm_restart_all_inbounds")
    elif data == "bulk_delete_all_inbounds":
        return await show_confirmation(query, "Удалить ВСЕ inbound'ы?", "confirm_delete_all_inbounds")

    # Операции с нодами - подтверждение
    elif data == "bulk_enable_all_nodes":
        return await show_confirmation(query, "Включить ВСЕ ноды?", "confirm_enable_all_nodes")
    elif data == "bulk_disable_all_nodes":
        return await show_confirmation(query, "Отключить ВСЕ ноды?", "confirm_disable_all_nodes")
    elif data == "bulk_restart_all_nodes":
        return await show_confirmation(query, "Перезапустить ВСЕ ноды?", "confirm_restart_all_nodes")
    elif data == "bulk_delete_all_nodes":
        return await show_confirmation(query, "Удалить ВСЕ ноды?", "confirm_delete_all_nodes")

    # Операции с хостами - подтверждение
    elif data == "bulk_enable_all_hosts":
        return await show_confirmation(query, "Включить ВСЕ хосты?", "confirm_enable_all_hosts")
    elif data == "bulk_disable_all_hosts":
        return await show_confirmation(query, "Отключить ВСЕ хосты?", "confirm_disable_all_hosts")
    elif data == "bulk_delete_all_hosts":
        return await show_confirmation(query, "Удалить ВСЕ хосты?", "confirm_delete_all_hosts")

    # Если ни одно условие не сработало, возвращаем текущее состояние
    logger.warning(f"Unhandled callback data: {data}")
    return BULK_MENU

async def show_confirmation(query, message_text, confirm_action):
    """Show confirmation dialog for bulk operation"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, выполнить", callback_data=confirm_action),
            InlineKeyboardButton("❌ Отмена", callback_data="back_to_bulk")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"⚠️ {message_text}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return BULK_CONFIRM

async def handle_bulk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bulk operation confirmation"""
    
    if not update.callback_query:
        return BULK_MENU
    
    query = update.callback_query
    await query.answer()
    data = query.data

    # Показать сообщение о выполнении
    await query.edit_message_text("⏳ Выполняется операция...")

    try:
        # ========================
        # ОПЕРАЦИИ С ПОЛЬЗОВАТЕЛЯМИ
        # ========================
        if data == "confirm_reset_all_traffic":
            result = await BulkAPI.bulk_reset_all_users_traffic()
            message = "✅ Трафик успешно сброшен у всех пользователей." if result else "❌ Ошибка при сбросе трафика."

        elif data == "confirm_revoke_all_subs":
            result = await BulkAPI.bulk_revoke_all_users_subscription()
            message = "✅ Подписки успешно отозваны у всех пользователей." if result else "❌ Ошибка при отзыве подписок."

        elif data == "confirm_reset_limited_traffic":
            # Получаем всех пользователей с статусом LIMITED и сбрасываем им трафик
            try:
                limited_users_response = await UserAPI.get_limited_users()
                if limited_users_response and 'response' in limited_users_response:
                    limited_users = limited_users_response['response']
                    if limited_users:
                        user_uuids = [user['uuid'] for user in limited_users]
                        result = await BulkAPI.bulk_reset_users_traffic(user_uuids)
                        if result:
                            message = f"✅ Трафик сброшен у {len(user_uuids)} пользователей с исчерпанным лимитом."
                        else:
                            message = "❌ Ошибка при сбросе трафика пользователям с исчерпанным лимитом."
                    else:
                        message = "ℹ️ Нет пользователей с исчерпанным лимитом трафика."
                else:
                    message = "❌ Не удалось получить список пользователей с исчерпанным лимитом."
            except Exception as e:
                logger.error(f"Error resetting traffic for limited users: {e}")
                message = "❌ Ошибка при получении пользователей с исчерпанным лимитом."

        elif data == "confirm_delete_expired":
            result = await BulkAPI.bulk_delete_users_by_status("EXPIRED")
            if result and 'response' in result:
                count = result['response'].get('deletedCount', 0)
                message = f"✅ Успешно удалено {count} пользователей с истекшим сроком."
            else:
                message = "❌ Ошибка при удалении истекших пользователей."

        # ========================
        # ОПЕРАЦИИ С INBOUND'АМИ
        # ========================
        elif data == "confirm_enable_all_inbounds":
            from modules.api.inbounds import InboundAPI
            inbounds_response = await InboundAPI.get_all_inbounds()
            if inbounds_response and 'response' in inbounds_response:
                inbound_uuids = [inbound['uuid'] for inbound in inbounds_response['response']]
                result = await BulkAPI.bulk_enable_inbounds(inbound_uuids)
                message = f"✅ Включено {len(inbound_uuids)} inbound'ов." if result else "❌ Ошибка при включении inbound'ов."
            else:
                message = "❌ Не удалось получить список inbound'ов."

        elif data == "confirm_disable_all_inbounds":
            from modules.api.inbounds import InboundAPI
            inbounds_response = await InboundAPI.get_all_inbounds()
            if inbounds_response and 'response' in inbounds_response:
                inbound_uuids = [inbound['uuid'] for inbound in inbounds_response['response']]
                result = await BulkAPI.bulk_disable_inbounds(inbound_uuids)
                message = f"✅ Отключено {len(inbound_uuids)} inbound'ов." if result else "❌ Ошибка при отключении inbound'ов."
            else:
                message = "❌ Не удалось получить список inbound'ов."

        elif data == "confirm_restart_all_inbounds":
            from modules.api.inbounds import InboundAPI
            inbounds_response = await InboundAPI.get_all_inbounds()
            if inbounds_response and 'response' in inbounds_response:
                inbound_uuids = [inbound['uuid'] for inbound in inbounds_response['response']]
                result = await BulkAPI.bulk_restart_inbounds(inbound_uuids)
                message = f"✅ Перезапущено {len(inbound_uuids)} inbound'ов." if result else "❌ Ошибка при перезапуске inbound'ов."
            else:
                message = "❌ Не удалось получить список inbound'ов."

        elif data == "confirm_delete_all_inbounds":
            from modules.api.inbounds import InboundAPI
            inbounds_response = await InboundAPI.get_all_inbounds()
            if inbounds_response and 'response' in inbounds_response:
                inbound_uuids = [inbound['uuid'] for inbound in inbounds_response['response']]
                result = await BulkAPI.bulk_delete_inbounds(inbound_uuids)
                message = f"✅ Удалено {len(inbound_uuids)} inbound'ов." if result else "❌ Ошибка при удалении inbound'ов."
            else:
                message = "❌ Не удалось получить список inbound'ов."

        # ========================
        # ОПЕРАЦИИ С НОДАМИ
        # ========================
        elif data == "confirm_enable_all_nodes":
            from modules.api.nodes import NodeAPI
            nodes_response = await NodeAPI.get_all_nodes()
            if nodes_response and 'response' in nodes_response:
                node_uuids = [node['uuid'] for node in nodes_response['response']]
                result = await BulkAPI.bulk_enable_nodes(node_uuids)
                message = f"✅ Включено {len(node_uuids)} нод." if result else "❌ Ошибка при включении нод."
            else:
                message = "❌ Не удалось получить список нод."

        elif data == "confirm_disable_all_nodes":
            from modules.api.nodes import NodeAPI
            nodes_response = await NodeAPI.get_all_nodes()
            if nodes_response and 'response' in nodes_response:
                node_uuids = [node['uuid'] for node in nodes_response['response']]
                result = await BulkAPI.bulk_disable_nodes(node_uuids)
                message = f"✅ Отключено {len(node_uuids)} нод." if result else "❌ Ошибка при отключении нод."
            else:
                message = "❌ Не удалось получить список нод."

        elif data == "confirm_restart_all_nodes":
            from modules.api.nodes import NodeAPI
            nodes_response = await NodeAPI.get_all_nodes()
            if nodes_response and 'response' in nodes_response:
                node_uuids = [node['uuid'] for node in nodes_response['response']]
                result = await BulkAPI.bulk_restart_nodes(node_uuids)
                message = f"✅ Перезапущено {len(node_uuids)} нод." if result else "❌ Ошибка при перезапуске нод."
            else:
                message = "❌ Не удалось получить список нод."

        elif data == "confirm_delete_all_nodes":
            from modules.api.nodes import NodeAPI
            nodes_response = await NodeAPI.get_all_nodes()
            if nodes_response and 'response' in nodes_response:
                node_uuids = [node['uuid'] for node in nodes_response['response']]
                result = await BulkAPI.bulk_delete_nodes(node_uuids)
                message = f"✅ Удалено {len(node_uuids)} нод." if result else "❌ Ошибка при удалении нод."
            else:
                message = "❌ Не удалось получить список нод."

        # ========================
        # ОПЕРАЦИИ С ХОСТАМИ
        # ========================
        elif data == "confirm_enable_all_hosts":
            from modules.api.hosts import HostAPI
            hosts_response = await HostAPI.get_all_hosts()
            if hosts_response and 'response' in hosts_response:
                host_uuids = [host['uuid'] for host in hosts_response['response']]
                result = await BulkAPI.bulk_enable_hosts(host_uuids)
                message = f"✅ Включено {len(host_uuids)} хостов." if result else "❌ Ошибка при включении хостов."
            else:
                message = "❌ Не удалось получить список хостов."

        elif data == "confirm_disable_all_hosts":
            from modules.api.hosts import HostAPI
            hosts_response = await HostAPI.get_all_hosts()
            if hosts_response and 'response' in hosts_response:
                host_uuids = [host['uuid'] for host in hosts_response['response']]
                result = await BulkAPI.bulk_disable_hosts(host_uuids)
                message = f"✅ Отключено {len(host_uuids)} хостов." if result else "❌ Ошибка при отключении хостов."
            else:
                message = "❌ Не удалось получить список хостов."

        elif data == "confirm_delete_all_hosts":
            from modules.api.hosts import HostAPI
            hosts_response = await HostAPI.get_all_hosts()
            if hosts_response and 'response' in hosts_response:
                host_uuids = [host['uuid'] for host in hosts_response['response']]
                result = await BulkAPI.bulk_delete_hosts(host_uuids)
                message = f"✅ Удалено {len(host_uuids)} хостов." if result else "❌ Ошибка при удалении хостов."
            else:
                message = "❌ Не удалось получить список хостов."

        elif data == "back_to_bulk":
            return await show_bulk_menu(update, context)

        else:
            message = "❌ Неизвестная операция."

    except Exception as e:
        logger.error(f"Error in bulk operation {data}: {e}")
        message = f"❌ Произошла ошибка: {str(e)}"

    # Показать результат с кнопкой возврата
    keyboard = [[InlineKeyboardButton("🔙 Назад к массовым операциям", callback_data="back_to_bulk")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return BULK_MENU

# Export functions for conversation handler
__all__ = [
    'show_bulk_menu',
    'handle_bulk_menu',
    'handle_bulk_action',
    'handle_bulk_confirm'
]

# Missing functions for conversation handler compatibility
async def handle_bulk_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bulk action - alias for handle_bulk_menu"""
    return await handle_bulk_menu(update, context)

async def handle_bulk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bulk confirmation - alias for handle_bulk_menu"""
    return await handle_bulk_menu(update, context)