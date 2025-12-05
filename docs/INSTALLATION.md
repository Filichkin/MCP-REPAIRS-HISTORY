# Installation Guide

Детальное руководство по установке Warranty Agent System.

## Системные требования

### Операционная система

- macOS 10.15+ (Catalina и выше)
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- Windows 10/11 (с WSL2 рекомендуется)

### Программное обеспечение

- **Python**: 3.11 или выше
- **pip**: 23.0 или выше
- **Poetry**: 1.7.0 или выше (опционально, но рекомендуется)
- **Git**: для клонирования репозитория

### Внешние сервисы

- **GigaChat API**: активный API ключ
- **MCP Server**: запущенный на порту 8004

### Аппаратные требования

- **CPU**: 2+ ядра
- **RAM**: 4GB минимум, 8GB рекомендуется
- **Disk**: 2GB свободного места

## Способы установки

### Способ 1: Poetry (рекомендуется)

Poetry управляет зависимостями и виртуальным окружением автоматически.

#### 1.1. Установка Poetry

**macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Windows (PowerShell):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Добавьте Poetry в PATH:
```bash
# macOS/Linux (добавьте в ~/.bashrc или ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

#### 1.2. Клонирование репозитория

```bash
cd /path/to/your/projects
git clone <repository-url>
cd MCP-REPAIRS-HISTORY/backend/agent
```

#### 1.3. Установка зависимостей

```bash
poetry install
```

Это создаст виртуальное окружение и установит все зависимости.

#### 1.4. Активация окружения

```bash
poetry shell
```

Или используйте `poetry run` перед командами:
```bash
poetry run python -m backend.agent.main server
```

### Способ 2: pip + venv

Традиционный подход с pip и виртуальным окружением.

#### 2.1. Клонирование репозитория

```bash
cd /path/to/your/projects
git clone <repository-url>
cd MCP-REPAIRS-HISTORY/backend/agent
```

#### 2.2. Создание виртуального окружения

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### 2.3. Обновление pip

```bash
pip install --upgrade pip
```

#### 2.4. Установка зависимостей

```bash
pip install -r requirements.txt
```

### Способ 3: System-wide установка (не рекомендуется)

```bash
pip install -r requirements.txt
```

Не рекомендуется, так как может вызвать конфликты зависимостей.

## Настройка переменных окружения

### 1. Создание .env файла

Скопируйте шаблон:
```bash
cd /path/to/MCP-REPAIRS-HISTORY
cp .env.example .env
```

### 2. Редактирование .env

Откройте `.env` в текстовом редакторе:
```bash
nano .env
# или
vim .env
# или
code .env  # VS Code
```

### 3. Обязательные переменные

```env
# GigaChat API ключ (ОБЯЗАТЕЛЬНО)
GIGACHAT_API_KEY=ваш_реальный_ключ_здесь

# MCP Server URL
MCP_SERVER_URL=http://localhost:8004
```

### 4. Опциональные переменные

```env
# GigaChat настройки
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat
GIGACHAT_TEMPERATURE=0.7

# MCP настройки
MCP_TIMEOUT=30
MCP_MAX_RETRIES=3

# API настройки
API_HOST=0.0.0.0
API_PORT=8005

# Логирование
LOG_LEVEL=INFO
APP_DEBUG=false
```

## Получение GigaChat API ключа

### Шаг 1: Регистрация

1. Перейдите на https://developers.sber.ru/
2. Нажмите "Войти" или "Зарегистрироваться"
3. Войдите через Сбер ID или создайте аккаунт

### Шаг 2: Создание проекта

1. В личном кабинете нажмите "Создать проект"
2. Выберите "GigaChat API"
3. Укажите название проекта
4. Выберите scope: `GIGACHAT_API_PERS` (персональный) или `GIGACHAT_API_CORP` (корпоративный)

### Шаг 3: Получение ключа

1. В разделе "Учётные данные" скопируйте API ключ
2. Вставьте его в `.env` файл как `GIGACHAT_API_KEY`

### Шаг 4: Проверка квот

- Бесплатный план: 1000 запросов/день
- Платные планы: см. на сайте

## Установка и настройка MCP Server

MCP Server должен быть запущен перед запуском Agent System.

### 1. Переход в директорию MCP

```bash
cd /path/to/MCP-REPAIRS-HISTORY/backend/mcp_server
```

### 2. Установка зависимостей (если не установлены)

```bash
pip install -r requirements.txt
```

### 3. Настройка базы данных

Убедитесь, что база данных настроена согласно документации MCP Server.

### 4. Запуск MCP Server

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8004
```

Или в фоновом режиме:
```bash
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8004 > mcp.log 2>&1 &
```

### 5. Проверка работы

```bash
curl http://localhost:8004/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy"
}
```

## Проверка установки

### 1. Проверка Python версии

```bash
python --version
# Должно быть: Python 3.11.x или выше
```

### 2. Проверка зависимостей

**С Poetry:**
```bash
poetry show
```

**С pip:**
```bash
pip list
```

Убедитесь, что установлены:
- langchain
- langgraph
- langchain-gigachat
- fastapi
- uvicorn

### 3. Проверка импортов

```bash
python -c "import langchain; import langgraph; from langchain_gigachat import GigaChat; print('OK')"
```

Должно вывести: `OK`

### 4. Проверка конфигурации

```bash
cd /path/to/MCP-REPAIRS-HISTORY/backend/agent
python -c "from backend.agent.config import settings; print(f'Config loaded: {settings.app_name}')"
```

Если ошибка про GIGACHAT_API_KEY - проверьте `.env` файл.

## Первый запуск

### 1. Проверка health endpoint MCP

```bash
curl http://localhost:8004/health
```

### 2. Запуск Agent System

**С Poetry:**
```bash
cd /path/to/MCP-REPAIRS-HISTORY/backend/agent
poetry run python -m backend.agent.main server
```

**С pip:**
```bash
cd /path/to/MCP-REPAIRS-HISTORY/backend/agent
source .venv/bin/activate  # если используется venv
python -m backend.agent.main server
```

### 3. Проверка запуска

В логах должно появиться:
```
INFO     | Logging configured
INFO     | Warranty Agent System v0.1.0
INFO     | MCP client initialized
INFO     | Starting server on 0.0.0.0:8005
INFO     | Application startup complete
```

### 4. Health check Agent

В новом терминале:
```bash
curl http://localhost:8005/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "mcp_server_status": "connected",
  "llm_status": "ready"
}
```

### 5. Тестовый запрос

```bash
curl -X POST http://localhost:8005/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Какие у меня права при превышении 30 дней ремонта?"
  }'
```

Должен вернуться JSON с полным ответом.

## Troubleshooting

### Проблема: ModuleNotFoundError

**Симптом:**
```
ModuleNotFoundError: No module named 'langchain'
```

**Решение:**
1. Убедитесь, что виртуальное окружение активировано
2. Переустановите зависимости: `poetry install` или `pip install -r requirements.txt`

### Проблема: GIGACHAT_API_KEY must be set

**Симптом:**
```
ValueError: GIGACHAT_API_KEY must be set to a valid API key in .env file
```

**Решение:**
1. Проверьте, что `.env` файл существует в корне проекта
2. Убедитесь, что `GIGACHAT_API_KEY` установлен и не равен `your_key_here`
3. Проверьте путь: `.env` должен быть в `/path/to/MCP-REPAIRS-HISTORY/.env`

### Проблема: MCP server connection error

**Симптом:**
```
MCPConnectionError: Connection error calling tool...
```

**Решение:**
1. Убедитесь, что MCP Server запущен: `curl http://localhost:8004/health`
2. Проверьте `MCP_SERVER_URL` в `.env`
3. Проверьте firewall/порты

### Проблема: Port 8005 already in use

**Симптом:**
```
OSError: [Errno 48] Address already in use
```

**Решение:**
1. Найдите процесс: `lsof -i :8005`
2. Убейте процесс: `kill -9 <PID>`
3. Или измените порт в `.env`: `API_PORT=8006`

### Проблема: SSL/Certificate errors

**Симптом:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Решение:**
В `gigachat_setup.py` уже установлено `verify_ssl_certs=False` для development.
Для production настройте правильные сертификаты.

### Проблема: Slow response times

**Возможные причины:**
1. GigaChat API throttling - проверьте квоты
2. MCP Server перегружен - проверьте логи MCP
3. Нет кэша - первый запрос всегда медленнее

**Решение:**
1. Включите кэширование: `MCP_CACHE_TTL=300` в `.env`
2. Увеличьте timeout: `GIGACHAT_TIMEOUT=120`

## Upgrade инструкция

### Обновление с предыдущей версии

```bash
cd /path/to/MCP-REPAIRS-HISTORY/backend/agent

# С Poetry
poetry update

# С pip
pip install --upgrade -r requirements.txt
```

### Миграция конфигурации

Проверьте `.env.example` на новые переменные и добавьте их в свой `.env`.

## Uninstall

### Удаление с Poetry

```bash
cd /path/to/MCP-REPAIRS-HISTORY/backend/agent
poetry env remove python
rm -rf .venv
```

### Удаление с pip

```bash
deactivate  # если окружение активировано
rm -rf .venv
```

### Удаление системной установки

```bash
pip uninstall -r requirements.txt
```

## Next Steps

После успешной установки:

1. Изучите [QUICKSTART.md](QUICKSTART.md) для быстрого старта
2. Прочитайте [README.md](README.md) для полной документации
3. Посмотрите [EXAMPLES.md](EXAMPLES.md) для примеров использования
4. Изучите [ARCHITECTURE.md](ARCHITECTURE.md) для понимания архитектуры

## Support

При возникновении проблем:

1. Проверьте логи: `tail -f logs/agent_*.log`
2. Включите debug: `APP_DEBUG=true LOG_LEVEL=DEBUG` в `.env`
3. Проверьте health endpoints
4. Обратитесь к troubleshooting секции выше

Удачи с использованием Warranty Agent System!
