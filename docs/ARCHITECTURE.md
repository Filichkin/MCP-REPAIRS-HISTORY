# Архитектура Warranty Agent System

## Обзор системы

Warranty Agent System - это мультиагентная система на базе LangGraph, которая анализирует гарантийные обращения автомобилей, используя GigaChat LLM и MCP (Model Context Protocol) для доступа к данным.

## Граф выполнения (LangGraph Flow)

```mermaid
graph TD
    Start([User Query]) --> Classifier[Query Classifier]
    
    Classifier --> Decision{Routing Decision}
    
    Decision -->|needs_repair_days| RepairDays[Repair Days Tracker]
    Decision -->|needs_compliance| Compliance[Warranty Compliance]
    Decision -->|needs_dealer_insights| DealerInsights[Dealer Insights]
    
    RepairDays --> Report[Report & Summary]
    Compliance --> Report
    DealerInsights --> Report
    
    Report --> Aggregator[Response Aggregator]
    Aggregator --> End([Final Response])
    
    style Start fill:#e1f5e1
    style End fill:#e1f5e1
    style Classifier fill:#fff4e1
    style Decision fill:#ffe1e1
    style Report fill:#e1f0ff
    style Aggregator fill:#f0e1ff
```

## Компоненты системы

### 1. API Layer (FastAPI)

```mermaid
graph LR
    Client[Client] -->|HTTP Request| API[FastAPI App]
    API -->|Validate| Schema[Pydantic Schemas]
    Schema -->|Execute| Graph[LangGraph]
    Graph -->|Result| API
    API -->|JSON Response| Client
    
    style API fill:#4CAF50,color:#fff
    style Graph fill:#2196F3,color:#fff
```

**Компоненты:**
- `api/app.py` - FastAPI приложение
- `api/schemas.py` - Pydantic модели для валидации
- Endpoints:
  - `POST /agent/query` - выполнение запроса
  - `GET /health` - проверка здоровья системы
  - `GET /docs` - Swagger документация

### 2. Graph Layer (LangGraph)

```mermaid
stateDiagram-v2
    [*] --> Classifier
    
    Classifier --> RepairDays: needs_repair_days
    Classifier --> Compliance: needs_compliance
    Classifier --> DealerInsights: needs_dealer_insights
    
    RepairDays --> Report
    Compliance --> Report
    DealerInsights --> Report
    
    Report --> Aggregator
    Aggregator --> [*]
    
    note right of Classifier
        Анализирует запрос
        Определяет нужных агентов
    end note
    
    note right of Report
        Объединяет результаты
        Генерирует итоговый отчёт
    end note
```

**Узлы (Nodes):**

1. **Classifier Node** (`graph/nodes/classifier.py`)
   - Анализирует пользовательский запрос
   - Определяет, какие агенты нужны
   - Извлекает VIN из запроса (если есть)

2. **Repair Days Tracker** (`graph/nodes/repair_days.py`)
   - Получает данные через `warranty_days(vin)`
   - Анализирует дни простоя по годам
   - Проверяет 30-дневный лимит
   - Прогнозирует риски

3. **Warranty Compliance** (`graph/nodes/compliance.py`)
   - Получает данные через `compliance_rag(query)`
   - Интерпретирует гарантийную политику
   - Объясняет права потребителя
   - Ссылается на законодательство

4. **Dealer Insights** (`graph/nodes/dealer_insights.py`)
   - Получает данные через:
     - `warranty_history(vin)`
     - `maintenance_history(vin)`
     - `vehicle_repairs_history(vin)`
   - Анализирует паттерны ремонтов
   - Выявляет повторяющиеся проблемы
   - Оценивает качество работы дилера

5. **Report & Summary** (`graph/nodes/report_summary.py`)
   - Агрегирует результаты всех агентов
   - Генерирует структурированный отчёт
   - Форматирует для пользователя

6. **Response Aggregator** (`graph/nodes/aggregator.py`)
   - Финальная валидация
   - Проверка полноты ответа
   - Добавление метаданных

**State Management:**

```python
class AgentState(BaseModel):
    # Input
    query: str
    vin: Optional[str]
    user_context: dict
    
    # Classification
    classification: Optional[AgentClassification]
    
    # Results
    repair_days_result: Optional[AgentResult]
    compliance_result: Optional[AgentResult]
    dealer_insights_result: Optional[AgentResult]
    
    # Output
    final_response: Optional[str]
    
    # Tracking
    steps_completed: list[str]
    errors: list[str]
```

### 3. LLM Layer (GigaChat)

```mermaid
graph TD
    Node[Agent Node] -->|Prompt| LLM[GigaChat LLM]
    
    Prompts[Prompt Templates] --> Node
    Config[Temperature Config] --> LLM
    
    LLM -->|Response| Node
    
    style LLM fill:#FF9800,color:#fff
    style Prompts fill:#9C27B0,color:#fff
```

**Компоненты:**
- `llm/gigachat_setup.py` - инициализация GigaChat
- `llm/prompts.py` - промпты для каждого агента

**LLM конфигурация по агентам:**

| Агент | Temperature | Назначение |
|-------|-------------|------------|
| Classifier | 0.3 | Точная классификация |
| Repair Days | 0.5 | Анализ с умеренной креативностью |
| Compliance | 0.4 | Точная интерпретация законов |
| Dealer Insights | 0.6 | Выявление паттернов |
| Report Summary | 0.5 | Структурированные отчёты |

### 4. Tools Layer (MCP Integration)

```mermaid
graph LR
    Agent[Agent Node] -->|Tool Call| LCTool[LangChain Tool]
    LCTool -->|HTTP Request| MCP[MCP Client]
    MCP -->|API Call| Server[MCP Server :8004]
    
    Server -->|Data| MCP
    MCP -->|Cache| Cache[(Cache)]
    MCP -->|Result| LCTool
    LCTool -->|Data| Agent
    
    style Server fill:#F44336,color:#fff
    style MCP fill:#03A9F4,color:#fff
    style Cache fill:#FFC107
```

**MCP Tools:**

1. `warranty_days(vin)` - статистика дней в ремонте
2. `warranty_history(vin)` - история гарантийных обращений
3. `maintenance_history(vin)` - история ТО
4. `vehicle_repairs_history(vin)` - полная история ремонтов
5. `compliance_rag(query)` - RAG поиск в базе знаний

**Особенности MCP Client:**
- Асинхронное выполнение
- Кэширование результатов (TTL: 5 минут)
- Retry логика (до 3 попыток)
- Обработка ошибок

### 5. Configuration Layer

```mermaid
graph TD
    Env[.env File] -->|Load| Settings[Pydantic Settings]
    
    Settings -->|GigaChat Config| LLM[LLM Layer]
    Settings -->|MCP Config| Tools[Tools Layer]
    Settings -->|API Config| API[API Layer]
    Settings -->|Agent Config| Graph[Graph Layer]
    
    style Settings fill:#673AB7,color:#fff
```

**Конфигурационные группы:**
- GigaChat (API key, model, temperature)
- MCP Server (URL, timeout, retries)
- Agent (iterations, execution time)
- Application (debug, logging)
- API (host, port, CORS)

## Поток данных

### Типичный запрос (полный цикл)

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant CL as Classifier
    participant RD as Repair Days
    participant CO as Compliance
    participant DI as Dealer Insights
    participant RS as Report Summary
    participant M as MCP Server
    
    C->>A: POST /agent/query
    A->>CL: Execute classifier_node
    CL->>CL: Analyze query
    CL-->>A: Classification result
    
    par Parallel Execution
        A->>RD: Execute if needed
        RD->>M: warranty_days(vin)
        M-->>RD: Days data
        RD->>RD: Analyze with LLM
        
        A->>CO: Execute if needed
        CO->>M: compliance_rag(query)
        M-->>CO: Compliance data
        CO->>CO: Interpret with LLM
        
        A->>DI: Execute if needed
        DI->>M: warranty_history(vin)
        DI->>M: maintenance_history(vin)
        DI->>M: vehicle_repairs_history(vin)
        M-->>DI: History data
        DI->>DI: Analyze with LLM
    end
    
    A->>RS: Execute report_summary_node
    RS->>RS: Aggregate results
    RS->>RS: Generate report with LLM
    RS-->>A: Final response
    
    A-->>C: JSON Response
```

## Обработка ошибок

```mermaid
graph TD
    Start[Error Occurs] --> Type{Error Type}
    
    Type -->|MCP Error| MCP[Log & Continue]
    Type -->|LLM Error| LLM[Retry or Fallback]
    Type -->|Validation Error| Val[Return 422]
    Type -->|System Error| Sys[Return 500]
    
    MCP --> State[Update State]
    LLM --> State
    State --> Continue[Continue Execution]
    
    Val --> Client[Return to Client]
    Sys --> Client
    
    Continue --> Check{All Agents Done?}
    Check -->|Yes| Report[Generate Report]
    Check -->|No| Next[Next Agent]
    
    Report --> Client
    Next --> Continue
    
    style Start fill:#f44336,color:#fff
    style Continue fill:#4caf50,color:#fff
```

**Стратегии обработки:**
1. **MCP ошибки** - логируются, агент продолжает с частичными данными
2. **LLM ошибки** - retry с exponential backoff
3. **Validation ошибки** - немедленный возврат 422
4. **System ошибки** - логирование, возврат 500

## Масштабирование и производительность

### Оптимизации

1. **Параллельное выполнение агентов**
   - LangGraph автоматически запускает независимые узлы параллельно
   - Repair Days, Compliance, Dealer Insights выполняются одновременно

2. **Кэширование**
   - MCP результаты кэшируются на 5 минут
   - LLM инстансы переиспользуются

3. **Асинхронность**
   - Все I/O операции асинхронные
   - Используется asyncio и httpx

### Метрики производительности

| Метрика | Значение |
|---------|----------|
| Средняя задержка (1 агент) | 2-3 сек |
| Средняя задержка (3 агента) | 4-6 сек |
| MCP запрос | 200-500 мс |
| LLM генерация | 1-3 сек |
| Кэш hit rate | ~60-70% |

## Безопасность

### Валидация входных данных

```mermaid
graph LR
    Input[User Input] --> VIN[VIN Validator]
    Input --> Query[Query Length Check]
    
    VIN --> Valid{Valid?}
    Query --> Valid
    
    Valid -->|Yes| Process[Process Request]
    Valid -->|No| Reject[Return 422]
    
    style Reject fill:#f44336,color:#fff
    style Process fill:#4caf50,color:#fff
```

### Меры безопасности

1. **Input Validation**
   - VIN: 17 символов, regex паттерн
   - Query: 3-1000 символов
   - Pydantic схемы для всех входных данных

2. **API Security**
   - CORS настройки
   - Rate limiting (будущее)
   - API ключи (будущее)

3. **Data Privacy**
   - Логи не содержат PII
   - VIN не логируется полностью
   - Кэш очищается по TTL

## Мониторинг и наблюдаемость

### Логирование

```python
# Уровни логирования
DEBUG   # Детальная трассировка
INFO    # Основные события
WARNING # Потенциальные проблемы
ERROR   # Ошибки выполнения
```

### Метрики (собираются в state)

- Execution time
- Steps completed
- Agents used
- Errors count
- Cache hits/misses

### Health Checks

```
GET /health
- API status
- MCP connection status
- LLM availability
```

## Будущие улучшения

1. **Streaming responses** - поддержка SSE для real-time обновлений
2. **Persistent memory** - сохранение истории диалогов
3. **Human-in-the-loop** - запрос подтверждений у пользователя
4. **Multi-modal** - обработка изображений документов
5. **Analytics dashboard** - визуализация метрик
6. **A/B testing** - эксперименты с промптами
