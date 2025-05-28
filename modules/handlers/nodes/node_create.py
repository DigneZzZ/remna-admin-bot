from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import CREATE_NODE_FIELD, NODE_FIELDS, MAIN_MENU
from modules.api.nodes import NodeAPI
from modules.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

async def start_create_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start creating a new node"""
    # Clear previous data
    context.user_data.pop("create_node", None)
    context.user_data.pop("create_node_fields", None)
    context.user_data.pop("current_field_index", None)
    
    # Initialize node creation data
    context.user_data["create_node_fields"] = {}
    context.user_data["current_field_index"] = 0
    
    keyboard = [
        [InlineKeyboardButton("📝 Заполнить поля", callback_data="start_node_fields")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = "➕ *Создание нового сервера*\n\n"
    message += "Вы можете создать новый сервер, заполнив необходимые поля.\n\n"
    message += "*Обязательные поля:*\n"
    message += "• Название сервера\n"
    message += "• IP адрес\n"
    message += "• Порт\n"
    message += "• Публичный ключ\n"
    message += "• Приватный ключ\n\n"
    message += "Нажмите кнопку ниже, чтобы начать заполнение полей."
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return CREATE_NODE_FIELD

async def handle_create_node_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user input for node creation"""
    field_index = context.user_data.get("current_field_index", 0)
    fields = NODE_FIELDS
    
    if field_index >= len(fields):
        return await finish_create_node(update, context)
    
    current_field = fields[field_index]
    user_input = update.message.text.strip()
    
    # Validate input based on field type
    if current_field["name"] == "port":
        try:
            port = int(user_input)
            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
            user_input = port
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Неверный формат порта: {e}\n"
                f"Пожалуйста, введите число от 1 до 65535.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Отмена", callback_data="cancel_create_node")
                ]])
            )
            return CREATE_NODE_FIELD
    
    # Store the input
    context.user_data["create_node_fields"][current_field["name"]] = user_input
    context.user_data["current_field_index"] = field_index + 1
    
    # Move to next field or finish
    return await show_next_field(update, context)

async def show_next_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the next field to fill"""
    field_index = context.user_data.get("current_field_index", 0)
    fields = NODE_FIELDS
    
    if field_index >= len(fields):
        return await finish_create_node(update, context)
    
    current_field = fields[field_index]
    filled_fields = context.user_data.get("create_node_fields", {})
    
    # Show progress
    progress = f"📋 Поле {field_index + 1} из {len(fields)}"
    
    message = f"➕ *Создание сервера* - {progress}\n\n"
    message += f"🔹 *{current_field['display_name']}*\n"
    
    if current_field.get("description"):
        message += f"📝 {current_field['description']}\n\n"
    
    if current_field.get("example"):
        message += f"💡 Пример: `{current_field['example']}`\n\n"
    
    # Show filled fields summary
    if filled_fields:
        message += "*Заполненные поля:*\n"
        for i, field in enumerate(fields[:field_index]):
            value = filled_fields.get(field["name"], "")
            if len(str(value)) > 30:
                value = str(value)[:27] + "..."
            message += f"• {field['display_name']}: {escape_markdown(str(value))}\n"
        message += "\n"
    
    message += f"Введите значение для поля *{current_field['display_name']}*:"
    
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create_node")]
    ]
    
    # Add skip button for optional fields
    if not current_field.get("required", True):
        keyboard.insert(0, [InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_field")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except:
        # If edit fails, send new message
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    return CREATE_NODE_FIELD

async def finish_create_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish node creation and send to API"""
    node_data = context.user_data.get("create_node_fields", {})
    
    if not node_data:
        await update.message.reply_text("❌ Нет данных для создания сервера.")
        return MAIN_MENU
    
    # Show confirmation
    message = "✅ *Подтвердите создание сервера*\n\n"
    
    for field in NODE_FIELDS:
        field_name = field["name"]
        if field_name in node_data:
            value = node_data[field_name]
            if field_name in ["publicKey", "privateKey"] and len(str(value)) > 50:
                # Truncate long keys for display
                value = str(value)[:47] + "..."
            message += f"• *{field['display_name']}:* {escape_markdown(str(value))}\n"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Создать", callback_data="confirm_create_node"),
            InlineKeyboardButton("✏️ Изменить", callback_data="edit_node_fields")
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_create_node")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    return CREATE_NODE_FIELD

async def execute_create_node(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the node creation via API"""
    node_data = context.user_data.get("create_node_fields", {})
    
    try:
        await update.callback_query.answer("⏳ Создание сервера...")
        
        # Prepare data for API
        api_data = {
            "name": node_data.get("name", ""),
            "address": node_data.get("address", ""),
            "port": int(node_data.get("port", 443)),
            "publicKey": node_data.get("publicKey", ""),
            "privateKey": node_data.get("privateKey", "")
        }
        
        # Optional fields
        if "remark" in node_data:
            api_data["remark"] = node_data["remark"]
        if "countryCode" in node_data:
            api_data["countryCode"] = node_data["countryCode"]
        if "trafficLimitBytes" in node_data:
            api_data["trafficLimitBytes"] = int(node_data["trafficLimitBytes"])
        if "consumptionMultiplier" in node_data:
            api_data["consumptionMultiplier"] = float(node_data["consumptionMultiplier"])
        
        response = await NodeAPI.create_node(api_data)
        
        if response and 'response' in response:
            node = response['response']
            keyboard = [
                [InlineKeyboardButton("👁️ Просмотреть", callback_data=f"view_node_{node['uuid']}")],
                [InlineKeyboardButton("🔙 К серверам", callback_data="back_to_nodes")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"✅ *Сервер успешно создан!*\n\n"
                f"🖥️ *Название:* {escape_markdown(node['name'])}\n"
                f"🆔 *UUID:* `{node['uuid']}`\n"
                f"🌐 *Адрес:* {escape_markdown(node['address'])}:{node['port']}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Ошибка при создании сервера. Проверьте данные и попробуйте еще раз.",
                reply_markup=reply_markup
            )
    
    except Exception as e:
        logger.error(f"Error creating node: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при создании сервера: {str(e)}",
            reply_markup=reply_markup
        )
    
    # Clear creation data
    context.user_data.pop("create_node_fields", None)
    context.user_data.pop("current_field_index", None)
    
    return MAIN_MENU
