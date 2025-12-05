# Files Index - Warranty Agent System

Полный индекс всех файлов проекта с описанием их назначения.

## Core Files

### Configuration & Entry Points

| File | Description | Lines | Type |
|------|-------------|-------|------|
| `config.py` | Централизованная конфигурация с Pydantic Settings | ~180 | Config |
| `main.py` | Entry point с CLI командами | ~130 | Entry |
| `__init__.py` | Package initialization | ~15 | Module |

### Dependencies

| File | Description | Lines | Type |
|------|-------------|-------|------|
| `pyproject.toml` | Poetry зависимости и настройки | ~60 | Config |
| `requirements.txt` | pip зависимости | ~20 | Config |
| `.env.example` | Шаблон переменных окружения | ~25 | Config |

## Graph Layer (`graph/`)

### State Management

| File | Description | Lines | Type |
|------|-------------|-------|------|
| `graph/state.py` | AgentState schema с Pydantic | ~120 | Model |
| `graph/graph_builder.py` | StateGraph construction и execution | ~170 | Core |
| `graph/edges.py` | Routing logic между узлами | ~100 | Logic |
| `graph/__init__.py` | Package exports | ~20 | Module |

### Nodes (`graph/nodes/`)

| File | Description | Lines | Type |
|------|-------------|-------|------|
| `graph/nodes/classifier.py` | Query classification node | ~140 | Node |
| `graph/nodes/repair_days.py` | Repair days analysis node | ~100 | Node |
| `graph/nodes/compliance.py` | Warranty compliance node | ~110 | Node |
| `graph/nodes/dealer_insights.py` | Dealer insights analysis node | ~120 | Node |
| `graph/nodes/report_summary.py` | Report generation node | ~130 | Node |
| `graph/nodes/aggregator.py` | Response aggregation node | ~90 | Node |
| `graph/nodes/__init__.py` | Nodes package exports | ~15 | Module |

**Total Nodes:** 6
**Total Lines:** ~835

## LLM Layer (`llm/`)

| File | Description | Lines | Type |
|------|-------------|-------|------|
| `llm/gigachat_setup.py` | GigaChat LLM initialization | ~90 | Setup |
| `llm/prompts.py` | Промпты для всех агентов (русский) | ~270 | Prompts |
| `llm/__init__.py` | Package exports | ~25 | Module |

**Total Lines:** ~385

## Tools Layer (`tools/`)

| File | Description | Lines | Type |
|------|-------------|-------|------|
| `tools/mcp_client.py` | Асинхронный MCP HTTP клиент | ~280 | Client |
| `tools/langchain_tools.py` | LangChain tool wrappers (5 tools) | ~250 | Tools |
| `tools/__init__.py` | Package exports | ~20 | Module |

**Total Lines:** ~550

**Available Tools:**
1. WarrantyDaysTool
2. WarrantyHistoryTool
3. MaintenanceHistoryTool
4. VehicleRepairsHistoryTool
5. ComplianceRAGTool

## Utilities (`utils/`)

| File | Description | Lines | Type |
|------|-------------|-------|------|
| `utils/vin_validator.py` | VIN validation и parsing | ~140 | Utility |
| `utils/formatters.py` | Output formatters (даты, валюта, таблицы) | ~200 | Utility |
| `utils/__init__.py` | Package exports | ~25 | Module |

**Total Lines:** ~365

## API Layer (`api/`)

| File | Description | Lines | Type |
|------|-------------|-------|------|
| `api/app.py` | FastAPI application с endpoints | ~180 | API |
| `api/schemas.py` | Pydantic request/response schemas | ~140 | Models |
| `api/__init__.py` | Package exports | ~15 | Module |

**Total Lines:** ~335

**Endpoints:**
- `POST /agent/query` - Execute query
- `GET /health` - Health check
- `GET /` - API info
- `GET /docs` - Swagger UI

## Documentation

| File | Description | Lines | Type |
|------|-------------|-------|------|
| `README.md` | Полная документация проекта | ~250 | Docs |
| `QUICKSTART.md` | Руководство быстрого старта | ~150 | Docs |
| `EXAMPLES.md` | Примеры использования API | ~400 | Docs |
| `ARCHITECTURE.md` | Архитектурная документация | ~450 | Docs |
| `INSTALLATION.md` | Детальное руководство по установке | ~350 | Docs |
| `PROJECT_SUMMARY.md` | Итоговый отчёт по проекту | ~450 | Docs |
| `CHANGELOG.md` | История изменений | ~200 | Docs |
| `FILES_INDEX.md` | Этот файл | ~150 | Docs |

**Total Documentation Lines:** ~2,400

## Deployment & Configuration

| File | Description | Lines | Type |
|------|-------------|-------|------|
| `warranty-agent.service` | systemd service file | ~25 | Deploy |
| `.gitignore` | Git ignore rules | ~40 | Config |

## Statistics

### Code Statistics

```
Total Python Files: 26
Total Documentation Files: 8
Total Configuration Files: 4

Python Code Lines: ~2,600
Documentation Lines: ~2,400
Configuration Lines: ~150

Total Project Lines: ~5,150
```

### File Size Distribution

| Category | Files | Lines | Percentage |
|----------|-------|-------|------------|
| Python Code | 26 | 2,600 | 50.5% |
| Documentation | 8 | 2,400 | 46.6% |
| Configuration | 4 | 150 | 2.9% |

### Code by Layer

| Layer | Files | Lines | Percentage |
|-------|-------|-------|------------|
| Graph (Nodes + State) | 8 | 1,090 | 42.0% |
| Tools (MCP + LangChain) | 3 | 550 | 21.2% |
| LLM (GigaChat + Prompts) | 3 | 385 | 14.8% |
| API (FastAPI) | 3 | 335 | 12.9% |
| Utils | 3 | 365 | 14.0% |
| Core (Config + Main) | 3 | 325 | 12.5% |

## File Dependencies Graph

```
config.py
  └─> llm/gigachat_setup.py
  └─> tools/mcp_client.py
  └─> api/app.py

main.py
  └─> config.py
  └─> api/app.py
  └─> graph/graph_builder.py

graph/graph_builder.py
  └─> graph/state.py
  └─> graph/nodes/*.py
  └─> graph/edges.py

graph/nodes/*.py
  └─> graph/state.py
  └─> llm/gigachat_setup.py
  └─> llm/prompts.py
  └─> tools/mcp_client.py

api/app.py
  └─> api/schemas.py
  └─> graph/graph_builder.py
  └─> utils/vin_validator.py
```

## Critical Files (Must Read First)

1. **config.py** - Конфигурация системы
2. **graph/state.py** - Структура данных
3. **graph/graph_builder.py** - Основной граф
4. **main.py** - Entry point
5. **README.md** - Документация

## Quick Navigation

### For Developers

- **Start Here:** `README.md` → `QUICKSTART.md`
- **Architecture:** `ARCHITECTURE.md`
- **API Usage:** `EXAMPLES.md`
- **Code Entry:** `main.py` → `graph/graph_builder.py`

### For Operators

- **Installation:** `INSTALLATION.md`
- **Deployment:** `warranty-agent.service`
- **Configuration:** `.env.example`
- **Troubleshooting:** `README.md#troubleshooting`

### For Users

- **Quick Start:** `QUICKSTART.md`
- **API Examples:** `EXAMPLES.md`
- **API Docs:** http://localhost:8005/docs

## File Naming Conventions

### Python Files
- `snake_case.py` - все Python файлы
- `__init__.py` - package initialization
- `test_*.py` - тестовые файлы (будущее)

### Documentation
- `UPPERCASE.md` - основная документация
- `README.md` - главная документация
- `CHANGELOG.md` - история изменений

### Configuration
- `.env` - переменные окружения
- `.gitignore` - git ignore
- `*.toml` - TOML конфигурация
- `*.txt` - текстовые файлы

## Modification Frequency

| File | Freq | Reason |
|------|------|--------|
| `graph/nodes/*.py` | High | Улучшение агентов |
| `llm/prompts.py` | High | Оптимизация промптов |
| `api/app.py` | Medium | Новые endpoints |
| `config.py` | Low | Новые настройки |
| `graph/graph_builder.py` | Low | Изменение структуры графа |

## Testing Files (Future)

```
tests/
├── test_graph/
│   ├── test_state.py
│   ├── test_nodes.py
│   └── test_edges.py
├── test_tools/
│   ├── test_mcp_client.py
│   └── test_langchain_tools.py
├── test_llm/
│   └── test_prompts.py
├── test_api/
│   └── test_app.py
└── test_utils/
    └── test_validators.py
```

**Status:** Not yet implemented (v0.2.0)

## File Access Patterns

### Startup
1. `.env` → `config.py`
2. `main.py`
3. `api/app.py` → `graph/graph_builder.py`
4. `tools/mcp_client.py` (connection)

### Request Processing
1. `api/app.py` (receive)
2. `graph/graph_builder.py` (invoke)
3. `graph/nodes/classifier.py` (route)
4. `graph/nodes/*.py` (execute)
5. `tools/mcp_client.py` (fetch data)
6. `llm/gigachat_setup.py` (LLM)
7. `api/app.py` (response)

## Backup Priority

### Critical (Daily Backup)
- `config.py`
- `graph/nodes/*.py`
- `llm/prompts.py`
- `.env` (if modified)

### Important (Weekly Backup)
- `graph/graph_builder.py`
- `api/app.py`
- `tools/mcp_client.py`

### Optional (Monthly Backup)
- Documentation files
- Configuration templates

---

**Last Updated:** 2024-12-05
**Project Version:** 0.1.0
**Total Files:** 38
**Total Size:** ~5,150 lines
