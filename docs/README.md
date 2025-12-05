# Warranty Agent System

Мультиагентная система на LangGraph для анализа гарантийных обращений автомобилей.

## Описание

Система использует LangGraph и GigaChat для интеллектуального анализа гарантийных обращений. Включает 4 специализированных агента:

1. **Repair Days Tracker** - анализ дней простоя в ремонте, проверка 30-дневного лимита
2. **Warranty Compliance** - интерпретация гарантийной политики и законодательства
3. **Dealer Insights** - анализ истории ремонтов, выявление паттернов
4. **Report & Summary** - генерация итоговых отчётов

## Архитектура

```
User Query
    ↓
Query Classifier (определяет нужных агентов)
    ↓
[Параллельное выполнение агентов]
    ↓
Report & Summary (итоговый отчёт)
    ↓
Response Aggregator
    ↓
Final Response
```

## Установка

### Требования

- Python 3.11+
- Poetry (рекомендуется) или pip
- Доступ к GigaChat API
- Запущенный MCP сервер (порт 8004)

### Шаги установки

1. Перейдите в директорию проекта:
```bash
cd backend/agent
```

2. Установите зависимости:

**С Poetry (рекомендуется):**
```bash
poetry install
```

**С pip:**
```bash
pip install -r requirements.txt
```

3. Настройте переменные окружения:

Создайте файл `.env` в корне проекта (`MCP-REPAIRS-HISTORY/.env`):

```env
# GigaChat Configuration
GIGACHAT_API_KEY=your_gigachat_api_key_here
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat
GIGACHAT_TEMPERATURE=0.7

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8004
MCP_TIMEOUT=30
MCP_MAX_RETRIES=3

# Agent Configuration
AGENT_MAX_ITERATIONS=10
AGENT_MAX_EXECUTION_TIME=120

# Application Configuration
APP_DEBUG=false
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8005
```

4. Получите API ключ GigaChat:
   - Зарегистрируйтесь на https://developers.sber.ru/
   - Создайте проект и получите API ключ
   - Укажите ключ в `.env` файле

## Запуск

### Запуск API сервера

**С Poetry:**
```bash
poetry run python -m backend.agent.main server
```

**С python:**
```bash
python -m backend.agent.main server
```

Сервер запустится на `http://localhost:8005`

### Тестовый запрос

```bash
poetry run python -m backend.agent.main test "Сколько дней автомобиль был в ремонте?" WBADT43452G123456
```

### Документация API

После запуска сервера документация доступна по адресу:
- Swagger UI: http://localhost:8005/docs
- ReDoc: http://localhost:8005/redoc

## Использование API

### Health Check

```bash
curl http://localhost:8005/health
```

### Выполнение запроса

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Сколько дней в 2023 году автомобиль был в ремонте?",
    "vin": "WBADT43452G123456"
  }'
```

### Пример с Python

```python
import requests

response = requests.post(
    'http://localhost:8005/agent/query',
    json={
        'query': 'Сколько дней в 2023 году автомобиль был в ремонте?',
        'vin': 'WBADT43452G123456',
        'context': {}
    }
)

result = response.json()
print(result['response'])
```

## Примеры запросов

### Анализ дней простоя
```json
{
  "query": "Сколько дней в этом году автомобиль был в ремонте? Есть ли риск превышения 30-дневного лимита?",
  "vin": "WBADT43452G123456"
}
```

### Вопрос о правах
```json
{
  "query": "Какие у меня права, если автомобиль более 30 дней находится в ремонте по гарантии?"
}
```

### Анализ истории ремонтов
```json
{
  "query": "Проанализируй всю историю ремонтов автомобиля. Есть ли повторяющиеся проблемы?",
  "vin": "WBADT43452G123456"
}
```

### Комплексный запрос
```json
{
  "query": "Составь полный отчёт по автомобилю: сколько дней был в ремонте, какие были проблемы, какие у меня права",
  "vin": "WBADT43452G123456"
}
```

## Структура проекта

```
backend/agent/
├── __init__.py
├── config.py                 # Конфигурация
├── main.py                   # Entry point
├── pyproject.toml           # Зависимости
├── README.md                # Документация
├── graph/                   # LangGraph
│   ├── state.py            # AgentState schema
│   ├── graph_builder.py    # Построение графа
│   ├── edges.py            # Routing logic
│   └── nodes/              # Узлы агентов
│       ├── classifier.py
│       ├── repair_days.py
│       ├── compliance.py
│       ├── dealer_insights.py
│       ├── report_summary.py
│       └── aggregator.py
├── llm/                     # GigaChat
│   ├── gigachat_setup.py
│   └── prompts.py
├── tools/                   # MCP tools
│   ├── mcp_client.py
│   └── langchain_tools.py
├── utils/                   # Утилиты
│   ├── vin_validator.py
│   └── formatters.py
└── api/                     # FastAPI
    ├── app.py
    └── schemas.py
```

## Разработка

### Запуск в режиме разработки

```bash
poetry run python -m backend.agent.main server
```

С auto-reload (добавьте в `.env`):
```env
API_RELOAD=true
APP_DEBUG=true
LOG_LEVEL=DEBUG
```

### Тестирование

```bash
# Запустите тесты (когда будут добавлены)
poetry run pytest

# Проверка типов
poetry run mypy backend/agent

# Форматирование кода
poetry run black backend/agent

# Линтинг
poetry run ruff check backend/agent
```

## Мониторинг и логи

Логи сохраняются в `logs/agent_YYYY-MM-DD.log` (ротация ежедневно, хранение 7 дней).

Просмотр логов в реальном времени:
```bash
tail -f logs/agent_$(date +%Y-%m-%d).log
```

## Производительность

- Средняя задержка запроса: 3-5 секунд
- Параллельное выполнение агентов
- Кэширование MCP запросов (TTL: 5 минут)
- Retry логика для устойчивости

## Troubleshooting

### Ошибка подключения к MCP серверу

Проверьте, что MCP сервер запущен:
```bash
curl http://localhost:8004/health
```

### Ошибка GigaChat API

- Проверьте API ключ в `.env`
- Убедитесь, что ключ активен
- Проверьте квоты и лимиты

### Невалидный VIN

VIN должен содержать:
- Ровно 17 символов
- Только латинские буквы и цифры
- Исключая I, O, Q

## Лицензия

Proprietary

## Контакты

Для вопросов и поддержки: your.email@example.com
