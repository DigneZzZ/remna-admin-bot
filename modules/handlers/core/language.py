from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from modules.config import MAIN_MENU
from modules.localization import SUPPORTED_LANGUAGES, set_user_language

LANGUAGE_MENU_CALLBACK = "language_settings"
LANGUAGE_SELECT_PREFIX = "language_select_"


async def show_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display language selection options."""
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data=f"{LANGUAGE_SELECT_PREFIX}ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data=f"{LANGUAGE_SELECT_PREFIX}en")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = "🌐 Выберите язык интерфейса:"
    if query:
        await query.edit_message_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)
    return MAIN_MENU


async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Update user language based on selection and return to main menu."""
    query = update.callback_query
    if query:
        await query.answer()
        data = query.data
    else:
        return MAIN_MENU

    if not data.startswith(LANGUAGE_SELECT_PREFIX):
        return MAIN_MENU

    language = data.replace(LANGUAGE_SELECT_PREFIX, "", 1)
    if language not in SUPPORTED_LANGUAGES:
        await query.answer("❌ Неподдерживаемый язык.", show_alert=True)
        return MAIN_MENU

    set_user_language(context, language, update=update)

    confirmation = (
        "✅ Язык изменен на English." if language == "en" else "✅ Язык изменен на Русский."
    )
    await query.answer(confirmation)

    from modules.handlers.core.start import show_main_menu

    await show_main_menu(update, context)
    return MAIN_MENU
