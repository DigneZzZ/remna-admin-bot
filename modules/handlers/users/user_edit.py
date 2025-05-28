from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import logging
import re

from modules.config import EDIT_USER, EDIT_USER_FIELD, SELECTING_USER, USER_FIELDS
from modules.api.users import UserAPI
from modules.utils.formatters import escape_markdown, format_bytes, parse_bytes

logger = logging.getLogger(__name__)

async def start_edit_user(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Start editing a user"""
    try:
        # Get user details
        response = await UserAPI.get_user_by_uuid(uuid)
        if not response or 'response' not in response:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Пользователь не найден.",
                reply_markup=reply_markup
            )
            return SELECTING_USER
        
        user = response['response']
        
        # Store user data in context
        context.user_data["editing_user"] = user
        
        # Create edit menu
        keyboard = [
            [InlineKeyboardButton("👤 Имя пользователя", callback_data=f"edit_field_username_{uuid}")],
            [InlineKeyboardButton("📊 Лимит трафика", callback_data=f"edit_field_trafficLimitBytes_{uuid}")],
            [InlineKeyboardButton("🔄 Стратегия сброса", callback_data=f"edit_field_trafficLimitStrategy_{uuid}")],
            [InlineKeyboardButton("📅 Дата истечения", callback_data=f"edit_field_expireAt_{uuid}")],
            [InlineKeyboardButton("📝 Описание", callback_data=f"edit_field_description_{uuid}")],
            [InlineKeyboardButton("📱 Telegram ID", callback_data=f"edit_field_telegramId_{uuid}")],
            [InlineKeyboardButton("📧 Email", callback_data=f"edit_field_email_{uuid}")],
            [InlineKeyboardButton("🏷️ Тег", callback_data=f"edit_field_tag_{uuid}")],
            [InlineKeyboardButton("💻 Лимит устройств", callback_data=f"edit_field_hwidDeviceLimit_{uuid}")],
            [InlineKeyboardButton("🔙 Назад к пользователю", callback_data=f"view_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"✏️ *Редактирование пользователя: {escape_markdown(user['username'])}*\n\n"
        message += f"📌 *Текущие значения:*\n"
        message += f"• Имя: `{user.get('username', 'Не указано')}`\n"
        message += f"• Лимит трафика: `{format_bytes(user.get('trafficLimitBytes', 0))}`\n"
        message += f"• Стратегия: `{user.get('trafficLimitStrategy', 'NO_RESET')}`\n"
        message += f"• Истекает: `{user.get('expireAt', 'Не установлено')[:19]}`\n"
        message += f"• Описание: `{user.get('description', 'Не указано')[:30]}...`\n"
        message += f"• Telegram ID: `{user.get('telegramId', 'Не указан')}`\n"
        message += f"• Email: `{user.get('email', 'Не указан')}`\n"
        message += f"• Тег: `{user.get('tag', 'Не указан')}`\n"
        message += f"• Лимит устройств: `{user.get('hwidDeviceLimit', 0)}`\n\n"
        message += "Выберите поле для редактирования:"
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return EDIT_USER
        
    except Exception as e:
        logger.error(f"Error starting user edit: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="list_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Ошибка при загрузке данных пользователя.",
            reply_markup=reply_markup
        )
        return SELECTING_USER

async def handle_edit_field_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle edit field selection"""
    if not update.callback_query:
        return EDIT_USER
        
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("edit_field_"):
        parts = data.split("_")
        if len(parts) >= 4:
            field = parts[2]
            uuid = "_".join(parts[3:])
            
            return await start_edit_field(update, context, uuid, field)
    
    elif data.startswith("view_"):
        from modules.handlers.users.user_details import show_user_details
        uuid = data.split("_", 1)[1]
        return await show_user_details(update, context, uuid)
    
    return EDIT_USER

async def start_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str, field: str):
    """Start editing a specific field"""
    try:
        user = context.user_data.get("editing_user")
        if not user:
            # Fallback: get user from API
            response = await UserAPI.get_user_by_uuid(uuid)
            if not response or 'response' not in response:
                await update.callback_query.edit_message_text("❌ Ошибка: данные пользователя не найдены.")
                return EDIT_USER
            user = response['response']
            context.user_data["editing_user"] = user
        
        # Store field being edited
        context.user_data["editing_field"] = field
        
        # Get current value and field info
        field_info = {
            "username": {
                "title": "Имя пользователя",
                "current": user.get("username", ""),
                "example": "Например: user123",
                "validation": "латинские буквы, цифры, подчеркивания (3-40 символов)"
            },
            "trafficLimitBytes": {
                "title": "Лимит трафика",
                "current": format_bytes(user.get("trafficLimitBytes", 0)),
                "example": "Например: 100GB, 50MB, 1TB",
                "validation": "размер с единицами измерения (KB, MB, GB, TB)"
            },
            "trafficLimitStrategy": {
                "title": "Стратегия сброса трафика",
                "current": user.get("trafficLimitStrategy", "NO_RESET"),
                "example": "NO_RESET, DAY, WEEK, MONTH",
                "validation": "одна из указанных стратегий"
            },
            "expireAt": {
                "title": "Дата истечения",
                "current": user.get("expireAt", "")[:19] if user.get("expireAt") else "",
                "example": "2024-12-31 23:59:59 или 2024-12-31",
                "validation": "формат YYYY-MM-DD [HH:MM:SS]"
            },
            "description": {
                "title": "Описание",
                "current": user.get("description", ""),
                "example": "Например: VIP пользователь",
                "validation": "любой текст (максимум 200 символов)"
            },
            "telegramId": {
                "title": "Telegram ID",
                "current": str(user.get("telegramId", "")),
                "example": "Например: 123456789",
                "validation": "числовой ID пользователя Telegram"
            },
            "email": {
                "title": "Email",
                "current": user.get("email", ""),
                "example": "Например: user@example.com",
                "validation": "корректный email адрес"
            },
            "tag": {
                "title": "Тег",
                "current": user.get("tag", ""),
                "example": "Например: vip, premium",
                "validation": "короткий тег (максимум 20 символов)"
            },
            "hwidDeviceLimit": {
                "title": "Лимит устройств HWID",
                "current": str(user.get("hwidDeviceLimit", 0)),
                "example": "Например: 1, 3, 5",
                "validation": "целое число от 0 до 100"
            }
        }
        
        if field not in field_info:
            await update.callback_query.edit_message_text("❌ Неизвестное поле для редактирования.")
            return EDIT_USER
        
        info = field_info[field]
        
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_edit_{uuid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"✏️ *Редактирование: {info['title']}*\n\n"
        message += f"📌 Текущее значение: `{info['current']}`\n\n"
        message += f"💡 {info['example']}\n"
        message += f"✅ Формат: {info['validation']}\n\n"
        message += f"✍️ Введите новое значение:"
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return EDIT_USER_FIELD
        
    except Exception as e:
        logger.error(f"Error starting field edit: {e}")
        await update.callback_query.edit_message_text("❌ Ошибка при подготовке редактирования.")
        return EDIT_USER

async def handle_edit_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle input for field editing"""
    try:
        user = context.user_data.get("editing_user")
        field = context.user_data.get("editing_field")
        
        if not user or not field:
            await update.message.reply_text("❌ Ошибка: данные редактирования потеряны.")
            return EDIT_USER
        
        user_input = update.message.text.strip()
        uuid = user["uuid"]
        
        # Validate and convert input
        try:
            validated_value = await validate_field_input(field, user_input)
        except ValueError as e:
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_edit_{uuid}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ {str(e)}\n\nПопробуйте еще раз:",
                reply_markup=reply_markup
            )
            return EDIT_USER_FIELD
        
        # Update user via API
        update_data = {field: validated_value}
        result = await UserAPI.update_user(uuid, update_data)
        
        if result:
            # Update stored user data
            user[field] = validated_value
            context.user_data["editing_user"] = user
            
            # Clear editing state
            context.user_data.pop("editing_field", None)
            
            keyboard = [
                [InlineKeyboardButton("✅ Продолжить редактирование", callback_data=f"edit_user_{uuid}")],
                [InlineKeyboardButton("📋 Показать пользователя", callback_data=f"view_{uuid}")],
                [InlineKeyboardButton("🔙 К списку пользователей", callback_data="list_users")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Поле '{field}' успешно обновлено!",
                reply_markup=reply_markup
            )
            
            return SELECTING_USER
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"edit_field_{field}_{uuid}")],
                [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_edit_{uuid}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Ошибка при обновлении пользователя. Проверьте данные и попробуйте снова.",
                reply_markup=reply_markup
            )
            return EDIT_USER_FIELD
            
    except Exception as e:
        logger.error(f"Error handling field value: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке ввода.")
        return EDIT_USER

async def validate_field_input(field: str, value: str):
    """Validate field input and convert to appropriate type"""
    if field == "username":
        if not value or len(value) < 3 or len(value) > 40:
            raise ValueError("Имя пользователя должно содержать от 3 до 40 символов")
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValueError("Имя может содержать только латинские буквы, цифры и подчеркивания")
        return value
    
    elif field == "trafficLimitBytes":
        try:
            return parse_bytes(value)
        except:
            raise ValueError("Неверный формат размера. Используйте: 100GB, 50MB, 1TB и т.д.")
    
    elif field == "trafficLimitStrategy":
        valid_strategies = ["NO_RESET", "DAY", "WEEK", "MONTH"]
        if value.upper() not in valid_strategies:
            raise ValueError(f"Стратегия должна быть одной из: {', '.join(valid_strategies)}")
        return value.upper()
    
    elif field == "expireAt":
        if not value:
            return None
        
        # Try different date formats
        formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            except ValueError:
                continue
        
        raise ValueError("Неверный формат даты. Используйте: YYYY-MM-DD или YYYY-MM-DD HH:MM:SS")
    
    elif field == "telegramId":
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            raise ValueError("Telegram ID должен быть числом")
    
    elif field == "email":
        if not value:
            return None
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError("Неверный формат email")
        return value
    
    elif field == "hwidDeviceLimit":
        try:
            limit = int(value)
            if limit < 0 or limit > 100:
                raise ValueError("Лимит устройств должен быть от 0 до 100")
            return limit
        except ValueError:
            raise ValueError("Лимит устройств должен быть числом")
    
    elif field == "description":
        if len(value) > 200:
            raise ValueError("Описание не должно превышать 200 символов")
        return value
    
    elif field == "tag":
        if len(value) > 20:
            raise ValueError("Тег не должен превышать 20 символов")
        return value
    
    else:
        return value

async def handle_cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle canceling edit"""
    if not update.callback_query:
        return SELECTING_USER
        
    query = update.callback_query
    await query.answer()
    
    # Clear editing state
    context.user_data.pop("editing_user", None)
    context.user_data.pop("editing_field", None)
    
    if query.data.startswith("cancel_edit_"):
        uuid = query.data.split("_", 2)[2]
        from modules.handlers.users.user_details import show_user_details
        return await show_user_details(update, context, uuid)
    else:
        from modules.handlers.user_handlers import show_users_menu
        return await show_users_menu(update, context)