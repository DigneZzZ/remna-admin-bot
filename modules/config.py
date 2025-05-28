import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging for config
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://remnawave:3000/api")
API_TOKEN = os.getenv("REMNAWAVE_API_TOKEN")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Parse admin user IDs with detailed logging
admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
logger.info(f"Raw ADMIN_USER_IDS from env: '{admin_ids_str}'")

ADMIN_USER_IDS = []
if admin_ids_str:
    try:
        ADMIN_USER_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
        logger.info(f"Parsed ADMIN_USER_IDS: {ADMIN_USER_IDS}")
    except ValueError as e:
        logger.error(f"Error parsing ADMIN_USER_IDS: {e}")
        ADMIN_USER_IDS = []
else:
    logger.warning("ADMIN_USER_IDS is empty or not set!")

# Conversation states - основные меню
MAIN_MENU, USER_MENU, NODE_MENU, STATS_MENU, HOST_MENU, INBOUND_MENU = range(6)

# Состояния работы с пользователями
SELECTING_USER, WAITING_FOR_INPUT, CONFIRM_ACTION = range(6, 9)
EDIT_USER, EDIT_USER_FIELD, EDIT_VALUE = range(9, 12)
CREATE_USER, CREATE_USER_FIELD = range(12, 14)

# Состояния массовых операций
BULK_MENU, BULK_ACTION, BULK_CONFIRM = range(14, 17)

# Состояния работы с нодами
SELECTING_NODE, EDIT_NODE, EDIT_NODE_FIELD = range(17, 20)
CREATE_NODE, CREATE_NODE_FIELD, NODE_NAME, NODE_ADDRESS, NODE_PORT, NODE_TLS, SELECT_INBOUNDS = range(20, 27)

# Состояния работы с хостами
EDIT_HOST, EDIT_HOST_FIELD, CREATE_HOST = range(26, 29)

# Состояния работы с inbound'ами
EDIT_INBOUND, EDIT_INBOUND_FIELD, CREATE_INBOUND = range(29, 32)

# Поисковые состояния
SEARCH_USERS, SEARCH_NODES, SEARCH_HOSTS, SEARCH_INBOUNDS = range(32, 36)

# User creation and edit fields
USER_FIELDS = {
    'username': 'Имя пользователя',
    'trafficLimitBytes': 'Лимит трафика (в байтах)',
    'trafficLimitStrategy': 'Стратегия сброса трафика (NO_RESET, DAY, WEEK, MONTH)',
    'expireAt': 'Дата истечения (YYYY-MM-DD HH:mm:ss или YYYY-MM-DD)',
    'description': 'Описание',
    'telegramId': 'Telegram ID',
    'email': 'Email',
    'tag': 'Тег',
    'hwidDeviceLimit': 'Лимит устройств HWID'
}

# Node creation and edit fields
NODE_FIELDS = {
    'name': 'Название ноды',
    'address': 'IP адрес или домен',
    'port': 'Порт подключения',
    'apiKey': 'API ключ',
    'certificate': 'TLS сертификат',
    'description': 'Описание ноды'
}

# Host creation and edit fields  
HOST_FIELDS = {
    'remark': 'Название хоста',
    'address': 'IP адрес или домен',
    'port': 'Порт',
    'path': 'Путь (WebSocket path)',
    'sni': 'SNI (Server Name Indication)', 
    'host': 'Host заголовок',
    'alpn': 'ALPN протокол',
    'fingerprint': 'TLS Fingerprint',
    'allowInsecure': 'Разрешить небезопасные соединения',
    'securityLayer': 'Уровень безопасности'
}

# Inbound creation and edit fields
INBOUND_FIELDS = {
    'remark': 'Название inbound',
    'type': 'Тип протокола',
    'port': 'Порт',
    'tag': 'Тег',
    'certificate': 'TLS сертификат',
    'host': 'Host заголовок',
    'path': 'Путь (WebSocket path)',
    'enableFragments': 'Включить фрагментацию'
}

# Traffic limit strategies
TRAFFIC_STRATEGIES = ['NO_RESET', 'DAY', 'WEEK', 'MONTH']

# User statuses
USER_STATUSES = ['ACTIVE', 'DISABLED', 'EXPIRED', 'LIMITED']

# Node statuses
NODE_STATUSES = ['CONNECTED', 'DISCONNECTED', 'ERROR']

# Inbound types
INBOUND_TYPES = ['VLESS', 'VMESS', 'TROJAN', 'SHADOWSOCKS']

# Security layers for hosts
SECURITY_LAYERS = ['DEFAULT', 'TLS', 'NONE']

# ALPN protocols
ALPN_PROTOCOLS = ['h3', 'h2', 'http/1.1', 'h2,http/1.1', 'h3,h2,http/1.1', 'h3,h2']

# TLS Fingerprints
TLS_FINGERPRINTS = ['chrome', 'firefox', 'safari', 'ios', 'android', 'edge', 'qq', 'random', 'randomized']

# Dashboard display settings - что показывать на главном экране
DASHBOARD_SHOW_SYSTEM_STATS = os.getenv("DASHBOARD_SHOW_SYSTEM_STATS", "true").lower() == "true"
DASHBOARD_SHOW_SERVER_INFO = os.getenv("DASHBOARD_SHOW_SERVER_INFO", "true").lower() == "true"
DASHBOARD_SHOW_USERS_COUNT = os.getenv("DASHBOARD_SHOW_USERS_COUNT", "true").lower() == "true"
DASHBOARD_SHOW_NODES_COUNT = os.getenv("DASHBOARD_SHOW_NODES_COUNT", "true").lower() == "true"
DASHBOARD_SHOW_TRAFFIC_STATS = os.getenv("DASHBOARD_SHOW_TRAFFIC_STATS", "true").lower() == "true"
DASHBOARD_SHOW_UPTIME = os.getenv("DASHBOARD_SHOW_UPTIME", "true").lower() == "true"
DASHBOARD_SHOW_INBOUNDS_COUNT = os.getenv("DASHBOARD_SHOW_INBOUNDS_COUNT", "true").lower() == "true"
DASHBOARD_SHOW_HOSTS_COUNT = os.getenv("DASHBOARD_SHOW_HOSTS_COUNT", "true").lower() == "true"

# Настройки поиска
ENABLE_PARTIAL_SEARCH = os.getenv("ENABLE_PARTIAL_SEARCH", "true").lower() == "true"
SEARCH_MIN_LENGTH = int(os.getenv("SEARCH_MIN_LENGTH", "2"))
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "20"))

# Настройки пагинации для списков
LIST_PAGE_SIZE = int(os.getenv("LIST_PAGE_SIZE", "10"))
MAX_LIST_ITEMS = int(os.getenv("MAX_LIST_ITEMS", "50"))

# Настройки форматирования
DATE_FORMAT = os.getenv("DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
TIMEZONE = os.getenv("TIMEZONE", "UTC")

# Настройки безопасности
REQUIRE_CONFIRMATION_FOR_DELETE = os.getenv("REQUIRE_CONFIRMATION_FOR_DELETE", "true").lower() == "true"
REQUIRE_CONFIRMATION_FOR_BULK = os.getenv("REQUIRE_CONFIRMATION_FOR_BULK", "true").lower() == "true"
ENABLE_AUDIT_LOG = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"

# Настройки уведомлений
NOTIFY_ON_ERRORS = os.getenv("NOTIFY_ON_ERRORS", "true").lower() == "true"
NOTIFY_ON_BULK_OPERATIONS = os.getenv("NOTIFY_ON_BULK_OPERATIONS", "true").lower() == "true"

# Настройки кэширования (для будущего использования)
CACHE_SYSTEM_STATS_TTL = int(os.getenv("CACHE_SYSTEM_STATS_TTL", "30"))  # секунд
CACHE_USER_LIST_TTL = int(os.getenv("CACHE_USER_LIST_TTL", "60"))  # секунд

# Лимиты для безопасности
MAX_USERNAME_LENGTH = int(os.getenv("MAX_USERNAME_LENGTH", "40"))
MAX_DESCRIPTION_LENGTH = int(os.getenv("MAX_DESCRIPTION_LENGTH", "200"))
MAX_TAG_LENGTH = int(os.getenv("MAX_TAG_LENGTH", "20"))
MIN_PORT_NUMBER = int(os.getenv("MIN_PORT_NUMBER", "1"))
MAX_PORT_NUMBER = int(os.getenv("MAX_PORT_NUMBER", "65535"))

# Настройки трафика
DEFAULT_TRAFFIC_LIMIT = int(os.getenv("DEFAULT_TRAFFIC_LIMIT", "10737418240"))  # 10GB in bytes
MAX_TRAFFIC_LIMIT = int(os.getenv("MAX_TRAFFIC_LIMIT", "1099511627776"))  # 1TB in bytes

# Валидация конфигурации при импорте
def validate_config():
    """Validate configuration values"""
    errors = []
    
    # Проверка обязательных параметров
    if not BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is required")
    
    if not API_TOKEN:
        errors.append("REMNAWAVE_API_TOKEN is required")
    
    if not API_BASE_URL:
        errors.append("API_BASE_URL is required")
    
    if not ADMIN_USER_IDS:
        errors.append("ADMIN_USER_IDS is required and must contain at least one valid user ID")
    
    # Проверка числовых параметров
    try:
        if SEARCH_MIN_LENGTH < 1:
            errors.append("SEARCH_MIN_LENGTH must be >= 1")
        
        if LIST_PAGE_SIZE < 1 or LIST_PAGE_SIZE > 50:
            errors.append("LIST_PAGE_SIZE must be between 1 and 50")
            
        if MIN_PORT_NUMBER < 1 or MIN_PORT_NUMBER > MAX_PORT_NUMBER:
            errors.append("Invalid port number range")
            
    except (ValueError, TypeError) as e:
        errors.append(f"Invalid numeric configuration: {e}")
    
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("Configuration validation passed")
    return True

# Автоматическая валидация при импорте
if __name__ != "__main__":
    validate_config()

# Convenience function для получения всех состояний
def get_all_states():
    """Get all conversation states for ConversationHandler"""
    return [
        # Main menus
        MAIN_MENU, USER_MENU, NODE_MENU, STATS_MENU, HOST_MENU, INBOUND_MENU,
        # User operations
        SELECTING_USER, WAITING_FOR_INPUT, CONFIRM_ACTION,
        EDIT_USER, EDIT_USER_FIELD, EDIT_VALUE,
        CREATE_USER, CREATE_USER_FIELD,
        # Bulk operations
        BULK_MENU, BULK_ACTION, BULK_CONFIRM,
        # Node operations
        SELECTING_NODE, EDIT_NODE, EDIT_NODE_FIELD,
        CREATE_NODE, NODE_NAME, NODE_ADDRESS, NODE_PORT, NODE_TLS, SELECT_INBOUNDS,
        # Host operations
        EDIT_HOST, EDIT_HOST_FIELD, CREATE_HOST,
        # Inbound operations
        EDIT_INBOUND, EDIT_INBOUND_FIELD, CREATE_INBOUND,
        # Search operations
        SEARCH_USERS, SEARCH_NODES, SEARCH_HOSTS, SEARCH_INBOUNDS
    ]

# Convenience function для получения полей по типу объекта
def get_fields_for_type(object_type: str) -> dict:
    """Get field definitions for object type"""
    field_maps = {
        'user': USER_FIELDS,
        'node': NODE_FIELDS,
        'host': HOST_FIELDS,
        'inbound': INBOUND_FIELDS
    }
    return field_maps.get(object_type.lower(), {})

# Convenience function для получения валидных значений
def get_valid_values(field_name: str) -> list:
    """Get valid values for specific fields"""
    value_maps = {
        'trafficLimitStrategy': TRAFFIC_STRATEGIES,
        'status': USER_STATUSES,
        'type': INBOUND_TYPES,
        'securityLayer': SECURITY_LAYERS,
        'alpn': ALPN_PROTOCOLS,
        'fingerprint': TLS_FINGERPRINTS
    }
    return value_maps.get(field_name, [])