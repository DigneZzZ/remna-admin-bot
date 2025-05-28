# Bulk API Methods Documentation (Official Remnawave API v1.6.5)

## Официальные методы BulkAPI

### Массовые операции с пользователями
- `bulk_delete_users(uuids)` - Массовое удаление пользователей по UUID
- `bulk_delete_users_by_status(status)` - Массовое удаление пользователей по статусу
- `bulk_revoke_users_subscription(uuids)` - Массовая отмена подписок пользователей
- `bulk_reset_users_traffic(uuids)` - Массовый сброс трафика пользователей
- `bulk_update_users(uuids, fields)` - Массовое обновление полей пользователей
- `bulk_update_users_inbounds(uuids, inbounds)` - Массовое обновление inbound'ов пользователей
- `bulk_update_all_users(fields)` - Обновление всех пользователей
- `bulk_reset_all_users_traffic()` - Сброс трафика всех пользователей
- `bulk_revoke_all_users_subscription()` - Отмена подписок всех пользователей
- `bulk_delete_all_users()` - Удаление всех пользователей

### Массовые операции с inbound'ами
- `bulk_delete_inbounds(uuids)` - Массовое удаление inbound'ов
- `bulk_enable_inbounds(uuids)` - Массовое включение inbound'ов
- `bulk_disable_inbounds(uuids)` - Массовое отключение inbound'ов
- `bulk_restart_inbounds(uuids)` - Массовый перезапуск inbound'ов
- `bulk_add_inbound_to_users(inbound_uuid, user_uuids)` - Добавить inbound к пользователям
- `bulk_remove_inbound_from_users(inbound_uuid, user_uuids)` - Удалить inbound у пользователей
- `bulk_add_inbound_to_nodes(inbound_uuid, node_uuids)` - Добавить inbound к нодам
- `bulk_remove_inbound_from_nodes(inbound_uuid, node_uuids)` - Удалить inbound у нод

### Массовые операции с хостами
- `bulk_delete_hosts(uuids)` - Массовое удаление хостов
- `bulk_enable_hosts(uuids)` - Массовое включение хостов
- `bulk_disable_hosts(uuids)` - Массовое отключение хостов
- `bulk_set_hosts_inbound(uuids, inbound_uuid)` - Установить inbound для хостов
- `bulk_set_hosts_port(uuids, port)` - Установить порт для хостов

### Массовые операции с нодами
- `bulk_delete_nodes(uuids)` - Массовое удаление нод
- `bulk_enable_nodes(uuids)` - Массовое включение нод
- `bulk_disable_nodes(uuids)` - Массовое отключение нод
- `bulk_restart_nodes(uuids)` - Массовый перезапуск нод

### Утилитарные методы
- `validate_bulk_operation_data(operation_type, data)` - Валидация данных массовых операций
- `bulk_operation_with_validation(operation_func, operation_type, data)` - Выполнение операции с валидацией
- `execute_multiple_bulk_operations(operations)` - Выполнение нескольких массовых операций
- `create_bulk_operation_summary(operation_name, total_items, ...)` - Создание сводки операции

## Примеры использования

### Массовые операции с пользователями
```python
# Массовое удаление пользователей
user_uuids = ["user1", "user2", "user3"]
result = await BulkAPI.bulk_delete_users(user_uuids)

# Удаление пользователей по статусу
result = await BulkAPI.bulk_delete_users_by_status("EXPIRED")

# Массовый сброс трафика
result = await BulkAPI.bulk_reset_users_traffic(user_uuids)

# Массовое обновление полей пользователей
fields = {
    "dataLimitInGB": 50,
    "expiryTime": "2024-12-31T23:59:59Z"
}
result = await BulkAPI.bulk_update_users(user_uuids, fields)

# Обновление inbound'ов пользователей
inbounds = [
    {"inboundUuid": "inbound1", "enable": True},
    {"inboundUuid": "inbound2", "enable": False}
]
result = await BulkAPI.bulk_update_users_inbounds(user_uuids, inbounds)
```

### Массовые операции с inbound'ами
```python
# Массовое включение inbound'ов
inbound_uuids = ["inbound1", "inbound2", "inbound3"]
result = await BulkAPI.bulk_enable_inbounds(inbound_uuids)

# Добавление inbound'а к пользователям
result = await BulkAPI.bulk_add_inbound_to_users("inbound-uuid", user_uuids)

# Добавление inbound'а к нодам
node_uuids = ["node1", "node2"]
result = await BulkAPI.bulk_add_inbound_to_nodes("inbound-uuid", node_uuids)
```

### Массовые операции с хостами
```python
# Массовое включение хостов
host_uuids = ["host1", "host2", "host3"]
result = await BulkAPI.bulk_enable_hosts(host_uuids)

# Установка inbound'а для хостов
result = await BulkAPI.bulk_set_hosts_inbound(host_uuids, "inbound-uuid")

# Установка порта для хостов (с валидацией)
port = 443
if 1 <= port <= 65535:
    result = await BulkAPI.bulk_set_hosts_port(host_uuids, port)
```

### Валидация данных
```python
# Валидация данных пользователей
data = {
    "uuids": ["user1", "user2"],
    "fields": {"dataLimitInGB": 100}
}
is_valid, error = BulkAPI.validate_bulk_operation_data("users", data)
if is_valid:
    result = await BulkAPI.bulk_update_users(data["uuids"], data["fields"])
else:
    print(f"Validation error: {error}")

# Валидация данных хостов
data = {
    "uuids": ["host1", "host2"],
    "port": 443
}
is_valid, error = BulkAPI.validate_bulk_operation_data("hosts", data)
```

### Выполнение множественных операций
```python
# Подготовка операций
operations = [
    {
        "func": BulkAPI.bulk_enable_users,
        "args": [["user1", "user2"]]
    },
    {
        "func": BulkAPI.bulk_reset_users_traffic,
        "args": [["user1", "user2"]]
    },
    {
        "func": BulkAPI.bulk_enable_inbounds,
        "args": [["inbound1", "inbound2"]]
    }
]

# Выполнение всех операций
results = await BulkAPI.execute_multiple_bulk_operations(operations)

# Анализ результатов
for i, result in enumerate(results):
    if result["success"]:
        print(f"Operation {i+1}: Success")
    else:
        print(f"Operation {i+1}: Failed - {result['error']}")
```

### Создание сводки операций
```python
# Создание сводки после выполнения массовой операции
total_users = 100
successful = 95
failed = 5

summary = BulkAPI.create_bulk_operation_summary(
    operation_name="bulk_reset_users_traffic",
    total_items=total_users,
    successful_items=successful,
    failed_items=failed
)

print(f"Operation: {summary['operation']}")
print(f"Success rate: {summary['success_rate']:.1f}%")
print(f"Total: {summary['total_items']}, Success: {summary['successful_items']}, Failed: {summary['failed_items']}")
```

### Операция с валидацией
```python
# Выполнение операции с автоматической валидацией
async def safe_bulk_update_users(uuids, fields):
    data = {"uuids": uuids, "fields": fields}
    return await BulkAPI.bulk_operation_with_validation(
        BulkAPI.bulk_update_users(uuids, fields),
        "users",
        data
    )

# Использование
result = await safe_bulk_update_users(
    ["user1", "user2"],
    {"dataLimitInGB": 50}
)
```

## Структуры данных для массовых операций

### Данные для обновления пользователей
```python
fields = {
    "dataLimitInGB": 100,                    # Лимит данных в ГБ
    "expiryTime": "2024-12-31T23:59:59Z",   # Время истечения
    "username": "new_username",              # Имя пользователя
    "isDisabled": False                      # Статус активности
}
```

### Данные для обновления inbound'ов пользователей
```python
inbounds = [
    {
        "inboundUuid": "550e8400-e29b-41d4-a716-446655440000",
        "enable": True
    },
    {
        "inboundUuid": "550e8400-e29b-41d4-a716-446655440001", 
        "enable": False
    }
]
```

### Статусы пользователей для фильтрации
- `ACTIVE` - Активные пользователи
- `EXPIRED` - Пользователи с истекшим сроком
- `LIMITED` - Пользователи с исчерпанным трафиком
- `DISABLED` - Отключенные пользователи

## API Endpoints (из официальной документации)

### Пользователи:
- `POST /api/users/bulk/delete` - Массовое удаление
- `POST /api/users/bulk/delete-by-status` - Удаление по статусу
- `POST /api/users/bulk/revoke-subscription` - Отмена подписок
- `POST /api/users/bulk/reset-traffic` - Сброс трафика
- `POST /api/users/bulk/update` - Массовое обновление
- `POST /api/users/bulk/update-inbounds` - Обновление inbound'ов
- `POST /api/users/bulk/all/update` - Обновление всех пользователей
- `POST /api/users/bulk/all/reset-traffic` - Сброс трафика всех
- `POST /api/users/bulk/all/revoke-subscription` - Отмена подписок всех
- `POST /api/users/bulk/all/delete` - Удаление всех пользователей

### Inbound'ы:
- `POST /api/inbounds/bulk/delete` - Массовое удаление
- `POST /api/inbounds/bulk/enable` - Массовое включение
- `POST /api/inbounds/bulk/disable` - Массовое отключение
- `POST /api/inbounds/bulk/restart` - Массовый перезапуск
- `POST /api/inbounds/bulk/add-to-users` - Добавить к пользователям
- `POST /api/inbounds/bulk/remove-from-users` - Удалить у пользователей
- `POST /api/inbounds/bulk/add-to-nodes` - Добавить к нодам
- `POST /api/inbounds/bulk/remove-from-nodes` - Удалить у нод

### Хосты:
- `POST /api/hosts/bulk/delete` - Массовое удаление
- `POST /api/hosts/bulk/enable` - Массовое включение
- `POST /api/hosts/bulk/disable` - Массовое отключение
- `POST /api/hosts/bulk/set-inbound` - Установить inbound
- `POST /api/hosts/bulk/set-port` - Установить порт

### Ноды:
- `POST /api/nodes/bulk/delete` - Массовое удаление
- `POST /api/nodes/bulk/enable` - Массовое включение
- `POST /api/nodes/bulk/disable` - Массовое отключение
- `POST /api/nodes/bulk/restart` - Массовый перезапуск

## Примечания
- Все методы асинхронные и используют `RemnaAPI` клиент
- Массовые операции могут обрабатывать большое количество элементов
- Валидация данных помогает избежать ошибок перед отправкой запросов
- Утилитарные методы упрощают выполнение сложных операций
- Все эндпоинты требуют авторизации через `Authorization` заголовок
- При массовых операциях рекомендуется обрабатывать ошибки для каждого элемента отдельно
- Операции "all" (со всеми пользователями) требуют особой осторожности