from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "ru": "Русский",
    "en": "English",
}

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"
_USER_LANGUAGE: Dict[int, str] = {}
_CHAT_LANGUAGE: Dict[int, str] = {}


def remember_language(user_id: Optional[int], chat_id: Optional[int], language: str) -> None:
    if user_id is not None:
        _USER_LANGUAGE[user_id] = language
    if chat_id is not None:
        _CHAT_LANGUAGE[chat_id] = language


def resolve_language(user_id: Optional[int], chat_id: Optional[int]) -> str:
    if user_id is not None and user_id in _USER_LANGUAGE:
        return _USER_LANGUAGE[user_id]
    if chat_id is not None and chat_id in _CHAT_LANGUAGE:
        return _CHAT_LANGUAGE[chat_id]
    return DEFAULT_LANGUAGE


@lru_cache()
def _load_language_map(language: str) -> Dict[str, Any]:
    if language == DEFAULT_LANGUAGE:
        return {"map": {}, "keys": ()}

    locale_file = _LOCALES_DIR / f"{language}.json"
    if not locale_file.exists():
        return {"map": {}, "keys": ()}

    data = json.loads(locale_file.read_text(encoding="utf-8"))
    keys = tuple(sorted(data.keys(), key=len, reverse=True))
    return {"map": data, "keys": keys}


def translate_text(text: Optional[str], language: Optional[str] = None) -> Optional[str]:
    if text is None:
        return None
    language = language or DEFAULT_LANGUAGE
    if language == DEFAULT_LANGUAGE:
        return text

    lang_data = _load_language_map(language)
    result = text
    for key in lang_data["keys"]:
        if key and key in result:
            result = result.replace(key, lang_data["map"][key])
    return result


def _translate_markup_for_language(
    markup: Optional[InlineKeyboardMarkup], language: str
) -> Optional[InlineKeyboardMarkup]:
    if markup is None or language == DEFAULT_LANGUAGE:
        return markup

    new_keyboard = []
    for row in markup.inline_keyboard:
        new_row = []
        for button in row:
            kwargs = {
                "callback_data": button.callback_data,
                "url": button.url,
                "switch_inline_query": button.switch_inline_query,
                "switch_inline_query_current_chat": button.switch_inline_query_current_chat,
                "callback_game": button.callback_game,
                "pay": button.pay,
                "login_url": button.login_url,
                "web_app": button.web_app,
            }
            filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            new_text = translate_text(button.text, language)
            new_row.append(InlineKeyboardButton(new_text, **filtered_kwargs))
        new_keyboard.append(new_row)
    return InlineKeyboardMarkup(new_keyboard)


def get_user_language(context: Optional[Any]) -> str:
    if context is None:
        return DEFAULT_LANGUAGE
    language = context.user_data.get("language") if hasattr(context, "user_data") else None
    if language:
        return language
    user_id = getattr(context, "_user_id", None)
    chat_id = getattr(context, "_chat_id", None)
    return resolve_language(user_id, chat_id)


def set_user_language(
    context: Any,
    language: str,
    *,
    update: Optional[Any] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
) -> None:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")

    if hasattr(context, "user_data"):
        context.user_data["language"] = language

    if update is not None:
        if getattr(update, "effective_user", None) is not None:
            user_id = update.effective_user.id
        if getattr(update, "effective_chat", None) is not None:
            chat_id = update.effective_chat.id

    if user_id is None:
        user_id = getattr(context, "_user_id", None)
    if chat_id is None:
        chat_id = getattr(context, "_chat_id", None)

    remember_language(user_id, chat_id, language)


def localize_text(context: Optional[Any], text: Optional[str], language: Optional[str] = None) -> Optional[str]:
    if text is None:
        return None
    language = language or get_user_language(context)
    return translate_text(text, language)


def localize_markup(
    context: Optional[Any], markup: Optional[InlineKeyboardMarkup], language: Optional[str] = None
) -> Optional[InlineKeyboardMarkup]:
    if markup is None:
        return None
    language = language or get_user_language(context)
    return _translate_markup_for_language(markup, language)


def localize_keyboard(
    context: Optional[Any],
    keyboard: Optional[Iterable[Iterable[InlineKeyboardButton]]],
    language: Optional[str] = None,
) -> Optional[Iterable[Iterable[InlineKeyboardButton]]]:
    if keyboard is None:
        return None
    language = language or get_user_language(context)
    if language == DEFAULT_LANGUAGE:
        return keyboard

    translated_rows = []
    for row in keyboard:
        translated_row = []
        for button in row:
            kwargs = {
                "callback_data": button.callback_data,
                "url": button.url,
                "switch_inline_query": button.switch_inline_query,
                "switch_inline_query_current_chat": button.switch_inline_query_current_chat,
                "callback_game": button.callback_game,
                "pay": button.pay,
                "login_url": button.login_url,
                "web_app": button.web_app,
            }
            filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            new_text = translate_text(button.text, language)
            translated_row.append(InlineKeyboardButton(new_text, **filtered_kwargs))
        translated_rows.append(translated_row)
    return translated_rows


_original_reply_text = Message.reply_text


async def _localized_reply_text(self: Message, text: Optional[str] = None, *args: Any, **kwargs: Any):
    language = resolve_language(
        self.from_user.id if getattr(self, "from_user", None) else None,
        self.chat_id,
    )
    localized_text = translate_text(text, language)
    if "reply_markup" in kwargs:
        kwargs["reply_markup"] = _translate_markup_for_language(kwargs["reply_markup"], language)
    return await _original_reply_text(self, localized_text, *args, **kwargs)


Message.reply_text = _localized_reply_text  # type: ignore[assignment]


_original_edit_message_text = CallbackQuery.edit_message_text


async def _localized_edit_message_text(
    self: CallbackQuery, text: Optional[str] = None, *args: Any, **kwargs: Any
):
    chat_id = self.message.chat_id if getattr(self, "message", None) else None
    language = resolve_language(
        self.from_user.id if getattr(self, "from_user", None) else None,
        chat_id,
    )
    localized_text = translate_text(text, language)
    if "reply_markup" in kwargs:
        kwargs["reply_markup"] = _translate_markup_for_language(kwargs["reply_markup"], language)
    return await _original_edit_message_text(self, localized_text, *args, **kwargs)


CallbackQuery.edit_message_text = _localized_edit_message_text  # type: ignore[assignment]


_original_edit_message_caption = CallbackQuery.edit_message_caption


async def _localized_edit_message_caption(
    self: CallbackQuery, caption: Optional[str] = None, *args: Any, **kwargs: Any
):
    chat_id = self.message.chat_id if getattr(self, "message", None) else None
    language = resolve_language(
        self.from_user.id if getattr(self, "from_user", None) else None,
        chat_id,
    )
    localized_caption = translate_text(caption, language)
    if "reply_markup" in kwargs:
        kwargs["reply_markup"] = _translate_markup_for_language(kwargs["reply_markup"], language)
    return await _original_edit_message_caption(self, localized_caption, *args, **kwargs)


CallbackQuery.edit_message_caption = _localized_edit_message_caption  # type: ignore[assignment]


_original_answer = CallbackQuery.answer


async def _localized_answer(self: CallbackQuery, text: Optional[str] = None, *args: Any, **kwargs: Any):
    chat_id = self.message.chat_id if getattr(self, "message", None) else None
    language = resolve_language(
        self.from_user.id if getattr(self, "from_user", None) else None,
        chat_id,
    )
    localized_text = translate_text(text, language) if text else text
    return await _original_answer(self, localized_text, *args, **kwargs)


CallbackQuery.answer = _localized_answer  # type: ignore[assignment]
