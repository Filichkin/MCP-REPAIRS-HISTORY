# Быстрый старт с Docker

## Предварительные требования

- Docker >= 20.10
- Docker Compose >= 2.0
- Минимум 4GB RAM
- Доступ к интернету для загрузки образов

## Шаг 1: Настройка переменных окружения

Скопируйте пример конфигурации и отредактируйте под свои нужды:

```bash
cd infra
cp .env.example .env
nano .env
```

Обязательные переменные:
```bash
# GigaChat API ключи
GIGACHAT_API_KEY=your-gigachat-key-here
GIGACHAT_API_KEY_EVOLUTION=your-evolution-key-here

# Cloud-RAG конфигурация
KEY_ID=your-key-id
KEY_SECRET=your-key-secret
AUTH_URL=https://ngw.devices.sberbank.ru:9443/api/v2/oauth
RETRIEVE_URL_TEMPLATE=https://gigachat.devices.sberbank.ru/api/v1
KNOWLEDGE_BASE_ID=your-kb-id
EVOLUTION_PROJECT_ID=your-project-id
```

## Шаг 2: Выберите режим запуска

### Вариант A: Только MCP Server

Для разработки или тестирования MCP инструментов:

```bash
docker-compose up mcp-server
```

Сервер будет доступен на: `http://localhost:8004`

Проверка работоспособности:
```bash
curl http://localhost:8004/health
```

### Вариант B: MCP Server + Agent System

Для использования API без UI:

```bash
docker-compose --profile agent up
```

Доступные endpoints:
- MCP Server: `http://localhost:8004`
- Agent API: `http://localhost:8005`

Проверка:
```bash
curl http://localhost:8005/health
```

### Вариант C: Полная система с UI

Рекомендуется для первого запуска:

```bash
docker-compose --profile full up
```

Доступные сервисы:
- Frontend UI: `http://localhost:7860`
- Agent API: `http://localhost:8005`
- MCP Server: `http://localhost:8004`

Откройте браузер и перейдите на `http://localhost:7860`

## Шаг 3: Первый запрос

### Через UI (если запущен frontend)

1. Откройте `http://localhost:7860` в браузере
2. Введите VIN: `XWEHC812BD0001234` (пример)
3. Введите вопрос: "Сколько дней машина была в ремонте?"
4. Нажмите Submit

### Через API

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Сколько дней машина была в ремонте?",
    "vin": "XWEHC812BD0001234"
  }'
```

### Через MCP Server напрямую

```bash
curl -X POST http://localhost:8004/tools/warranty_days \
  -H "Content-Type: application/json" \
  -d '{
    "vin": "XWEHC812BD0001234"
  }'
```

## Остановка и очистка

```bash
# Остановить все сервисы
docker-compose down

# Остановить и удалить volumes
docker-compose down -v

# Полная очистка (включая образы)
docker-compose down --rmi all -v
```

## Запуск в фоновом режиме

```bash
# Запуск в background
docker-compose --profile full up -d

# Просмотр логов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f agent
```

## Обновление кода

После изменения кода пересоберите нужный образ:

```bash
# Пересборка конкретного сервиса
docker-compose build agent

# Перезапуск с пересборкой
docker-compose --profile full up --build
```

## Частые команды

```bash
# Статус сервисов
docker-compose ps

# Logs всех сервисов
docker-compose logs -f

# Выполнить команду в контейнере
docker-compose exec agent python -m agent.main test "test query"

# Перезапустить сервис
docker-compose restart agent

# Масштабирование
docker-compose --profile full up --scale agent=3
```

## Проверка health статуса

```bash
# MCP Server
curl http://localhost:8004/health

# Agent System
curl http://localhost:8005/health

# Frontend (просто проверка доступности)
curl http://localhost:7860/
```

## Troubleshooting

### Порты заняты

Если порты 8004, 8005 или 7860 уже используются, измените их в `docker-compose.yml`:

```yaml
ports:
  - "18004:8004"  # Изменить внешний порт
```

### Нехватка памяти

```bash
# Проверить использование ресурсов
docker stats

# Увеличить лимиты в docker-compose.yml
services:
  agent:
    deploy:
      resources:
        limits:
          memory: 4G
```

### Ошибки при сборке

```bash
# Очистить кеш и пересобрать
docker-compose build --no-cache

# Проверить Docker daemon
docker info
```

### Проблемы с сетью

```bash
# Пересоздать сеть
docker-compose down
docker network prune
docker-compose --profile full up
```

## Дополнительная информация

Подробная документация: [DOCKER.md](./DOCKER.md)

## Примеры использования

### Пример 1: Проверка гарантийных дней

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Проверь гарантийные обязательства",
    "vin": "XWEHC812BD0001234"
  }'
```

### Пример 2: Анализ истории ремонтов

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Покажи историю всех ремонтов",
    "vin": "XWEHC812BD0001234"
  }'
```

### Пример 3: Поиск в базе знаний

```bash
curl -X POST http://localhost:8004/tools/compliance_rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Какие условия гарантии на двигатель?"
  }'
```

## Production Deployment

Для production используйте:

1. Отдельный `.env` файл с production секретами
2. Nginx reverse proxy (включен в профиль)
3. HTTPS сертификаты
4. Мониторинг и логирование
5. Backup стратегию

```bash
# Production запуск с Nginx
docker-compose --profile full --profile nginx up -d
```

Подробнее см. [DOCKER.md](./DOCKER.md#production-deployment)
