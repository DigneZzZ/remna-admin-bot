from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import EDIT_NODE_FIELD, NODE_FIELDS, SELECTING_NODE
from modules.api.nodes import NodeAPI
from modules.utils.formatters import escape_markdown, format_bytes, parse_bytes
from modules.utils.selection_helpers import SelectionHelper

logger = logging.getLogger(__name__)

async def start_edit_node(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Start editing a node"""
    try:
        response = await NodeAPI.get_node_by_uuid(uuid)
        
        if not response or 'response' not in response:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Сервер не найден.",
                reply_markup=reply_markup
            )
            return SELECTING_NODE
        
        node = response['response']
        context.user_data["edit_node_uuid"] = uuid
        context.user_data["edit_node_data"] = node
        
        # Create field selection keyboard
        keyboard = []
        
        # Group fields by category
        basic_fields = ["name", "address", "port", "remark"]
        config_fields = ["countryCode", "trafficLimitBytes", "consumptionMultiplier"]
        
        # Basic settings
        keyboard.append([InlineKeyboardButton("📝 Основные настройки", callback_data="edit_basic")])
        for field_name in basic_fields:
            field_info = next((f for f in NODE_FIELDS if f["name"] == field_name), None)
            if field_info:
                current_value = node.get(field_name, "Не указано")
                if field_name == "trafficLimitBytes" and current_value:
                    current_value = format_bytes(current_value)
                
                display_value = str(current_value)
                if len(display_value) > 20:
                    display_value = display_value[:17] + "..."
                
                keyboard.append([InlineKeyboardButton(
                    f"• {field_info['display_name']}: {display_value}",
                    callback_data=f"edit_field_{field_name}"
                )])
        
        # Configuration
        keyboard.append([InlineKeyboardButton("⚙️ Конфигурация", callback_data="edit_config")])
        for field_name in config_fields:
            field_info = next((f for f in NODE_FIELDS if f["name"] == field_name), None)
            if field_info:
                current_value = node.get(field_name, "Не указано")
                if field_name == "trafficLimitBytes" and current_value:
                    current_value = format_bytes(current_value)
                
                display_value = str(current_value)
                if len(display_value) > 20:
                    display_value = display_value[:17] + "..."
                
                keyboard.append([InlineKeyboardButton(
                    f"• {field_info['display_name']}: {display_value}",
                    callback_data=f"edit_field_{field_name}"
                )])
        
        # Actions
        keyboard.extend([
            [InlineKeyboardButton("💾 Сохранить изменения", callback_data="save_node_changes")],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"view_node_{uuid}")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"✏️ *Редактирование сервера*\n\n"
        message += f"🖥️ *Сервер:* {escape_markdown(node['name'])}\n"
        message += f"🆔 *UUID:* `{uuid}`\n\n"
        message += "Выберите поле для редактирования:"
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return EDIT_NODE_FIELD
        
    except Exception as e:
        logger.error(f"Error starting node edit: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при загрузке данных сервера: {str(e)}",
            reply_markup=reply_markup
        )
        return SELECTING_NODE

async def handle_edit_field_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle field selection for editing"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("edit_field_"):
        field_name = data.replace("edit_field_", "")
        context.user_data["edit_field_name"] = field_name
        
        field_info = next((f for f in NODE_FIELDS if f["name"] == field_name), None)
        if not field_info:
            await query.edit_message_text("❌ Неизвестное поле.")
            return EDIT_NODE_FIELD
        
        node_data = context.user_data.get("edit_node_data", {})
        current_value = node_data.get(field_name, "")
        
        message = f"✏️ *Редактирование поля*\n\n"
        message += f"🔹 *Поле:* {field_info['display_name']}\n"
        
        if field_info.get("description"):
            message += f"📝 *Описание:* {field_info['description']}\n"
        
        if current_value:
            if field_name == "trafficLimitBytes":
                display_value = format_bytes(current_value)
            else:
                display_value = str(current_value)
            message += f"📊 *Текущее значение:* {escape_markdown(display_value)}\n"
        
        if field_info.get("example"):
            message += f"💡 *Пример:* `{field_info['example']}`\n"
        
        message += f"\nВведите новое значение для поля *{field_info['display_name']}*:"
        
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_edit_field")]
        ]
        
        # Add clear button for optional fields
        if not field_info.get("required", True) and current_value:
            keyboard.insert(0, [InlineKeyboardButton("🗑️ Очистить", callback_data="clear_field")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return EDIT_NODE_FIELD
    
    return EDIT_NODE_FIELD

async def handle_edit_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new field value input"""
    field_name = context.user_data.get("edit_field_name")
    if not field_name:
        await update.message.reply_text("❌ Ошибка: поле не выбрано.")
        return EDIT_NODE_FIELD
    
    field_info = next((f for f in NODE_FIELDS if f["name"] == field_name), None)
    if not field_info:
        await update.message.reply_text("❌ Ошибка: неизвестное поле.")
        return EDIT_NODE_FIELD
    
    new_value = update.message.text.strip()
    
    # Validate input based on field type
    try:
        if field_name == "port":
            new_value = int(new_value)
            if new_value < 1 or new_value > 65535:
                raise ValueError("Port must be between 1 and 65535")
        elif field_name == "trafficLimitBytes":
            new_value = parse_bytes(new_value)
        elif field_name == "consumptionMultiplier":
            new_value = float(new_value)
            if new_value <= 0:
                raise ValueError("Consumption multiplier must be positive")
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Неверный формат: {e}\n"
            f"Попробуйте еще раз.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Отмена", callback_data="cancel_edit_field")
            ]])
        )
        return EDIT_NODE_FIELD
    
    # Update the value
    if "edit_node_data" not in context.user_data:
        context.user_data["edit_node_data"] = {}
    
    context.user_data["edit_node_data"][field_name] = new_value
    
    # Mark as modified
    if "modified_fields" not in context.user_data:
        context.user_data["modified_fields"] = set()
    context.user_data["modified_fields"].add(field_name)
    
    # Show success and return to edit menu
    uuid = context.user_data.get("edit_node_uuid")
    
    success_message = f"✅ Поле *{field_info['display_name']}* обновлено"
    if field_name == "trafficLimitBytes":
        display_value = format_bytes(new_value)
    else:
        display_value = str(new_value)
    success_message += f" на: {escape_markdown(display_value)}"
    
    keyboard = [[InlineKeyboardButton("🔙 К редактированию", callback_data=f"edit_node_{uuid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        success_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return EDIT_NODE_FIELD

async def save_node_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save changes to the node via API"""
    uuid = context.user_data.get("edit_node_uuid")
    modified_fields = context.user_data.get("modified_fields", set())
    node_data = context.user_data.get("edit_node_data", {})
    
    if not modified_fields:
        await update.callback_query.answer("ℹ️ Нет изменений для сохранения")
        return EDIT_NODE_FIELD
    
    try:
        await update.callback_query.answer("⏳ Сохранение изменений...")
        
        # Prepare data for API (only modified fields)
        api_data = {}
        for field_name in modified_fields:
            if field_name in node_data:
                api_data[field_name] = node_data[field_name]
        
        response = await NodeAPI.update_node(uuid, api_data)
        
        if response and 'response' in response:
            # Clear edit data
            context.user_data.pop("edit_node_data", None)
            context.user_data.pop("edit_node_uuid", None)
            context.user_data.pop("edit_field_name", None)
            context.user_data.pop("modified_fields", None)
            
            # Show node details
            from modules.handlers.nodes.node_details import show_node_details
            return await show_node_details(update, context, uuid)
        else:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"edit_node_{uuid}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Ошибка при сохранении изменений. Попробуйте еще раз.",
                reply_markup=reply_markup
            )
    
    except Exception as e:
        logger.error(f"Error saving node changes: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"edit_node_{uuid}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при сохранении: {str(e)}",
            reply_markup=reply_markup
        )
    
    return EDIT_NODE_FIELD
