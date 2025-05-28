from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import USER_MENU, SELECTING_USER, CONFIRM_ACTION
from modules.api.users import UserAPI
from modules.utils.formatters import format_user_details, format_user_details_safe, escape_markdown
from modules.utils.selection_helpers import SelectionHelper

logger = logging.getLogger(__name__)

async def show_user_details(update: Update, context: ContextTypes.DEFAULT_TYPE, uuid: str):
    """Show user details with improved error handling and response parsing"""
    try:
        logger.info(f"Getting user details for UUID: {uuid}")
        response = await UserAPI.get_user_by_uuid(uuid)
        
        # Check if we got any response
        if not response:
            logger.warning(f"No response for user {uuid}")
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Пользователь не найден или ошибка при получении данных.",
                reply_markup=reply_markup
            )
            return USER_MENU

        # Handle different response formats from API
        user = None
        if isinstance(response, dict):
            # Check if response is wrapped in 'response' field
            if 'response' in response:
                user = response['response']
                logger.debug(f"Found user data in 'response' field")
            # Check if response has user fields directly
            elif 'uuid' in response or 'username' in response:
                user = response
                logger.debug(f"Found user data directly in response")
            else:
                logger.warning(f"Invalid response structure: {response}")
        elif isinstance(response, list) and len(response) > 0:
            user = response[0]
            logger.debug(f"Found user data in list format")
        
        # Validate that we have user data
        if not user or not isinstance(user, dict):
            logger.warning(f"No valid user data found in response: {response}")
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "❌ Данные пользователя не найдены или имеют неверный формат.",
                reply_markup=reply_markup
            )
            return USER_MENU

        logger.info(f"Successfully parsed user data for {user.get('username', 'Unknown')}")

        # Format user details with fallback to safe formatter
        try:
            message = format_user_details(user)
            logger.info("Successfully formatted user details with full formatter")
        except Exception as e:
            logger.warning(f"Error formatting user details with full formatter: {e}")
            try:
                message = format_user_details_safe(user)
                logger.info("Successfully formatted user details with safe formatter")
            except Exception as e2:
                logger.error(f"Error in safe formatter: {e2}")
                # Fallback to basic info
                username = escape_markdown(str(user.get('username', 'N/A')))
                status = user.get('status', 'UNKNOWN')
                status_emoji = "✅" if status == "ACTIVE" else "❌" if status == "DISABLED" else "⚠️"
                message = f"👤 *Пользователь:* {username}\n🆔 *UUID:* `{uuid}`\n{status_emoji} *Статус:* {status}"

        # Create action keyboard
        keyboard = SelectionHelper.create_user_info_keyboard(uuid, action_prefix="user_action")

        # Send message with error handling for Markdown parsing
        try:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            logger.info("Successfully updated message with user details")
        except Exception as e:
            if "can't parse entities" in str(e).lower() or "parse_mode" in str(e).lower():
                logger.warning(f"Markdown parsing error, retrying without parse_mode: {e}")
                try:
                    # Remove markdown formatting and try again
                    safe_message = message.replace('*', '').replace('`', '').replace('_', '')
                    await update.callback_query.edit_message_text(
                        text=safe_message,
                        reply_markup=keyboard
                    )
                    logger.info("Successfully updated message without markdown")
                except Exception as e2:
                    logger.error(f"Error in fallback message update: {e2}")
                    # Last resort - basic message
                    basic_message = f"👤 {user.get('username', 'N/A')}\n🆔 {uuid}\n❌ Ошибка отображения форматирования"
                    await update.callback_query.edit_message_text(
                        text=basic_message,
                        reply_markup=keyboard
                    )
            else:
                logger.error(f"Non-parsing error updating message: {e}")
                await update.callback_query.answer("❌ Ошибка при отображении данных")
                return USER_MENU

        # Store user data for future actions
        if not context.user_data:
            context.user_data = {}
        context.user_data["current_user"] = user
        context.user_data["current_user_uuid"] = uuid
        
        return SELECTING_USER
        
    except Exception as e:
        logger.error(f"Critical error in show_user_details: {e}", exc_info=True)
        try:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "❌ Произошла критическая ошибка при загрузке данных пользователя.",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    "❌ Произошла критическая ошибка при загрузке данных пользователя.",
                    reply_markup=reply_markup
                )
        except Exception as fallback_error:
            logger.error(f"Error in error handler: {fallback_error}")
            
        return USER_MENU

async def handle_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user actions from inline keyboard"""
    if not update.callback_query:
        return SELECTING_USER
    
    query = update.callback_query
    await query.answer()
    data = query.data

    # Import handlers locally to avoid circular imports
    try:
        from modules.handlers.users.user_edit import start_edit_user
        from modules.handlers.users.user_delete import confirm_delete_user
        from modules.handlers.users.user_hwid import show_user_hwid_devices
        from modules.handlers.users.user_stats import show_user_stats
    except ImportError as e:
        logger.error(f"Import error in handle_user_action: {e}")
        await query.edit_message_text("❌ Ошибка загрузки модулей")
        return USER_MENU

    if data.startswith("user_action_"):
        action_parts = data.split("_", 3)  # Split into max 4 parts
        if len(action_parts) >= 4:
            action = action_parts[2]
            uuid = action_parts[3]
            
            logger.info(f"Handling user action: {action} for UUID: {uuid}")
            
            try:
                if action == "edit":
                    return await start_edit_user(update, context, uuid)
                elif action == "refresh":
                    return await show_user_details(update, context, uuid)
                elif action == "delete":
                    return await confirm_delete_user(update, context, uuid)
                elif action == "hwid":
                    return await show_user_hwid_devices(update, context, uuid)
                elif action == "stats":
                    return await show_user_stats(update, context, uuid)
                elif action in ["disable", "enable", "reset", "revoke"]:
                    return await setup_action_confirmation(update, context, action, uuid)
                else:
                    logger.warning(f"Unknown action: {action}")
                    await query.edit_message_text("❌ Неизвестное действие")
                    return USER_MENU
            except Exception as e:
                logger.error(f"Error handling action {action}: {e}")
                await query.edit_message_text("❌ Ошибка при выполнении действия")
                return USER_MENU
        else:
            logger.warning(f"Invalid action data format: {data}")
    
    # Handle back navigation
    elif data == "back_to_users":
        from modules.handlers.user_handlers import show_users_menu
        return await show_users_menu(update, context)
    
    return SELECTING_USER

async def setup_action_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, uuid: str):
    """Setup confirmation dialog for user actions"""
    if not context.user_data:
        context.user_data = {}
        
    context.user_data["pending_action"] = action
    context.user_data["pending_uuid"] = uuid
    
    # Action descriptions for user-friendly messages
    action_messages = {
        "disable": "отключить",
        "enable": "включить", 
        "reset": "сбросить трафик",
        "revoke": "отозвать подписку"
    }
    
    action_text = action_messages.get(action, action)
    
    # Get current user info for confirmation
    current_user = context.user_data.get("current_user", {})
    username = current_user.get("username", "Unknown")
    
    keyboard = [
        [
            InlineKeyboardButton(f"✅ Да, {action_text}", callback_data="confirm_user_action"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"user_action_refresh_{uuid}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"⚠️ *Подтверждение действия*\n\n"
    message += f"👤 *Пользователь:* {escape_markdown(username)}\n"
    message += f"🆔 *UUID:* `{uuid}`\n\n"
    message += f"🔄 *Действие:* {action_text}\n\n"
    message += f"Вы уверены, что хотите {action_text} этого пользователя?"
    
    try:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Markdown error in confirmation: {e}")
        # Fallback without markdown
        simple_message = f"⚠️ Подтверждение действия\n\n👤 Пользователь: {username}\n🆔 UUID: {uuid}\n\n🔄 Действие: {action_text}\n\nВы уверены?"
        await update.callback_query.edit_message_text(
            simple_message,
            reply_markup=reply_markup
        )
    
    return CONFIRM_ACTION

async def confirm_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute confirmed user action"""
    if not update.callback_query or not context.user_data:
        return USER_MENU
    
    query = update.callback_query
    await query.answer()
    
    action = context.user_data.get("pending_action")
    uuid = context.user_data.get("pending_uuid")
    
    if not action or not uuid:
        logger.error("Missing action or UUID in confirmation")
        await query.edit_message_text("❌ Ошибка: отсутствуют данные для выполнения действия")
        return USER_MENU
    
    try:
        # Execute the action
        if action == "disable":
            result = await UserAPI.disable_user(uuid)
        elif action == "enable":
            result = await UserAPI.enable_user(uuid)
        elif action == "reset":
            result = await UserAPI.reset_user_traffic(uuid)
        elif action == "revoke":
            result = await UserAPI.revoke_user_subscription(uuid)
        else:
            logger.error(f"Unknown action: {action}")
            await query.edit_message_text("❌ Неизвестное действие")
            return USER_MENU
        
        # Check result and show appropriate message
        if result:
            success_messages = {
                "disable": "отключен",
                "enable": "включен",
                "reset": "трафик сброшен",
                "revoke": "подписка отозвана"
            }
            message = f"✅ Пользователь успешно {success_messages.get(action, 'обработан')}"
            await query.edit_message_text(message)
            
            # Clear pending action data
            context.user_data.pop("pending_action", None)
            context.user_data.pop("pending_uuid", None)
            
            # Return to user details with updated info
            return await show_user_details(update, context, uuid)
        else:
            await query.edit_message_text("❌ Не удалось выполнить действие")
            return await show_user_details(update, context, uuid)
            
    except Exception as e:
        logger.error(f"Error executing action {action}: {e}")
        await query.edit_message_text("❌ Произошла ошибка при выполнении действия")
        return await show_user_details(update, context, uuid)