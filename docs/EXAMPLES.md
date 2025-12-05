# Примеры использования Warranty Agent System

## Примеры запросов к API

### 1. Анализ дней простоя в ремонте

**Запрос:**
```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Сколько дней в 2023 году автомобиль находился в ремонте? Есть ли риск превышения 30-дневного лимита?",
    "vin": "WBADT43452G123456"
  }'
```

**Что происходит:**
- Classifier определяет, что нужен Repair Days Tracker
- Repair Days Tracker вызывает `warranty_days(vin)` через MCP
- Анализирует данные и проверяет 30-дневный лимит
- Report & Summary генерирует итоговый отчёт

**Пример ответа:**
```json
{
  "success": true,
  "query": "Сколько дней в 2023 году...",
  "vin": "WBADT43452G123456",
  "response": "# Анализ дней простоя в ремонте\n\n## Статистика за 2023 год\n\nВаш автомобиль находился в гарантийном ремонте **23 дня** в течение 2023 года.\n\n## Соблюдение лимита\n\n✅ 30-дневный лимит НЕ превышен (использовано 76.7%)\n\n## Риски\n\nТекущий запас до лимита: 7 дней. При планировании следующего ремонта учитывайте этот остаток...",
  "agents_used": ["Repair Days Tracker"],
  "execution_time_seconds": 3.45
}
```

### 2. Вопрос о правах потребителя

**Запрос:**
```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Какие у меня права, если автомобиль более 30 дней находится в ремонте? Могу ли я требовать замены автомобиля?"
  }'
```

**Что происходит:**
- Classifier определяет, что нужен Warranty Compliance
- Warranty Compliance вызывает `compliance_rag(query)` для поиска в базе знаний
- Интерпретирует законодательство и гарантийную политику
- Объясняет права и обязанности

**Пример ответа:**
```json
{
  "success": true,
  "query": "Какие у меня права...",
  "response": "# Ваши права при превышении 30-дневного лимита\n\n## Законодательная база\n\nСогласно статье 18 Закона РФ \"О защите прав потребителей\", если недостаток товара не устранён в течение 30 дней, потребитель вправе:\n\n1. Потребовать замены на товар аналогичной марки\n2. Потребовать замены на товар другой марки с перерасчётом цены\n3. Потребовать возврата уплаченной суммы\n\n## Ваши действия...",
  "agents_used": ["Warranty Compliance"]
}
```

### 3. Анализ истории ремонтов

**Запрос:**
```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Проанализируй всю историю ремонтов автомобиля. Есть ли повторяющиеся проблемы? Качественно ли работает дилер?",
    "vin": "WBADT43452G123456"
  }'
```

**Что происходит:**
- Classifier определяет, что нужен Dealer Insights
- Dealer Insights вызывает три MCP инструмента:
  - `warranty_history(vin)`
  - `maintenance_history(vin)`
  - `vehicle_repairs_history(vin)`
- Анализирует паттерны и проблемы
- Оценивает качество работы дилера

**Пример ответа:**
```json
{
  "success": true,
  "query": "Проанализируй всю историю...",
  "vin": "WBADT43452G123456",
  "response": "# Анализ истории ремонтов\n\n## Общая статистика\n\n- Всего обращений: 8\n- Гарантийных ремонтов: 5\n- ТО: 3\n- Период: 2021-2024\n\n## Выявленные паттерны\n\n⚠️ Обнаружена повторяющаяся проблема:\n- Система охлаждения двигателя ремонтировалась 3 раза (2022, 2023, 2024)\n- Замена термостата (2 раза)\n- Замена помпы (1 раз)\n\nВозможна системная неисправность...",
  "agents_used": ["Dealer Insights"]
}
```

### 4. Комплексный анализ

**Запрос:**
```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Составь полный отчёт по автомобилю WBADT43452G123456: сколько дней был в ремонте, какие были проблемы, какие у меня права",
    "vin": "WBADT43452G123456"
  }'
```

**Что происходит:**
- Classifier определяет, что нужны ВСЕ три агента
- Repair Days Tracker, Compliance и Dealer Insights работают **параллельно**
- Report & Summary объединяет результаты всех агентов
- Создаётся комплексный отчёт

**Пример ответа:**
```json
{
  "success": true,
  "query": "Составь полный отчёт...",
  "vin": "WBADT43452G123456",
  "response": "# ПОЛНЫЙ ОТЧЁТ ПО АВТОМОБИЛЮ\n\n**VIN:** WBADT43452G123456\n**Дата отчёта:** 15.01.2024\n\n---\n\n## 1. АНАЛИЗ ДНЕЙ ПРОСТОЯ\n\n### За 2023 год\nАвтомобиль находился в ремонте **28 дней**\n- Январь: 5 дней\n- Апрель: 12 дней\n- Октябрь: 11 дней\n\n⚠️ ВНИМАНИЕ: Близко к 30-дневному лимиту (93.3%)\n\n---\n\n## 2. ИСТОРИЯ РЕМОНТОВ И ПРОБЛЕМЫ\n\n### Выявленные паттерны\n...\n\n---\n\n## 3. ВАШИ ПРАВА И РЕКОМЕНДАЦИИ\n\n...",
  "agents_used": [
    "Repair Days Tracker",
    "Warranty Compliance",
    "Dealer Insights"
  ],
  "execution_time_seconds": 5.23
}
```

## Примеры использования из Python

### Простой запрос

```python
import requests
import json

def query_agent(query, vin=None):
    response = requests.post(
        'http://localhost:8005/agent/query',
        json={
            'query': query,
            'vin': vin,
            'context': {}
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(result['response'])
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Использование
query_agent(
    "Сколько дней автомобиль был в ремонте?",
    "WBADT43452G123456"
)
```

### Асинхронный запрос

```python
import httpx
import asyncio

async def query_agent_async(query, vin=None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8005/agent/query',
            json={
                'query': query,
                'vin': vin,
                'context': {}
            },
            timeout=30.0
        )
        
        return response.json()

# Использование
result = asyncio.run(query_agent_async(
    "Проанализируй историю ремонтов",
    "WBADT43452G123456"
))
print(result['response'])
```

### Обработка ошибок

```python
import requests
from typing import Optional

def safe_query(query: str, vin: Optional[str] = None) -> dict:
    try:
        response = requests.post(
            'http://localhost:8005/agent/query',
            json={'query': query, 'vin': vin},
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        if not result['success']:
            print(f"Query failed with errors: {result['errors']}")
        
        return result
        
    except requests.exceptions.Timeout:
        print("Request timed out")
        return {'error': 'timeout'}
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return {'error': str(e)}

# Использование
result = safe_query("Мой запрос", "WBADT43452G123456")
if 'error' not in result:
    print(result['response'])
```

## CLI примеры

### Тестовый запрос через CLI

```bash
# С Poetry
poetry run python -m backend.agent.main test \
  "Сколько дней автомобиль был в ремонте?" \
  WBADT43452G123456

# С python
python -m backend.agent.main test \
  "Какие у меня права?" \
  WBADT43452G123456
```

### Запуск сервера

```bash
# Обычный режим
poetry run python -m backend.agent.main server

# С auto-reload (для разработки)
# Установите в .env: API_RELOAD=true
poetry run python -m backend.agent.main server
```

## Типичные сценарии использования

### Сценарий 1: Проверка перед покупкой б/у автомобиля

```python
import requests

def check_used_car(vin: str):
    """Комплексная проверка автомобиля перед покупкой."""
    
    response = requests.post(
        'http://localhost:8005/agent/query',
        json={
            'query': f'''
                Проанализируй полную историю автомобиля:
                1. Сколько раз и по каким причинам он был в ремонте?
                2. Есть ли повторяющиеся проблемы?
                3. Как часто проходило ТО?
                4. Есть ли признаки серьёзных неисправностей?
            ''',
            'vin': vin
        }
    )
    
    return response.json()

# Использование
report = check_used_car('WBADT43452G123456')
print(report['response'])
```

### Сценарий 2: Подготовка к суду

```python
def prepare_legal_case(vin: str):
    """Подготовка документов для судебного разбирательства."""
    
    response = requests.post(
        'http://localhost:8005/agent/query',
        json={
            'query': f'''
                Составь детальную справку для суда:
                1. Точное количество дней в ремонте по годам
                2. Факты превышения 30-дневного лимита
                3. Описание моих прав согласно закону
                4. Хронология всех обращений
                5. Доказательства некачественного ремонта
            ''',
            'vin': vin
        }
    )
    
    result = response.json()
    
    # Сохранить в файл
    with open(f'legal_report_{vin}.txt', 'w', encoding='utf-8') as f:
        f.write(result['response'])
    
    return result

# Использование
prepare_legal_case('WBADT43452G123456')
```

### Сценарий 3: Мониторинг текущего ремонта

```python
def monitor_current_repair(vin: str):
    """Отслеживание текущего ремонта и рисков."""
    
    response = requests.post(
        'http://localhost:8005/agent/query',
        json={
            'query': f'''
                Автомобиль сейчас в ремонте. Проанализируй:
                1. Сколько дней уже было потрачено в этом году?
                2. Какой запас до 30-дневного лимита?
                3. Что делать, если ремонт затянется?
                4. Какие права у меня возникнут при превышении лимита?
            ''',
            'vin': vin
        }
    )
    
    return response.json()

# Использование
status = monitor_current_repair('WBADT43452G123456')
print(status['response'])
```

## Интеграция с другими системами

### Webhook для уведомлений

```python
import requests
from typing import Callable

def setup_warranty_alert(
    vin: str,
    callback: Callable[[dict], None]
):
    """Настройка автоматических уведомлений."""
    
    # Проверка текущего статуса
    result = requests.post(
        'http://localhost:8005/agent/query',
        json={
            'query': 'Сколько дней осталось до 30-дневного лимита?',
            'vin': vin
        }
    ).json()
    
    # Если близко к лимиту - вызвать callback
    if '30' in result['response'] and 'превышен' in result['response']:
        callback(result)

# Пример callback
def send_notification(result):
    print(f"ВНИМАНИЕ: {result['response']}")
    # Здесь можно отправить email, SMS и т.д.

# Использование
setup_warranty_alert('WBADT43452G123456', send_notification)
```
