from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    ConversationHandler
)
from telegram import Update
from telegram.ext import ContextTypes
import logging
import warnings

# Подавляем предупреждение PTBUserWarning о per_message=False с CallbackQueryHandler
warnings.filterwarnings("ignore", message=".*?per_message=False.*?CallbackQueryHandler", category=UserWarning)

from modules.config import (
    MAIN_MENU, USER_MENU, NODE_MENU, STATS_MENU, HOST_MENU, INBOUND_MENU,
    SELECTING_USER, WAITING_FOR_INPUT, CONFIRM_ACTION,
    EDIT_USER, EDIT_USER_FIELD, EDIT_VALUE,
    CREATE_USER, CREATE_USER_FIELD,
    BULK_MENU, BULK_ACTION, BULK_CONFIRM,
    EDIT_NODE, EDIT_NODE_FIELD,
    CREATE_NODE, NODE_NAME, NODE_ADDRESS, NODE_PORT, NODE_TLS, SELECT_INBOUNDS,
    EDIT_HOST, EDIT_HOST_FIELD, CREATE_HOST,
    EDIT_INBOUND, EDIT_INBOUND_FIELD, CREATE_INBOUND,
    SEARCH_USERS, SEARCH_NODES, SEARCH_HOSTS, SEARCH_INBOUNDS
)
from modules.utils.auth import check_authorization

# Main handlers
from modules.handlers.start_handler import start
from modules.handlers.menu_handler import handle_menu_selection

# User handlers - main file
from modules.handlers.user_handlers import (
    handle_users_menu, handle_text_input
)

# User handlers - sub-modules
from modules.handlers.users.user_list import handle_user_selection
from modules.handlers.users.user_details import handle_user_action
from modules.handlers.users.user_edit import handle_edit_field_selection, handle_edit_field_value
from modules.handlers.users.user_create import handle_create_user_input
from modules.handlers.users.user_actions import handle_action_confirmation
from modules.handlers.users.user_delete import handle_delete_confirmation
from modules.handlers.users.user_hwid import handle_hwid_input

# Other handlers
from modules.handlers.node_handlers import (
    handle_nodes_menu, handle_node_edit_menu, handle_node_field_input, handle_cancel_node_edit,
    handle_node_creation, show_node_certificate
)
from modules.handlers.stats_handlers import handle_stats_menu
from modules.handlers.host_handlers import (
    handle_hosts_menu, handle_host_edit_menu, handle_host_field_input, handle_cancel_host_edit,
    handle_create_host
)
from modules.handlers.inbound_handlers import (
    handle_inbounds_menu, handle_inbound_edit_menu, handle_inbound_field_input, 
    handle_cancel_inbound_edit, handle_create_inbound
)
from modules.handlers.bulk_handlers import handle_bulk_menu, handle_bulk_action, handle_bulk_confirm

logger = logging.getLogger(__name__)

async def unauthorized_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unauthorized access attempts"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Проверяем авторизацию
    if not check_authorization(update.effective_user):
        logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
        
        if update.message:
            await update.message.reply_text("⛔ Вы не авторизованы для использования этого бота.")
        elif update.callback_query:
            await update.callback_query.answer("⛔ Вы не авторизованы для использования этого бота.", show_alert=True)
        
        return ConversationHandler.END
    
    # Если пользователь авторизован, но попал в fallback, перенаправляем на главное меню
    return await start(update, context)

def create_conversation_handler():
    """Create the main conversation handler with improved structure"""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # ============= MAIN MENUS =============
            MAIN_MENU: [
                CallbackQueryHandler(handle_menu_selection)
            ],
            USER_MENU: [
                CallbackQueryHandler(handle_users_menu)
            ],
            NODE_MENU: [
                CallbackQueryHandler(show_node_certificate, pattern="^show_certificate_"),
                CallbackQueryHandler(show_node_certificate, pattern="^get_panel_certificate$"),
                CallbackQueryHandler(handle_nodes_menu)
            ],
            STATS_MENU: [
                CallbackQueryHandler(handle_stats_menu)
            ],
            HOST_MENU: [
                CallbackQueryHandler(handle_hosts_menu)
            ],
            INBOUND_MENU: [
                CallbackQueryHandler(handle_inbounds_menu)
            ],
            
            # ============= USER OPERATIONS =============
            SELECTING_USER: [
                CallbackQueryHandler(handle_user_action, pattern="^user_action_"),
                CallbackQueryHandler(handle_user_selection)
            ],
            WAITING_FOR_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
            ],
            CONFIRM_ACTION: [
                CallbackQueryHandler(handle_action_confirmation)
            ],
            
            # User editing
            EDIT_USER: [
                CallbackQueryHandler(handle_edit_field_selection)
            ],
            EDIT_USER_FIELD: [
                CallbackQueryHandler(handle_edit_field_value),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_field_value)
            ],
            EDIT_VALUE: [
                CallbackQueryHandler(handle_edit_field_value),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_field_value)
            ],
            
            # User creation
            CREATE_USER: [
                CallbackQueryHandler(handle_create_user_input)
            ],
            CREATE_USER_FIELD: [
                CallbackQueryHandler(handle_create_user_input),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_user_input)
            ],
            
            # ============= BULK OPERATIONS =============
            BULK_MENU: [
                CallbackQueryHandler(handle_bulk_menu)
            ],
            BULK_ACTION: [
                CallbackQueryHandler(handle_bulk_action)
            ],
            BULK_CONFIRM: [
                CallbackQueryHandler(handle_bulk_confirm)
            ],
            
            # ============= NODE OPERATIONS =============
            EDIT_NODE: [
                CallbackQueryHandler(handle_node_edit_menu),
                CallbackQueryHandler(handle_cancel_node_edit, pattern="^cancel_edit_node_")
            ],
            EDIT_NODE_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_field_input),
                CallbackQueryHandler(handle_cancel_node_edit, pattern="^cancel_edit_node_")
            ],
            
            # Node creation states
            CREATE_NODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_creation),
                CallbackQueryHandler(handle_node_creation, pattern="^cancel_create_node$"),
            ],
            NODE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_creation),
                CallbackQueryHandler(handle_node_creation, pattern="^cancel_create_node$"),
            ],
            NODE_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_creation),
                CallbackQueryHandler(handle_node_creation, pattern="^cancel_create_node$"),
            ],
            NODE_PORT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_creation),
                CallbackQueryHandler(handle_node_creation, pattern="^(cancel_create_node|use_port_3000)$"),
            ],
            NODE_TLS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_node_creation),
                CallbackQueryHandler(handle_node_creation, pattern="^(cancel_create_node|skip_tls|use_panel_cert)$"),
            ],
            SELECT_INBOUNDS: [
                CallbackQueryHandler(show_node_certificate, pattern="^show_certificate_"),
                CallbackQueryHandler(show_node_certificate, pattern="^get_panel_certificate$"),
                CallbackQueryHandler(handle_node_creation, pattern="^(select_inbound_|remove_inbound_|finish_node_creation|cancel_create_node)"),
            ],
            
            # ============= HOST OPERATIONS =============
            EDIT_HOST: [
                CallbackQueryHandler(handle_host_edit_menu),
                CallbackQueryHandler(handle_cancel_host_edit, pattern="^ceh_")
            ],
            EDIT_HOST_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_host_field_input),
                CallbackQueryHandler(handle_cancel_host_edit, pattern="^ceh_")
            ],
            CREATE_HOST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_host),
                CallbackQueryHandler(handle_create_host, pattern="^(cancel_create_host|create_host_)"),
            ],
            
            # ============= INBOUND OPERATIONS =============
            EDIT_INBOUND: [
                CallbackQueryHandler(handle_inbound_edit_menu),
                CallbackQueryHandler(handle_cancel_inbound_edit, pattern="^cei_")
            ],
            EDIT_INBOUND_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_inbound_field_input),
                CallbackQueryHandler(handle_cancel_inbound_edit, pattern="^cei_")
            ],
            CREATE_INBOUND: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_create_inbound),
                CallbackQueryHandler(handle_create_inbound, pattern="^(cancel_create_inbound|create_inbound_)"),
            ],
            
            # ============= SEARCH OPERATIONS =============
            SEARCH_USERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input),
                CallbackQueryHandler(handle_users_menu, pattern="^back_to_users$")
            ],
            SEARCH_NODES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input),
                CallbackQueryHandler(handle_nodes_menu, pattern="^back_to_nodes$")
            ],
            SEARCH_HOSTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input),
                CallbackQueryHandler(handle_hosts_menu, pattern="^back_to_hosts$")
            ],
            SEARCH_INBOUNDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input),
                CallbackQueryHandler(handle_inbounds_menu, pattern="^back_to_inbounds$")
            ],
        },
        fallbacks=[
            CommandHandler("start", unauthorized_handler),
            CommandHandler("help", start),  # Help также ведет на главное меню
            MessageHandler(filters.TEXT, unauthorized_handler),
            CallbackQueryHandler(unauthorized_handler)
        ],
        name="remnawave_admin_conversation",
        persistent=False,
        per_chat=True,
        per_user=True,
        per_message=False,
        # Добавляем обработку ошибок
        block=False
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in conversation"""
    logger.error(f"Error in conversation: {context.error}")
    
    # Попытаемся отправить пользователю сообщение об ошибке
    try:
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Произошла ошибка. Попробуйте /start для перезапуска."
            )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")
    
    return ConversationHandler.END

def setup_conversation_handler(application):
    """Setup conversation handler with error handling"""
    conv_handler = create_conversation_handler()
    application.add_handler(conv_handler)
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Conversation handler setup completed")
    return conv_handler