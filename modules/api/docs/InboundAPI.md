# Inbound API Methods Documentation (Official Remnawave API v1.6.5)

## Официальные методы InboundAPI

### Основные CRUD операции
- `get_all_inbounds()` - Получить все inbound'ы
- `get_inbound_by_uuid(uuid)` - Получить inbound по UUID
- `create_inbound(data)` - Создать новый inbound
- `update_inbound(data)` - Обновить inbound (требует uuid в data)
- `delete_inbound(uuid)` - Удалить inbound по UUID

### Управление состоянием
- `enable_inbound(uuid)` - Включить inbound
- `disable_inbound(uuid)` - Отключить inbound
- `restart_inbound(uuid)` - Перезапустить inbound

### Управление порядком
- `reorder_inbounds(inbounds_data)` - Изменить порядок inbound'ов

### Официальные массовые операции
- `bulk_delete_inbounds(uuids)` - Массовое удаление inbound'ов
- `bulk_enable_inbounds(uuids)` - Массовое включение inbound'ов
- `bulk_disable_inbounds(uuids)` - Массовое отключение inbound'ов
- `bulk_restart_inbounds(uuids)` - Массовый перезапуск inbound'ов

### Операции с пользователями
- `add_inbound_to_users(inbound_uuid, user_uuids)` - Добавить inbound к пользователям
- `remove_inbound_from_users(inbound_uuid, user_uuids)` - Удалить inbound у пользователей
- `add_inbound_to_user(inbound_uuid, user_uuid)` - Добавить inbound к пользователю
- `remove_inbound_from_user(inbound_uuid, user_uuid)` - Удалить inbound у пользователя

### Операции с нодами
- `add_inbound_to_nodes(inbound_uuid, node_uuids)` - Добавить inbound к нодам
- `remove_inbound_from_nodes(inbound_uuid, node_uuids)` - Удалить inbound у нод
- `add_inbound_to_node(inbound_uuid, node_uuid)` - Добавить inbound к ноде
- `remove_inbound_from_node(inbound_uuid, node_uuid)` - Удалить inbound у ноды

### Получение связанных данных
- `get_inbound_users(inbound_uuid)` - Получить пользователей inbound'а
- `get_inbound_nodes(inbound_uuid)` - Получить ноды inbound'а
- `get_inbound_hosts(inbound_uuid)` - Получить хосты inbound'а

### Фильтрация и поиск (клиентская фильтрация)
- `get_inbounds_by_protocol(protocol)` - Получить inbound'ы по протоколу
- `get_enabled_inbounds()` - Получить включенные inbound'ы
- `get_disabled_inbounds()` - Получить отключенные inbound'ы
- `search_inbounds_by_tag(query)` - Поиск inbound'ов по тегу
- `get_inbounds_by_port_range(min_port, max_port)` - Получить inbound'ы в диапазоне портов

### Валидация и утилиты
- `validate_inbound_data(data)` - Валидация данных inbound'а
- `create_inbound_template(tag, protocol, port, **kwargs)` - Создать базовый шаблон
- `create_vless_inbound(tag, port, **kwargs)` - Создать VLESS inbound
- `create_vmess_inbound(tag, port, **kwargs)` - Создать VMess inbound
- `create_trojan_inbound(tag, port, **kwargs)` - Создать Trojan inbound
- `create_shadowsocks_inbound(tag, port, method, **kwargs)` - Создать Shadowsocks inbound

## Структура данных inbound (официальная)

### Обязательные поля для создания:
```python
{
    "tag": "inbound-name",           # Имя/тег inbound'а
    "protocol": "vless",             # Протокол: vless, vmess, trojan, shadowsocks
    "port": 443,                     # Порт (integer, 1-65535)
    "listen": "0.0.0.0"              # Адрес прослушивания (по умолчанию)
}
```

### Опциональные поля:
```python
{
    "settings": {},                  # Настройки протокола
    "streamSettings": {},            # Настройки потока
    "sniffing": {},                  # Настройки сниффинга
    "allocate": {}                   # Настройки выделения портов
}
```

### Поля ответа API:
```python
{
    "uuid": "inbound-uuid",
    "viewPosition": 1,
    "tag": "inbound-name",
    "protocol": "vless",
    "port": 443,
    "listen": "0.0.0.0",
    "settings": {},
    "streamSettings": {},
    "sniffing": {},
    "allocate": {},
    "isDisabled": false
}
```

## Примеры использования

### Создание VLESS inbound с валидацией
```python
# Создание VLESS inbound
vless_data = InboundAPI.create_vless_inbound(
    tag="Main VLESS",
    port=443,
    settings={
        "clients": [],
        "decryption": "none",
        "fallbacks": []
    },
    streamSettings={
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {
            "certificates": []
        }
    }
)

# Валидация данных
is_valid, error = InboundAPI.validate_inbound_data(vless_data)
if is_valid:
    result = await InboundAPI.create_inbound(vless_data)
    print("VLESS inbound created successfully")
else:
    print(f"Validation error: {error}")
```

### Создание VMess inbound
```python
vmess_data = InboundAPI.create_vmess_inbound(
    tag="VMess Inbound",
    port=8080,
    settings={
        "clients": [],
        "default": {
            "level": 0,
            "alterId": 0
        }
    }
)

result = await InboundAPI.create_inbound(vmess_data)
```

### Обновление inbound
```python
update_data = {
    "uuid": "inbound-uuid",
    "tag": "Updated Inbound",
    "port": 8443
}

# Валидация порта
if 1 <= update_data['port'] <= 65535:
    result = await InboundAPI.update_inbound(update_data)
```

### Массовые операции
```python
# Включить несколько inbound'ов
inbound_uuids = ["uuid1", "uuid2", "uuid3"]
result = await InboundAPI.bulk_enable_inbounds(inbound_uuids)

# Добавить inbound к пользователям
user_uuids = ["user1", "user2", "user3"]
await InboundAPI.add_inbound_to_users("inbound-uuid", user_uuids)

# Добавить inbound к нодам
node_uuids = ["node1", "node2"]
await InboundAPI.add_inbound_to_nodes("inbound-uuid", node_uuids)
```

### Изменение порядка inbound'ов
```python
inbounds_order = [
    {"uuid": "inbound-uuid-1", "viewPosition": 1},
    {"uuid": "inbound-uuid-2", "viewPosition": 2},
    {"uuid": "inbound-uuid-3", "viewPosition": 3}
]
result = await InboundAPI.reorder_inbounds(inbounds_order)
```

### Поиск и фильтрация
```python
# Поиск по тегу
results = await InboundAPI.search_inbounds_by_tag("vless")

# Получить inbound'ы по протоколу
vless_inbounds = await InboundAPI.get_inbounds_by_protocol("vless")

# Получить только включенные inbound'ы
enabled = await InboundAPI.get_enabled_inbounds()

# Получить inbound'ы в диапазоне портов
port_range = await InboundAPI.get_inbounds_by_port_range(443, 8443)
```

### Получение связанных данных
```python
# Получить пользователей inbound'а
users = await InboundAPI.get_inbound_users("inbound-uuid")

# Получить ноды inbound'а
nodes = await InboundAPI.get_inbound_nodes("inbound-uuid")

# Получить хосты inbound'а
hosts = await InboundAPI.get_inbound_hosts("inbound-uuid")
```

## API Endpoints (из официальной документации)

### Основные endpoints:
- `GET /api/inbounds` - Получить все inbound'ы
- `POST /api/inbounds` - Создать inbound
- `PATCH /api/inbounds` - Обновить inbound
- `GET /api/inbounds/{uuid}` - Получить inbound по UUID
- `DELETE /api/inbounds/{uuid}` - Удалить inbound

### Управление состоянием:
- `POST /api/inbounds/{uuid}/enable` - Включить inbound
- `POST /api/inbounds/{uuid}/disable` - Отключить inbound
- `POST /api/inbounds/{uuid}/restart` - Перезапустить inbound

### Массовые операции:
- `POST /api/inbounds/bulk/delete` - Массовое удаление
- `POST /api/inbounds/bulk/enable` - Массовое включение
- `POST /api/inbounds/bulk/disable` - Массовое отключение
- `POST /api/inbounds/bulk/restart` - Массовый перезапуск

### Операции с пользователями:
- `POST /api/inbounds/bulk/add-to-users` - Добавить к пользователям
- `POST /api/inbounds/bulk/remove-from-users` - Удалить у пользователей

### Операции с нодами:
- `POST /api/inbounds/bulk/add-to-nodes` - Добавить к нодам
- `POST /api/inbounds/bulk/remove-from-nodes` - Удалить у нод

### Управление порядком:
- `POST /api/inbounds/actions/reorder` - Изменить порядок

### Связанные данные:
- `GET /api/inbounds/{uuid}/users` - Получить пользователей
- `GET /api/inbounds/{uuid}/nodes` - Получить ноды
- `GET /api/inbounds/{uuid}/hosts` - Получить хосты

## Поддерживаемые протоколы
- **VLESS** - Современный протокол с минимальными накладными расходами
- **VMess** - Протокол V2Ray с шифрованием
- **Trojan** - Протокол маскировки под HTTPS трафик
- **Shadowsocks** - Популярный прокси-протокол

## Примечания
- Все методы асинхронные и используют `RemnaAPI` клиент
- UUID параметры обязательны для операций с конкретными inbound'ами
- Методы возвращают JSON ответы от API в формате `{"response": data}`
- Обработка ошибок происходит на уровне `RemnaAPI` клиента
- Поиск и фильтрация выполняются на стороне клиента
- Валидация данных помогает избежать ошибок перед отправкой запросов
- Все эндпоинты требуют авторизации через `Authorization` заголовок
- Утилиты для создания протокол-специфичных inbound'ов упрощают настройку