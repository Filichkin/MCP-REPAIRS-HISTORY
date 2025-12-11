# Система агентов для анализа гарантийных обращений

Мультиагентная система для анализа гарантийных обращений автомобилей, истории ремонтов и соблюдения гарантийных политик с использованием LangGraph и GigaChat LLM.

## Обзор

Система использует граф-процесс для маршрутизации пользовательских запросов через специализированных агентов, которые анализируют различные аспекты гарантийных данных и истории ремонтов автомобиля:

- **Классификатор** - Направляет запросы к соответствующим агентам
- **Анализатор дней простоя** - Анализирует дни простоя в ремонте и соблюдение 30-дневного лимита
- **Гарантийная политика** - Предоставляет рекомендации по гарантийным политикам и стандартам клиентского сервиса
- **Анализ истории ремонтов** - Анализирует полную историю ремонтов, паттерны и проблемы
- **Генератор отчетов** - Формирует итоговые отчеты на основе результатов работы агентов

## Архитектура

```
Запрос → Классификатор → [Агенты] → Генератор отчетов → Итоговый ответ
                ↓
         Дни простоя       ┐
         Гарантийная       ├→ Агрегатор → Отчет
         История ремонтов  ┘
```

### Компоненты

- **Graph Workflow** (`graph/`) - Машина состояний LangGraph для оркестрации выполнения агентов
- **Агенты/Узлы** (`graph/nodes/`) - Специализированные агенты анализа
- **LLM Интеграция** (`llm/`) - Настройка GigaChat и шаблоны промптов
- **MCP Client** (`tools/`) - Клиент для Model Context Protocol сервера
- **API** (`api/`) - FastAPI REST endpoints

## Предварительные требования

1. **MCP Server** должен быть запущен на `http://localhost:8004/sse`
   ```bash
   cd backend/mcp_server
   python server.py
   ```

2. **Переменные окружения** (см. `infra/.env`):
   - `GIGACHAT_API_KEY` - Ключ для langchain_gigachat библиотеки
   - `GIGACHAT_API_KEY_EVOLUTION` - API ключ для Evolution Platform (Api-Key)
   - `EVOLUTION_PROJECT_ID` - ID проекта в Evolution Platform
   - `GIGACHAT_USE_API` - Использовать прямой Evolution API вместо langchain (true/false, по умолчанию: false)
   - `GIGACHAT_SCOPE` - API scope для langchain (GIGACHAT_API_PERS или GIGACHAT_API_CORP)
   - `GIGACHAT_MODEL` - Название модели для langchain (по умолчанию: GigaChat-2)
     - **Важно:** Для Evolution API всегда используется модель `GigaChat`, независимо от этой настройки
   - `MCP_SERVER_URL` - URL MCP сервера (по умолчанию: http://localhost:8004)
   - `API_KEY`, `API_URL` - Credentials для внешнего API

## Установка

```bash
# Установка зависимостей
uv sync

# Или с помощью pip
pip install -r requirements.txt
```

## Запуск системы агентов

### Запуск сервера

```bash
# Используя CLI
python -m backend.agent.main server

# Или напрямую с uvicorn
uvicorn backend.agent.api.app:app --host 0.0.0.0 --port 8005 --reload
```

Сервер запустится на `http://0.0.0.0:8005`

### API Документация

После запуска, доступ к интерактивной API документации:
- Swagger UI: http://localhost:8005/docs
- ReDoc: http://localhost:8005/redoc

### API Endpoint

Основной endpoint для взаимодействия с системой агентов:

```bash
POST http://localhost:8005/agent/query
Content-Type: application/json

{
  "query": "Ваш вопрос",
  "vin": "Z94C251BBLR102931",  # опционально
  "context": {}
}
```

**Параметры запроса:**
- `query` (обязательный) - Текст запроса пользователя
- `vin` (опциональный) - VIN номер автомобиля для анализа конкретного транспортного средства
- `context` (опциональный) - Дополнительный контекст для запроса

## Примеры использования

### 1. Запрос с VIN (Анализ дней простоя)

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Сколько дней автомобиль находился в ремонте в 2025 году?",
    "vin": "XWEG3417BN0009095"
  }'
```

**Активирует:** Анализатор дней простоя

### 2. Запрос о гарантийной политике (VIN не требуется)

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Какие у меня права, если автомобиль находится в ремонте более 30 дней?"
  }'
```

**Активирует:** Гарантийная политика

### 3. Анализ истории ремонтов

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Какие проблемы повторяются с этим автомобилем?",
    "vin": "XWEG3417BN0009095"
  }'
```

**Активирует:** Анализ истории ремонтов

### 4. Комплексный запрос (Несколько агентов)

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Дай полный анализ: дни простоя, мои права и повторяющиеся проблемы",
    "vin": "XWEG3417BN0009095"
  }'
```

**Активирует:** Все три агента

## Формат ответа

```json
{
  "success": true,
  "query": "Текст запроса пользователя",
  "vin": "XWEG3417BN0009095",
  "response": "Сформированный комплексный отчет...",
  "agents_used": ["Repair Days Tracker", "Warranty Compliance"],
  "agent_results": [
    {
      "agent_name": "Repair Days Tracker",
      "success": true,
      "data": { "analysis": "...", "raw_data": {...} },
      "error": null,
      "timestamp": "2025-12-06T12:00:00"
    }
  ],
  "execution_time_seconds": 5.23,
  "steps_completed": ["classifier", "repair_days_tracker", "report_summary"],
  "errors": [],
  "start_time": "2025-12-06T12:00:00",
  "end_time": "2025-12-06T12:00:05"
}
```

## Описание агентов

### Классификатор (Classifier Agent)

**Назначение:** Анализирует запрос пользователя и направляет к соответствующим агентам

**Логика классификации:**
- Ключевые слова о "днях", "времени ремонта", "30-дневный лимит" → Анализатор дней простоя
- Ключевые слова о "правах", "гарантийной политике", "что делать если" → Гарантийная политика
- Ключевые слова об "истории", "повторяющихся проблемах", "качестве дилера" → Анализ истории ремонтов

**Результат:** Устанавливает флаги `needs_repair_days`, `needs_compliance`, `needs_dealer_insights`

### Анализатор дней простоя (Repair Days Tracker)

**Назначение:** Анализирует статистику дней простоя и соблюдение 30-дневного лимита

**Требования:** VIN должен быть указан

**Источники данных (через MCP):**
- `warranty_days` - Дни простоя в ремонте по годам владения

**Анализ:**
- Количество дней в гарантийных ремонтах по годам
- Соблюдение 30-дневного лимита (закон о защите прав потребителей РФ)
- Оценка рисков и прогнозирование
- Рекомендации

### Гарантийная политика (Warranty Compliance)

**Назначение:** Предоставляет рекомендации по гарантийным политикам и стандартам клиентского сервиса

**Требования:** Нет (работает без VIN)

**Источники данных (через MCP):**
- `compliance_rag` - База знаний с гарантийными политиками и стандартами дилера

**Анализ:**
- Интерпретация гарантийной политики
- Стандарты клиентского сервиса
- Права потребителей
- Рекомендуемые действия

### Анализ истории ремонтов (Dealer Insights)

**Назначение:** Анализирует полную историю ремонтов на предмет паттернов и проблем

**Требования:** VIN должен быть указан

**Источники данных (через MCP):**
- `warranty_history` - Записи гарантийных обращений
- `maintenance_history` - Записи регулярного технического обслуживания
- `vehicle_repairs_history` - Полная история ремонтов (записи DNM)

**Анализ:**
- Повторяющиеся проблемы и паттерны
- Частота ремонтов и сезонность
- Качество обслуживания дилера
- Эффективность ремонтов

## Конфигурация

### Настройки LLM

Настраиваются в `infra/.env`:

**Базовые настройки:**
```env
# Метод работы: true = прямой Evolution API, false = langchain_gigachat
GIGACHAT_USE_API=true

# Для langchain_gigachat:
GIGACHAT_API_KEY=your-langchain-api-key
GIGACHAT_MODEL=GigaChat-2
GIGACHAT_SCOPE=GIGACHAT_API_PERS

# Для Evolution Platform API:
GIGACHAT_API_KEY_EVOLUTION=your-evolution-api-key
EVOLUTION_PROJECT_ID=your-project-id

# Общие настройки:
GIGACHAT_TEMPERATURE=0.7
GIGACHAT_TIMEOUT=60
GIGACHAT_MAX_RETRIES=3
```

**Расширенные параметры (только для Evolution API, `GIGACHAT_USE_API=true`):**
```env
GIGACHAT_TOP_P=0.9
GIGACHAT_MAX_TOKENS=512
GIGACHAT_REPETITION_PENALTY=1.0
```

**Примечания:**
- При `GIGACHAT_USE_API=true` используется Evolution Platform API с аутентификацией через Api-Key
- Evolution API всегда использует модель `GigaChat` (не зависит от `GIGACHAT_MODEL`)
- `GIGACHAT_MODEL` применяется только при `GIGACHAT_USE_API=false` (langchain_gigachat)

### Настройки агентов

```env
AGENT_MAX_ITERATIONS=10
AGENT_MAX_EXECUTION_TIME=120
AGENT_ENABLE_STREAMING=true
```

### Настройки MCP клиента

```env
MCP_SERVER_URL=http://localhost:8004
MCP_TRANSPORT=http
MCP_TIMEOUT=30
MCP_MAX_RETRIES=3
MCP_CACHE_TTL=300
```

## Разработка

### Структура проекта

```
backend/agent/
├── api/              # FastAPI приложение и схемы
│   ├── app.py       # Основное FastAPI приложение
│   └── schemas.py   # Pydantic модели
├── graph/           # LangGraph workflow
│   ├── graph_builder.py  # Построение графа
│   ├── state.py     # Управление состоянием
│   ├── edges.py     # Логика маршрутизации
│   └── nodes/       # Реализация агентов
│       ├── classifier.py
│       ├── repair_days.py
│       ├── compliance.py
│       ├── dealer_insights.py
│       ├── report_summary.py
│       └── aggregator.py
├── llm/             # LLM интеграция
│   ├── gigachat_setup.py  # GigaChat менеджер (langchain/Evolution API)
│   ├── gigachat_api_client.py  # Прямой клиент Evolution Platform API
│   └── prompts.py   # Шаблоны промптов
├── tools/           # Внешние интеграции
│   └── mcp_client.py  # MCP SSE клиент
├── utils/           # Утилиты
│   └── vin_validator.py
└── main.py          # CLI точка входа
```

### Добавление нового агента

1. Создайте узел агента в `graph/nodes/your_agent.py`:

```python
async def your_agent_node(state: AgentState) -> AgentState:
    logger.info('Ваш агент запущен')

    # Ваша логика здесь
    result = perform_analysis(state.query, state.vin)

    # Сохраните результат
    state.your_agent_result = AgentResult(
        agent_name='Your Agent',
        success=True,
        data={'analysis': result}
    )

    state.mark_step_completed(GraphNodes.YOUR_AGENT)
    return state
```

2. Добавьте в логику классификатора в `prompts.py`
3. Добавьте маршрутизацию в `edges.py`
4. Зарегистрируйте в `graph_builder.py`

### Логирование

Логи настраиваются в `main.py`:

```python
logger.add(
    "logs/agent_{time}.log",
    rotation="100 MB",
    retention="7 days",
    level="INFO"
)
```

## Устранение неполадок

### Проблемы с подключением к MCP

```
ERROR | Ошибка дней в ремонте: Инструмент не найден: warranty_days
```

**Решение:** Убедитесь, что MCP сервер запущен на правильном URL:
```bash
# Проверка MCP сервера
curl http://localhost:8004/health
```

### Ошибки классификатора

```
ERROR | Ошибка классификации: '\n    "needs_repair_days"'
```

**Решение:** Это проблема с шаблоном промпта. Убедитесь, что JSON фигурные скобки экранированы с помощью `{{` и `}}` в промптах.

### Проблемы с сериализацией состояния

```
ERROR | 'dict' object has no attribute 'get_all_results'
```

**Решение:** Убедитесь, что граф возвращает dict состояния, который преобразуется обратно в AgentState:
```python
final_state_dict = await graph.ainvoke(initial_state.model_dump())
final_state = AgentState(**final_state_dict)
```

### Проверка работоспособности

```bash
curl http://localhost:8005/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "mcp_server_status": "healthy",
  "llm_status": "ready"
}
```

## Производительность

Типичное время выполнения:
- **Запрос с одним агентом:** 2-5 секунд
- **Запрос с несколькими агентами:** 10-15 секунд
- **С RAG:** +2-3 секунды

Кэширование включено по умолчанию (TTL 5 минут) для улучшения производительности при повторных запросах.

## Лицензия

См. корневой файл [LICENSE](../../LICENSE).
