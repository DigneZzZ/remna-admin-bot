from functools import wraps
from typing import Iterable, Optional

from modules.config import USER_ROLES
from telegram import Update, User
from telegram.ext import ContextTypes, ConversationHandler
import logging

logger = logging.getLogger(__name__)

NOT_AUTHORIZED_MESSAGE = "Вам недоступен этот бот. Обратитесь к администратору."
INSUFFICIENT_PERMISSIONS_MESSAGE = "Действие доступно только администраторам."

def get_user_role(user_id: int) -> Optional[str]:
    """Return configured role for the given user id."""
    return USER_ROLES.get(int(user_id))

def is_admin_user(user_id: int) -> bool:
    """Check whether the user has admin role."""
    return get_user_role(user_id) == "admin"

def is_operator_user(user_id: int) -> bool:
    """Check whether the user has operator role."""
    return get_user_role(user_id) == "operator"

def is_authorized_user(user_id: int) -> bool:
    """Return True if user has any configured role."""
    return get_user_role(user_id) is not None

def _log_request(user: User, role: Optional[str]):
    username = user.username or "Unknown"
    first_name = user.first_name or "Unknown"
    logger.info(
        "Authorization check for user %s (@%s, %s), role=%s",
        user.id, username, first_name, role or "unknown"
    )

def _reply_denied(update: Update, message: str):
    if update.callback_query:
        return update.callback_query.answer(message, show_alert=True)
    if update.message:
        return update.message.reply_text(message)
    return None

def check_roles(allowed_roles: Iterable[str]):
    """Decorator factory to enforce that user role belongs to allowed_roles."""
    allowed = set(allowed_roles)

    def decorator(func):
        @wraps(func)
        async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            role = get_user_role(user.id)
            _log_request(user, role)

            if role is None:
                logger.warning("User %s has no role configured", user.id)
                await _reply_denied(update, NOT_AUTHORIZED_MESSAGE)
                return ConversationHandler.END

            if role not in allowed:
                logger.warning("User %s with role %s attempted admin-only action", user.id, role)
                await _reply_denied(update, INSUFFICIENT_PERMISSIONS_MESSAGE)
                return ConversationHandler.END

            return await func(update, context, *args, **kwargs)

        return wrapped

    return decorator

check_admin = check_roles({"admin"})
check_operator_or_admin = check_roles({"admin", "operator"})

def check_authorization(user):
    """Check if user is authorized (without decorator)."""
    role = get_user_role(user.id)
    _log_request(user, role)

    if role is None:
        logger.warning("Unauthorized access attempt from user %s (@%s)", user.id, user.username or "Unknown")
        return False

    logger.info("User %s authorized as %s", user.id, role)
    return True
