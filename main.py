import os
import logging
from dotenv import load_dotenv

# Setup logging first, before any other imports
def setup_logging():
    """Setup logging configuration from environment variables"""
    # Load environment variables first
    load_dotenv()
    
    # Get log level from environment variable
    log_level = os.getenv("LOG_LEVEL", "ERROR").upper()
    
    # Map string log levels to logging constants
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    # Set the log level, default to ERROR if invalid level provided
    level = log_levels.get(log_level, logging.ERROR)
    
    # Configure basic logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=level,
        force=True,  # Override any existing logging configuration
        handlers=[
            logging.StreamHandler()  # Ensure logs go to stdout
        ]
    )
    
    # Also configure a custom handler to ensure logs go to stdout
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setStream(sys.stdout)
    
    # Force flush to ensure logs are written
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Test logging configuration
    test_logger = logging.getLogger('test')
    test_logger.info("Logging system initialized successfully")
    test_logger.warning("Warning logging enabled")
    test_logger.error("Error logging enabled")
    
    # Force flush again
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Configure telegram library logging
    # For production (ERROR), disable telegram debug logs
    # For development (DEBUG/INFO), allow telegram logs
    if level <= logging.INFO:
        logging.getLogger('telegram').setLevel(logging.INFO)
        logging.getLogger('telegram.ext').setLevel(logging.INFO)
    else:
        logging.getLogger('telegram').setLevel(logging.ERROR)
        logging.getLogger('telegram.ext').setLevel(logging.ERROR)
    
    return level

# Setup logging immediately
current_log_level = setup_logging()
logger = logging.getLogger(__name__)

# Test logging configuration
logger.info("Logging system initialized")
logger.debug("Debug logging enabled")
logger.warning("Warning logging enabled")
logger.error("Error logging enabled")

# Force flush to ensure logs are written
import sys
sys.stdout.flush()
sys.stderr.flush()

from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters

# Import modules
from modules.handlers.core.conversation import create_conversation_handler


def main():
    # Load environment variables
    load_dotenv()
    
    logger.info("Starting RemnaWave Telegram Bot...")
    
    # Check if required environment variables are set
    api_token = os.getenv("REMNAWAVE_API_TOKEN")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_user_ids = [int(id) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id]
    
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
    logger.info(f"Log level: {os.getenv('LOG_LEVEL', 'ERROR')}")
    logger.info(f"Admin user IDs: {admin_user_ids}")
    
    # Force flush to ensure logs are written
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
      # Environment check - only errors in production
    if not api_token:
        logger.error("REMNAWAVE_API_TOKEN environment variable is not set")
        return

    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set")
        return

    if not admin_user_ids:
        logger.error("ADMIN_USER_IDS environment variable is not set. No users will be able to use the bot.")
        return
    # Create the Application
    logger.info("Creating Telegram Application...")
    application = Application.builder().token(bot_token).build()
    logger.info("Telegram Application created successfully")
    
    # Cache cleanup will be handled automatically by the cache TTL mechanism
    logger.info("Cache system initialized")
    
    # Create and add conversation handler
    logger.info("Creating conversation handler...")
    conv_handler = create_conversation_handler()
    application.add_handler(conv_handler, group=0)
    logger.info("Conversation handler added successfully")
    
    # Run polling with retry logic
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Starting bot polling (attempt {retry_count + 1}/{max_retries})")
            logger.info("Bot configuration:")
            logger.info(f"  - Poll interval: 5.0s")
            logger.info(f"  - Timeout: 30s")
            logger.info(f"  - Bootstrap retries: 5")
            logger.info(f"  - Drop pending updates: True")
            
            # Run polling - production configuration
            application.run_polling(
                poll_interval=5.0,
                timeout=30,
                bootstrap_retries=5,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=30,
                drop_pending_updates=True
            )
            logger.info("Bot polling started successfully")
            break  # If successful, exit the retry loop
        except Exception as e:
            retry_count += 1
            logger.error(f"Error during polling (attempt {retry_count}/{max_retries}): {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            
            if retry_count >= max_retries:
                logger.error(f"Max retries reached. Bot failed to start after {max_retries} attempts.")
                raise
            
            # Wait before retrying
            import time
            wait_time = min(30 * retry_count, 300)  # Exponential backoff, max 5 minutes
            logger.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass  # Graceful shutdown
    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)

