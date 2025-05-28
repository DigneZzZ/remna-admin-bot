# Node API Methods Documentation (Official Remnawave API v1.6.5)

## Официальные методы NodeAPI

### Основные CRUD операции
- `get_all_nodes()` - Получить все ноды
- `get_node_by_uuid(uuid)` - Получить ноду по UUID
- `create_node(data)` - Создать новую ноду
- `update_node(data)` - Обновить ноду (требует uuid в data)
- `delete_node(uuid)` - Удалить ноду по UUID

### Управление состоянием
- `enable_node(uuid)` - Включить ноду
- `disable_node(uuid)` - Отключить ноду
- `restart_node(uuid)` - Перезапустить ноду
- `restart_all_nodes()` - Перезапустить все ноды

### Управление порядком
- `reorder_nodes(nodes_data)` - Изменить порядок нод

### Официальные массовые операции
- `bulk_delete_nodes(uuids)` - Массовое удаление нод
- `bulk_enable_nodes(uuids)` - Массовое включение нод
- `bulk_disable_nodes(uuids)` - Массовое отключение нод
- `bulk_restart_nodes(uuids)` - Массовый перезапуск нод

### Управление inbound'ами
- `get_node_inbounds(uuid)` - Получить inbound'ы ноды
- `add_inbound_to_node(node_uuid, inbound_uuid)` - Добавить inbound к ноде
- `remove_inbound_from_node(node_uuid, inbound_uuid)` - Удалить inbound у ноды

### Статистика и мониторинг
- `get_node_usage_by_range(uuid, start_date, end_date)` - Получить использование ноды за период
- `get_nodes_usage_by_range(start_date, end_date)` - Получить использование всех нод за период
- `get_nodes_realtime_usage()` - Получить статистику использования в реальном времени

### Сертификаты и ключи
- `get_node_certificate()` - Получить публичный ключ панели для сертификата ноды

### Фильтрация и поиск (клиентская фильтрация)
- `get_enabled_nodes()` - Получить включенные ноды
- `get_disabled_nodes()` - Получить отключенные ноды
- `get_connected_nodes()` - Получить подключенные ноды
- `get_disconnected_nodes()` - Получить отключенные ноды
- `search_nodes_by_name(query)` - Поиск нод по имени
- `get_nodes_by_country(country_code)` - Получить ноды по коду страны

### Валидация и утилиты
- `validate_node_data(data)` - Валидация данных ноды
- `create_node_template(name, address, port, **kwargs)` - Создать шаблон ноды

### Совместимость
- `get_nodes_stats()` - Получить статистику нод (для совместимости с существующим кодом)

## Структура данных ноды (официальная)

### Обязательные поля для создания:
```python
{
    "name": "Node Name",              # Имя ноды
    "address": "node.example.com",    # Адрес ноды
    "port": 62050,                    # Порт ноды (1-65535)
    "usageCoefficient": 1.0           # Коэффициент использования (по умолчанию 1.0)
}
```

### Опциональные поля:
```python
{
    "countryCode": "US",              # Код страны (2 символа ISO)
    "isDisabled": false               # Статус отключения (по умолчанию false)
}
```

### Поля ответа API:
```python
{
    "uuid": "node-uuid",
    "viewPosition": 1,
    "name": "Node Name",
    "address": "node.example.com",
    "port": 62050,
    "usageCoefficient": 1.0,
    "countryCode": "US",
    "isDisabled": false,
    "isConnected": true,
    "version": "1.6.5",
    "uptime": "2d 5h 30m",
    "lastConnectedAt": "2024-01-15T10:30:00Z"
}
```

## Примеры использования

### Создание ноды с валидацией
```python
# Создание данных ноды
node_data = NodeAPI.create_node_template(
    name="Main Server",
    address="server.example.com",
    port=62050,
    usageCoefficient=1.5,
    countryCode="US"
)

# Валидация данных
is_valid, error = NodeAPI.validate_node_data(node_data)
if is_valid:
    result = await NodeAPI.create_node(node_data)
    print("Node created successfully")
else:
    print(f"Validation error: {error}")
```

### Обновление ноды
```python
update_data = {
    "uuid": "node-uuid",
    "name": "Updated Server",
    "usageCoefficient": 2.0,
    "isDisabled": False
}

# Валидация коэффициента использования
if update_data.get('usageCoefficient', 1.0) > 0:
    result = await NodeAPI.update_node(update_data)
```

### Массовые операции
```python
# Включить несколько нод
node_uuids = ["uuid1", "uuid2", "uuid3"]
result = await NodeAPI.bulk_enable_nodes(node_uuids)

# Перезапустить выбранные ноды
await NodeAPI.bulk_restart_nodes(node_uuids)

# Добавить inbound к ноде
await NodeAPI.add_inbound_to_node("node-uuid", "inbound-uuid")
```

### Изменение порядка нод
```python
nodes_order = [
    {"uuid": "node-uuid-1", "viewPosition": 1},
    {"uuid": "node-uuid-2", "viewPosition": 2},
    {"uuid": "node-uuid-3", "viewPosition": 3}
]
result = await NodeAPI.reorder_nodes(nodes_order)
```

### Получение статистики
```python
# Получить статистику использования за период
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=7)

usage = await NodeAPI.get_nodes_usage_by_range(
    start_date.isoformat(),
    end_date.isoformat()
)

# Получить статистику в реальном времени
realtime = await NodeAPI.get_nodes_realtime_usage()

# Получить статистику конкретной ноды
node_usage = await NodeAPI.get_node_usage_by_range(
    "node-uuid",
    start_date.isoformat(),
    end_date.isoformat()
)
```

### Поиск и фильтрация
```python
# Поиск по имени
results = await NodeAPI.search_nodes_by_name("main")

# Получить ноды по стране
us_nodes = await NodeAPI.get_nodes_by_country("US")

# Получить только подключенные ноды
connected = await NodeAPI.get_connected_nodes()

# Получить только включенные ноды
enabled = await NodeAPI.get_enabled_nodes()
```

### Управление inbound'ами ноды
```python
# Получить inbound'ы ноды
inbounds = await NodeAPI.get_node_inbounds("node-uuid")

# Добавить inbound к ноде
await NodeAPI.add_inbound_to_node("node-uuid", "inbound-uuid")

# Удалить inbound у ноды
await NodeAPI.remove_inbound_from_node("node-uuid", "inbound-uuid")
```

### Получение сертификата
```python
# Получить публичный ключ для настройки ноды
certificate = await NodeAPI.get_node_certificate()
print(f"Public key: {certificate}")
```

## API Endpoints (из официальной документации)

### Основные endpoints:
- `GET /api/nodes` - Получить все ноды
- `POST /api/nodes` - Создать ноду
- `PATCH /api/nodes` - Обновить ноду
- `GET /api/nodes/{uuid}` - Получить ноду по UUID
- `DELETE /api/nodes/{uuid}` - Удалить ноду

### Управление состоянием:
- `POST /api/nodes/{uuid}/enable` - Включить ноду
- `POST /api/nodes/{uuid}/disable` - Отключить ноду
- `POST /api/nodes/{uuid}/restart` - Перезапустить ноду
- `POST /api/nodes/actions/restart-all` - Перезапустить все ноды

### Массовые операции:
- `POST /api/nodes/bulk/delete` - Массовое удаление
- `POST /api/nodes/bulk/enable` - Массовое включение
- `POST /api/nodes/bulk/disable` - Массовое отключение
- `POST /api/nodes/bulk/restart` - Массовый перезапуск

### Управление порядком:
- `POST /api/nodes/actions/reorder` - Изменить порядок

### Управление inbound'ами:
- `GET /api/nodes/{uuid}/inbounds` - Получить inbound'ы ноды
- `POST /api/nodes/{uuid}/inbounds` - Добавить inbound к ноде
- `DELETE /api/nodes/{uuid}/inbounds/{inboundUuid}` - Удалить inbound у ноды

### Статистика:
- `GET /api/nodes/usage/realtime` - Статистика в реальном времени
- `GET /api/nodes/usage/range` - Статистика за период
- `GET /api/nodes/usage/{uuid}/users/range` - Статистика ноды за период

### Сертификаты:
- `GET /api/keygen` - Получить публичный ключ панели

## Примечания
- Все методы асинхронные и используют `RemnaAPI` клиент
- UUID параметры обязательны для операций с конкретными нодами
- Методы возвращают JSON ответы от API в формате `{"response": data}`
- Обработка ошибок происходит на уровне `RemnaAPI` клиента
- Поиск и фильтрация выполняются на стороне клиента
- Валидация данных помогает избежать ошибок перед отправкой запросов
- Все эндпоинты требуют авторизации через `Authorization` заголовок
- Статистика в реальном времени может быть пустой, в этом случае создаются fallback данные
- Коэффициент использования влияет на расчет потребления трафика пользователями