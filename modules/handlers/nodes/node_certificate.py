from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from modules.config import NODE_MENU
from modules.api.nodes import NodeAPI

logger = logging.getLogger(__name__)

async def show_node_certificate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show node certificate for copying"""
    try:
        callback_data = update.callback_query.data
        node_uuid = None
        
        logger.info(f"Certificate request with callback_data: {callback_data}")
        
        if callback_data == "get_panel_certificate":
            logger.info("Processing panel certificate request")
        elif callback_data.startswith("show_certificate_"):
            node_uuid = callback_data.replace("show_certificate_", "")
            logger.info(f"Certificate request for node: {node_uuid}")
        else:
            logger.error(f"Invalid callback_data: {callback_data}")
            await update.callback_query.edit_message_text("❌ Ошибка: неверный тип запроса.")
            return NODE_MENU
        
        await update.callback_query.edit_message_text("📜 Получение сертификата панели...")
        
        # Get certificate from API
        certificate_response = await NodeAPI.get_node_certificate()
        logger.info(f"Certificate response: {certificate_response}")
        
        if certificate_response and 'response' in certificate_response:
            cert_data = certificate_response['response']
            pub_key = cert_data.get("pubKey")
            
            if pub_key:
                logger.info(f"Certificate obtained successfully, length: {len(pub_key)}")
                
                # Create keyboard based on context
                if node_uuid:
                    keyboard = [
                        [InlineKeyboardButton("👁️ К деталям сервера", callback_data=f"view_node_{node_uuid}")],
                        [InlineKeyboardButton("🔙 К списку серверов", callback_data="list_nodes")]
                    ]
                else:
                    keyboard = [
                        [InlineKeyboardButton("🔙 К меню серверов", callback_data="back_to_nodes")]
                    ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Try different formatting approaches
                try:
                    # First attempt: code block formatting
                    message = "📜 *Сертификат панели*\n\n"
                    message += "🔐 **Переменная для настройки ноды:**\n\n"
                    message += f"```bash\nSSL_CERT=\"{pub_key}\"\n```\n\n"
                    message += "📋 **Инструкция по установке:**\n"
                    message += "1. Скопируйте SSL_CERT переменную выше\n"
                    message += "2. Добавьте её в docker-compose.yml или .env\n"
                    message += "3. Перезапустите Remnawave Node\n"
                    message += "4. Проверьте подключение к панели\n\n"
                    message += "⚠️ **Важно:** Храните сертификат в безопасности!"
                    
                    await update.callback_query.edit_message_text(
                        text=message,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    logger.info("Certificate sent with Markdown formatting")
                    
                except Exception as markdown_error:
                    logger.warning(f"Markdown failed, trying HTML: {markdown_error}")
                    
                    try:
                        # Second attempt: HTML formatting
                        message = "📜 <b>Сертификат панели</b>\n\n"
                        message += "🔐 <b>Переменная для настройки ноды:</b>\n\n"
                        message += f"<code>SSL_CERT=\"{pub_key}\"</code>\n\n"
                        message += "📋 <b>Инструкция по установке:</b>\n"
                        message += "1. Скопируйте SSL_CERT переменную выше\n"
                        message += "2. Добавьте её в docker-compose.yml или .env\n"
                        message += "3. Перезапустите Remnawave Node\n"
                        message += "4. Проверьте подключение к панели\n\n"
                        message += "⚠️ <b>Важно:</b> Храните сертификат в безопасности!"
                        
                        await update.callback_query.edit_message_text(
                            text=message,
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
                        logger.info("Certificate sent with HTML formatting")
                        
                    except Exception as html_error:
                        logger.warning(f"HTML failed, using plain text: {html_error}")
                        
                        # Final attempt: plain text
                        message = "📜 Сертификат панели\n\n"
                        message += "🔐 Переменная для настройки ноды:\n\n"
                        message += f"SSL_CERT=\"{pub_key}\"\n\n"
                        message += "📋 Инструкция по установке:\n"
                        message += "1. Скопируйте SSL_CERT переменную выше\n"
                        message += "2. Добавьте её в docker-compose.yml или .env\n"
                        message += "3. Перезапустите Remnawave Node\n"
                        message += "4. Проверьте подключение к панели\n\n"
                        message += "⚠️ Важно: Храните сертификат в безопасности!"
                        
                        await update.callback_query.edit_message_text(
                            text=message,
                            reply_markup=reply_markup,
                            parse_mode=None
                        )
                        logger.info("Certificate sent with plain text")
            else:
                raise Exception("Сертификат не найден в ответе API")
        else:
            raise Exception("Некорректный ответ от API")
        
        return NODE_MENU
        
    except Exception as e:
        logger.error(f"Error showing certificate: {e}")
        
        # Create appropriate keyboard for error case
        if 'node_uuid' in locals() and node_uuid:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"show_certificate_{node_uuid}")],
                [InlineKeyboardButton("👁️ К деталям сервера", callback_data=f"view_node_{node_uuid}")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="get_panel_certificate")],
                [InlineKeyboardButton("🔙 К меню серверов", callback_data="back_to_nodes")]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"❌ Ошибка при получении сертификата: {str(e)}",
            reply_markup=reply_markup
        )
        
        return NODE_MENU

async def show_installation_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed installation guide for Remnawave Node"""
    message = "📚 *Руководство по установке Remnawave Node*\n\n"
    message += "🐳 **Docker Compose setup:**\n"
    message += "```bash\nsudo bash -c \"$(curl -sL https://github.com/DigneZzZ/remnawave-scripts/raw/main/remnanode.sh)\" @ install\n```\n\n"
   
    message += "▶️ **Управление и информация:** `remnanode help`"
    
    keyboard = [
        [InlineKeyboardButton("📜 Получить сертификат", callback_data="get_panel_certificate")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_nodes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return NODE_MENU