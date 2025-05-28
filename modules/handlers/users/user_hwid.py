from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import SELECTING_USER, WAITING_FOR_INPUT
from modules.api.users import UserAPI
from modules.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

async def show_user_hwid_devices(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show user HWID devices"""
    try:
        # Get user details first
        user_response = await UserAPI.get_user_by_uuid(uuid)
        if not user_response or 'response' not in user_response:
            await update.callback_query.edit_message_text("❌ Пользователь не найден.")
            return SELECTING_USER
        
        user = user_response['response']
        
        # Get HWID devices
        devices_response = await UserAPI.get_user_hwid_devices(uuid)
        
        if not devices_response or 'response' not in devices_response:
            devices = []
        else:
            devices = devices_response['response']
        
        message = f"💻 *HWID устройства пользователя*\n\n"
        message += f"👤 Пользователь: `{escape_markdown(user['username'])}`\n"
        message += f"🆔 UUID: `{user['uuid']}`\n"
        message += f"📱 Лимит устройств: `{user.get('hwidDeviceLimit', 0)}`\n"
        message += f"💻 Подключено устройств: `{len(devices)}`\n\n"
        
        if devices:
            message += f"📋 *Список устройств:*\n"
            for i, device in enumerate(devices, 1):
                device_id = device.get('deviceId', 'N/A')
                device_name = device.get('deviceName', 'Неизвестно')
                last_seen = device.get('lastSeen', 'Никогда')
                
                message += f"{i}. `{device_id[:16]}...`\n"
                message += f"   📱 Имя: {device_name}\n"
                message += f"   ⏰ Последний раз: {last_seen[:19] if last_seen != 'Никогда' else last_seen}\n\n"
        else:
            message += f"ℹ️ Устройства не подключены"
        
        keyboard = []
        
        if devices:
            # Add device management buttons
            for device in devices[:5]:  # Show max 5 devices for UI clarity
                device_id = device.get('deviceId', '')
                device_name = device.get('deviceName', device_id[:8] + '...')
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ Удалить {device_name}", 
                        callback_data=f"delete_hwid_{uuid}_{device_id}"
                    )
                ])
            
            if len(devices) > 5:
                keyboard.append([
                    InlineKeyboardButton("📋 Показать все устройства", callback_data=f"show_all_hwid_{uuid}")
                ])
            
            keyboard.append([
                InlineKeyboardButton("❌ Сбросить все устройства", callback_data=f"reset_all_hwid_{uuid}")
            ])
        
        keyboard.extend([
            [InlineKeyboardButton("🔄 Обновить", callback_data=f"hwid_{uuid}")],
            [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error showing HWID devices for user {uuid}: {e}")
        
        keyboard = [[InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке HWID устройств: {str(e)}",
            reply_markup=reply_markup
        )
        
        return SELECTING_USER

async def handle_hwid_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle HWID device actions"""
    if not update.callback_query:
        return SELECTING_USER
    
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("delete_hwid_"):
        parts = data.split("_", 3)
        if len(parts) >= 4:
            uuid = parts[2]
            device_id = parts[3]
            return await confirm_delete_hwid_device(update, context, uuid, device_id)
    
    elif data.startswith("reset_all_hwid_"):
        uuid = data.split("_", 3)[3]
        return await confirm_reset_all_hwid_devices(update, context, uuid)
    
    elif data.startswith("show_all_hwid_"):
        uuid = data.split("_", 3)[3]
        return await show_all_hwid_devices(update, context, uuid)
    
    elif data.startswith("hwid_"):
        uuid = data.split("_", 1)[1]
        return await show_user_hwid_devices(update, context, uuid)
    
    return SELECTING_USER

async def confirm_delete_hwid_device(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str, device_id: str):
    """Confirm HWID device deletion"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_hwid_{uuid}_{device_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"hwid_{uuid}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"⚠️ *Подтверждение удаления устройства*\n\n"
    message += f"Вы действительно хотите удалить устройство?\n"
    message += f"🆔 Device ID: `{device_id[:32]}...`\n\n"
    message += f"❗ Это действие необратимо!"
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SELECTING_USER

async def confirm_reset_all_hwid_devices(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Confirm reset all HWID devices"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, сбросить все", callback_data=f"confirm_reset_all_hwid_{uuid}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"hwid_{uuid}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"⚠️ *Подтверждение сброса всех устройств*\n\n"
    message += f"Вы действительно хотите удалить ВСЕ HWID устройства пользователя?\n\n"
    message += f"❗ Это действие необратимо!"
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return SELECTING_USER

async def execute_delete_hwid_device(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str, device_id: str):
    """Execute HWID device deletion"""
    await update.callback_query.edit_message_text("⏳ Удаление устройства...")
    
    try:
        result = await UserAPI.delete_user_hwid_device(uuid, device_id)
        
        if result:
            message = "✅ Устройство успешно удалено."
        else:
            message = "❌ Не удалось удалить устройство."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить список", callback_data=f"hwid_{uuid}")],
            [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup
        )
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error deleting HWID device {device_id} for user {uuid}: {e}")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"delete_hwid_{uuid}_{device_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"hwid_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Произошла ошибка при удалении устройства: {str(e)}",
            reply_markup=reply_markup
        )
        
        return SELECTING_USER

async def execute_reset_all_hwid_devices(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Execute reset all HWID devices"""
    await update.callback_query.edit_message_text("⏳ Сброс всех устройств...")
    
    try:
        result = await UserAPI.reset_all_user_hwid_devices(uuid)
        
        if result:
            message = "✅ Все устройства успешно удалены."
        else:
            message = "❌ Не удалось удалить устройства."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить список", callback_data=f"hwid_{uuid}")],
            [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup
        )
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error resetting all HWID devices for user {uuid}: {e}")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"reset_all_hwid_{uuid}")],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"hwid_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Произошла ошибка при сбросе устройств: {str(e)}",
            reply_markup=reply_markup
        )
        
        return SELECTING_USER

async def show_all_hwid_devices(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show all HWID devices in detail"""
    try:
        devices_response = await UserAPI.get_user_hwid_devices(uuid)
        
        if not devices_response or 'response' not in devices_response:
            devices = []
        else:
            devices = devices_response['response']
        
        if not devices:
            await update.callback_query.edit_message_text("ℹ️ У пользователя нет подключенных устройств.")
            return SELECTING_USER
        
        message = f"💻 *Все HWID устройства ({len(devices)} шт.)*\n\n"
        
        for i, device in enumerate(devices, 1):
            device_id = device.get('deviceId', 'N/A')
            device_name = device.get('deviceName', 'Неизвестно')
            last_seen = device.get('lastSeen', 'Никогда')
            created_at = device.get('createdAt', 'Неизвестно')
            
            message += f"*{i}. Устройство {i}*\n"
            message += f"🆔 ID: `{device_id}`\n"
            message += f"📱 Имя: {escape_markdown(device_name)}\n"
            message += f"⏰ Последний раз: {last_seen[:19] if last_seen != 'Никогда' else last_seen}\n"
            message += f"📅 Создано: {created_at[:19] if created_at != 'Неизвестно' else created_at}\n\n"
            
            # Limit message length
            if len(message) > 3500:
                message += f"... и еще {len(devices) - i} устройств"
                break
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад к управлению HWID", callback_data=f"hwid_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Error showing all HWID devices for user {uuid}: {e}")
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"hwid_{uuid}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке устройств: {str(e)}",
            reply_markup=reply_markup
        )
        
        return SELECTING_USER

async def handle_hwid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle HWID input (for manual operations)"""
    user_input = update.message.text.strip()
    
    # This function can be extended for manual HWID operations
    # For now, just acknowledge the input
    
    await update.message.reply_text(
        "❌ Ручное управление HWID пока не реализовано.\n"
        "Используйте интерфейс с кнопками."
    )
    
    # Clear waiting state
    context.user_data.pop("waiting_for", None)
    
    return SELECTING_USER