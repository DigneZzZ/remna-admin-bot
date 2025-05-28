# Host API Methods Documentation (Official Remnawave API v1.6.5)

## Официальные методы HostAPI

### Основные CRUD операции
- `get_all_hosts()` - Получить все хосты
- `get_host_by_uuid(uuid)` - Получить хост по UUID
- `create_host(data)` - Создать новый хост
- `update_host(data)` - Обновить хост (требует uuid в data)
- `delete_host(uuid)` - Удалить хост по UUID

### Управление порядком
- `reorder_hosts(hosts_data)` - Изменить порядок хостов

### Официальные массовые операции
- `bulk_delete_hosts(uuids)` - Массовое удаление хостов
- `bulk_enable_hosts(uuids)` - Массовое включение хостов
- `bulk_disable_hosts(uuids)` - Массовое отключение хостов
- `bulk_set_inbound_to_hosts(uuids, inbound_uuid)` - Установить inbound для хостов
- `bulk_set_port_to_hosts(uuids, port)` - Установить порт для хостов

### Вспомогательные методы для одиночных операций
- `enable_host(uuid)` - Включить хост
- `disable_host(uuid)` - Отключить хост
- `set_host_inbound(uuid, inbound_uuid)` - Установить inbound для хоста
- `set_host_port(uuid, port)` - Установить порт для хоста

### Фильтрация и поиск (клиентская фильтрация)
- `get_hosts_by_inbound(inbound_uuid)` - Получить хосты по inbound UUID
- `get_enabled_hosts()` - Получить включенные хосты
- `get_disabled_hosts()` - Получить отключенные хосты
- `search_hosts_by_remark(query)` - Поиск хостов по описанию
- `search_hosts_by_address(query)` - Поиск хостов по адресу

### Валидация и утилиты
- `validate_host_data(data)` - Валидация данных хоста
- `create_host_template(inbound_uuid, remark, address, port, **kwargs)` - Создать шаблон хоста

## Структура данных хоста (официальная)

### Обязательные поля для создания:
```python
{
    "inboundUuid": "uuid-string",      # UUID inbound'а
    "remark": "Host description",       # Описание (макс 40 символов)
    "address": "example.com",           # Адрес хоста
    "port": 443                         # Порт (integer)
}
```

### Опциональные поля:
```python
{
    "path": "/path",                    # Путь
    "sni": "example.com",              # Server Name Indication
    "host": "example.com",             # Host заголовок
    "alpn": "h2",                      # ALPN: h3, h2, http/1.1, h2,http/1.1, h3,h2,http/1.1, h3,h2
    "fingerprint": "chrome",           # chrome, firefox, safari, ios, android, edge, qq, random, randomized
    "allowInsecure": false,            # Разрешить небезопасные соединения
    "isDisabled": false,               # Статус отключения
    "securityLayer": "DEFAULT",        # DEFAULT, TLS, NONE
    "xHttpExtraParams": {}             # Дополнительные HTTP параметры
}
```

### Поля ответа API:
```python
{
    "uuid": "host-uuid",
    "inboundUuid": "inbound-uuid",
    "viewPosition": 1,
    "remark": "Host description",
    "address": "example.com",
    "port": 443,
    "path": "/path",
    "sni": "example.com",
    "host": "example.com", 
    "alpn": "h2",
    "fingerprint": "chrome",
    "allowInsecure": false,
    "isDisabled": false,
    "securityLayer": "DEFAULT",
    "xHttpExtraParams": {}
}
```

## Примеры использования

### Создание хоста с валидацией
```python
# Создание данных хоста
host_data = HostAPI.create_host_template(
    inbound_uuid="550e8400-e29b-41d4-a716-446655440000",
    remark="Production Host",
    address="example.com",
    port=443,
    sni="example.com",
    alpn="h2",
    fingerprint="chrome",
    securityLayer="TLS"
)

# Валидация данных
is_valid, error = HostAPI.validate_host_data(host_data)
if is_valid:
    result = await HostAPI.create_host(host_data)
    print("Host created successfully")
else:
    print(f"Validation error: {error}")
```

### Обновление хоста
```python
update_data = {
    "uuid": "host-uuid",
    "remark": "Updated Host",
    "port": 8080,
    "isDisabled": False
}

# Валидация (проверяем только изменяемые поля)
if update_data.get('port'):
    port = update_data['port']
    if not isinstance(port, int) or port < 1 or port > 65535:
        print("Invalid port number")
    else:
        result = await HostAPI.update_host(update_data)
```

### Массовые операции
```python
# Включить несколько хостов
host_uuids = ["uuid1", "uuid2", "uuid3"]
result = await HostAPI.bulk_enable_hosts(host_uuids)

# Установить inbound для хостов
await HostAPI.bulk_set_inbound_to_hosts(host_uuids, "inbound-uuid")

# Установить порт для хостов (с валидацией)
new_port = 443
if 1 <= new_port <= 65535:
    await HostAPI.bulk_set_port_to_hosts(host_uuids, new_port)
```

### Изменение порядка хостов
```python
hosts_order = [
    {"uuid": "host-uuid-1", "viewPosition": 1},
    {"uuid": "host-uuid-2", "viewPosition": 2},
    {"uuid": "host-uuid-3", "viewPosition": 3}
]
result = await HostAPI.reorder_hosts(hosts_order)
```

### Поиск и фильтрация
```python
# Поиск по описанию
results = await HostAPI.search_hosts_by_remark("prod")

# Получить хосты по inbound
hosts = await HostAPI.get_hosts_by_inbound("inbound-uuid")

# Получить только включенные хосты
enabled = await HostAPI.get_enabled_hosts()
```

## API Endpoints (из официальной документации)

### Основные endpoints:
- `GET /api/hosts` - Получить все хосты
- `POST /api/hosts` - Создать хост
- `PATCH /api/hosts` - Обновить хост
- `GET /api/hosts/{uuid}` - Получить хост по UUID
- `DELETE /api/hosts/{uuid}` - Удалить хост

### Массовые операции:
- `POST /api/hosts/bulk/delete` - Массовое удаление
- `POST /api/hosts/bulk/enable` - Массовое включение
- `POST /api/hosts/bulk/disable` - Массовое отключение
- `POST /api/hosts/bulk/set-inbound` - Установить inbound
- `POST /api/hosts/bulk/set-port` - Установить порт

### Управление порядком:
- `POST /api/hosts/actions/reorder` - Изменить порядок

## Примечания
- Все методы асинхронные и используют `RemnaAPI` клиент
- UUID параметры обязательны для операций с конкретными хостами
- Методы возвращают JSON ответы от API в формате `{"response": data}`
- Обработка ошибок происходит на уровне `RemnaAPI` клиента
- Поиск и фильтрация выполняются на стороне клиента
- Валидация данных помогает избежать ошибок перед отправкой запросов
- Все эндпоинты требуют авторизации через `Authorization` заголовок