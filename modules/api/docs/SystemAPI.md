# System API Methods Documentation (For Telegram Bot)

## Методы SystemAPI для Telegram бота

### Статистика системы
- `get_stats()` - Получить общую статистику системы
- `get_bandwidth_stats()` - Получить статистику пропускной способности
- `get_nodes_statistics()` - Получить статистику нод
- `get_users_statistics()` - Получить статистику пользователей
- `get_inbounds_statistics()` - Получить статистику inbound'ов
- `get_system_info()` - Получить информацию о системе

### XRay конфигурация
- `get_xray_config()` - Получить конфигурацию XRay
- `update_xray_config(config_data)` - Обновить конфигурацию XRay
- `restart_xray()` - Перезапустить XRay core
- `get_xray_status()` - Получить статус XRay

### Управление панелью
- `get_panel_info()` - Получить информацию о панели
- `restart_panel()` - Перезапустить панель
- `get_panel_logs()` - Получить логи панели

### Мониторинг системы
- `get_health_check()` - Получить проверку состояния системы
- `get_disk_usage()` - Получить информацию об использовании диска
- `get_memory_usage()` - Получить информацию об использовании памяти
- `get_cpu_usage()` - Получить информацию об использовании CPU

### Обновления и версии
- `get_version_info()` - Получить информацию о версии
- `check_updates()` - Проверить доступные обновления
- `get_update_status()` - Получить статус обновления

### Утилиты для бота
- `format_bytes(bytes_value)` - Форматировать байты в читаемый вид
- `format_uptime(seconds)` - Форматировать время работы
- `get_system_summary()` - Получить сводку состояния системы

## Примеры использования в боте

### Отображение статистики в боте
```python
async def show_system_stats(update, context):
    """Показать статистику системы в боте"""
    try:
        # Получить общую статистику
        stats = await SystemAPI.get_stats()
        if stats and 'response' in stats:
            data = stats['response']
            
            message = f"📊 **Статистика системы**\n\n"
            message += f"👥 Пользователей: {data.get('totalUsers', 0)}\n"
            message += f"🔗 Активных подключений: {data.get('activeConnections', 0)}\n"
            message += f"📡 Inbound'ов: {data.get('totalInbounds', 0)}\n"
            message += f"🖥️ Нод: {data.get('totalNodes', 0)}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения статистики: {e}")

async def show_bandwidth_stats(update, context):
    """Показать статистику трафика в боте"""
    try:
        bandwidth = await SystemAPI.get_bandwidth_stats()
        if bandwidth and 'response' in bandwidth:
            data = bandwidth['response']
            
            upload = SystemAPI.format_bytes(data.get('upload', 0))
            download = SystemAPI.format_bytes(data.get('download', 0))
            total = SystemAPI.format_bytes(data.get('total', 0))
            
            message = f"📈 **Статистика трафика**\n\n"
            message += f"⬆️ Отправлено: {upload}\n"
            message += f"⬇️ Получено: {download}\n"
            message += f"📊 Всего: {total}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения статистики трафика: {e}")
```

### Мониторинг ресурсов системы
```python
async def show_system_resources(update, context):
    """Показать использование ресурсов системы"""
    try:
        # Получаем данные о ресурсах
        disk = await SystemAPI.get_disk_usage()
        memory = await SystemAPI.get_memory_usage()
        cpu = await SystemAPI.get_cpu_usage()
        
        message = f"🖥️ **Ресурсы системы**\n\n"
        
        if disk and 'response' in disk:
            usage = disk['response'].get('usage', 0)
            message += f"💾 Диск: {usage}%\n"
        
        if memory and 'response' in memory:
            usage = memory['response'].get('usage', 0)
            message += f"🧠 Память: {usage}%\n"
        
        if cpu and 'response' in cpu:
            usage = cpu['response'].get('usage', 0)
            message += f"⚡ CPU: {usage}%\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения данных о ресурсах: {e}")
```

### Управление XRay через бота
```python
async def restart_xray_command(update, context):
    """Перезапустить XRay через бота"""
    try:
        # Показать статус перезапуска
        await update.message.reply_text("🔄 Перезапускаю XRay...")
        
        # Перезапустить XRay
        result = await SystemAPI.restart_xray()
        
        if result:
            await update.message.reply_text("✅ XRay успешно перезапущен")
        else:
            await update.message.reply_text("❌ Ошибка перезапуска XRay")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def show_xray_status(update, context):
    """Показать статус XRay"""
    try:
        status = await SystemAPI.get_xray_status()
        if status and 'response' in status:
            data = status['response']
            status_text = "🟢 Работает" if data.get('running') else "🔴 Остановлен"
            
            message = f"⚡ **Статус XRay**\n\n"
            message += f"Состояние: {status_text}\n"
            if 'version' in data:
                message += f"Версия: {data['version']}\n"
            if 'uptime' in data:
                uptime = SystemAPI.format_uptime(data['uptime'])
                message += f"Время работы: {uptime}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения статуса XRay: {e}")
```

### Проверка обновлений через бота
```python
async def check_updates_command(update, context):
    """Проверить обновления через бота"""
    try:
        # Текущая версия
        version_info = await SystemAPI.get_version_info()
        current_version = "Неизвестно"
        if version_info and 'response' in version_info:
            current_version = version_info['response'].get('version', 'Неизвестно')
        
        # Проверка обновлений
        updates = await SystemAPI.check_updates()
        
        message = f"📦 **Информация о версии**\n\n"
        message += f"Текущая версия: {current_version}\n"
        
        if updates and 'response' in updates:
            data = updates['response']
            if data.get('available'):
                latest = data.get('latestVersion', 'Неизвестно')
                message += f"🆕 Доступна новая версия: {latest}\n"
                message += "Обновление доступно!"
            else:
                message += "✅ У вас последняя версия"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка проверки обновлений: {e}")
```

### Сводка системы для бота
```python
async def show_system_summary(update, context):
    """Показать полную сводку системы"""
    try:
        summary = await SystemAPI.get_system_summary()
        if summary and 'response' in summary:
            data = summary['response']
            
            message = f"📋 **Сводка системы**\n\n"
            
            # Статистика
            stats = data.get('stats', {})
            message += f"👥 Пользователей: {stats.get('totalUsers', 0)}\n"
            message += f"🔗 Подключений: {stats.get('activeConnections', 0)}\n"
            
            # Здоровье системы
            health = data.get('health', {})
            status = health.get('status', 'unknown')
            status_emoji = "🟢" if status == "healthy" else "🔴"
            message += f"{status_emoji} Состояние: {status}\n"
            
            # Информация о системе
            info = data.get('info', {})
            if 'version' in info:
                message += f"📦 Версия: {info['version']}\n"
            if 'uptime' in info:
                uptime = SystemAPI.format_uptime(info['uptime'])
                message += f"⏱️ Время работы: {uptime}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения сводки: {e}")
```

## API Endpoints

### Статистика:
- `GET /api/system/stats` - Общая статистика
- `GET /api/system/stats/bandwidth` - Статистика трафика
- `GET /api/system/stats/nodes` - Статистика нод
- `GET /api/system/stats/users` - Статистика пользователей
- `GET /api/system/stats/inbounds` - Статистика inbound'ов
- `GET /api/system/info` - Информация о системе

### XRay:
- `GET /api/xray` - Конфигурация XRay
- `PATCH /api/xray` - Обновить конфигурацию
- `POST /api/xray/restart` - Перезапустить XRay
- `GET /api/xray/status` - Статус XRay

### Панель:
- `GET /api/panel/info` - Информация о панели
- `POST /api/panel/restart` - Перезапустить панель
- `GET /api/panel/logs` - Логи панели

### Мониторинг:
- `GET /api/health` - Проверка состояния
- `GET /api/system/disk` - Использование диска
- `GET /api/system/memory` - Использование памяти
- `GET /api/system/cpu` - Использование CPU

### Обновления:
- `GET /api/version` - Информация о версии
- `GET /api/updates/check` - Проверить обновления
- `GET /api/updates/status` - Статус обновления

## Примечания для бота
- Все методы асинхронные и подходят для использования в Telegram боте
- Утилиты форматирования помогают показывать данные в удобном виде
- Обработка ошибок важна для стабильной работы бота
- Методы возвращают данные в формате, удобном для отображения в сообщениях