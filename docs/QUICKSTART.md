# Quick Start Guide

Быстрый запуск Warranty Agent System за 5 минут.

## Шаг 1: Клонирование и переход в директорию

```bash
cd /Users/alexeyfilichkin/KRU_DEV/MCP-REPAIRS-HISTORY/backend/agent
```

## Шаг 2: Установка зависимостей

### Вариант A: С Poetry (рекомендуется)

```bash
# Установка Poetry (если не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# Установка зависимостей
poetry install
```

### Вариант B: С pip

```bash
# Создание виртуального окружения
python3 -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

## Шаг 3: Настройка .env файла

```bash
# Скопируйте пример
cp ../../.env.example ../../.env

# Отредактируйте .env и укажите ваш GigaChat API ключ
nano ../../.env
```

Минимально необходимые переменные:

```env
GIGACHAT_API_KEY=ваш_ключ_здесь
MCP_SERVER_URL=http://localhost:8004
```

## Шаг 4: Запуск MCP сервера

В отдельном терминале:

```bash
cd ../../backend/mcp_server
python -m uvicorn main:app --host 0.0.0.0 --port 8004
```

## Шаг 5: Запуск Warranty Agent

```bash
# С Poetry
poetry run python -m backend.agent.main server

# С python
python -m backend.agent.main server
```

## Шаг 6: Проверка работоспособности

### Health Check

```bash
curl http://localhost:8005/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "mcp_server_status": "connected",
  "llm_status": "ready"
}
```

### Тестовый запрос

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Какие у меня права, если автомобиль более 30 дней в ремонте?"
  }'
```

## Шаг 7: Открытие документации

Откройте в браузере:
- Swagger UI: http://localhost:8005/docs
- ReDoc: http://localhost:8005/redoc

## Быстрые тесты

### Тест 1: Вопрос о правах (без VIN)

```bash
poetry run python -m backend.agent.main test \
  "Какие у меня права при превышении 30 дней ремонта?"
```

### Тест 2: Анализ дней простоя (с VIN)

```bash
poetry run python -m backend.agent.main test \
  "Сколько дней автомобиль был в ремонте?" \
  WBADT43452G123456
```

### Тест 3: Комплексный анализ

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Проанализируй полную историю ремонтов",
    "vin": "WBADT43452G123456"
  }' | jq '.response'
```

## Что дальше?

1. Изучите [README.md](README.md) для полной документации
2. Посмотрите [EXAMPLES.md](EXAMPLES.md) для примеров использования
3. Изучите [ARCHITECTURE.md](ARCHITECTURE.md) для понимания архитектуры

## Troubleshooting

### Ошибка: "GIGACHAT_API_KEY must be set"

Убедитесь, что в `.env` файле указан валидный API ключ GigaChat.

### Ошибка: "MCP server connection error"

Проверьте, что MCP сервер запущен на порту 8004:
```bash
curl http://localhost:8004/health
```

### Ошибка: "Port 8005 already in use"

Измените порт в `.env`:
```env
API_PORT=8006
```

### Ошибка импорта модулей

Убедитесь, что вы находитесь в правильной директории и виртуальное окружение активировано.

## Получение помощи

- Проверьте логи: `tail -f logs/agent_*.log`
- Включите debug режим: `APP_DEBUG=true` в `.env`
- Проверьте health endpoint: `curl http://localhost:8005/health`

## Успешный запуск!

Если все прошло успешно, вы должны видеть:

```
2024-01-15 10:30:00 | INFO     | Starting server on 0.0.0.0:8005
2024-01-15 10:30:00 | INFO     | MCP client initialized
2024-01-15 10:30:01 | INFO     | Application startup complete
```

Система готова к работе!
