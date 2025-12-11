# Документация по контейнеризации проекта MCP-REPAIRS-HISTORY

## Обзор

Проект разделен на три независимых микросервиса, каждый из которых контейнеризирован с использованием Docker и оптимизирован для production-окружения.

## Архитектура

### Структура проекта

```
MCP-REPAIRS-HISTORY/
├── backend/
│   ├── mcp_server/          # MCP Server - инструменты для работы с данными
│   │   ├── config.py        # Конфигурация MCP сервера
│   │   ├── requirements.txt # Зависимости только для MCP сервера
│   │   └── server.py        # Основной сервер
│   └── agent/               # Agent System - мульти-агентная система анализа
│       ├── config.py        # Конфигурация агентной системы
│       ├── requirements.txt # Зависимости только для агентов
│       └── main.py          # Точка входа
├── frontend/                # Gradio UI
│   ├── config.py           # Конфигурация фронтенда
│   ├── requirements.txt    # Зависимости только для фронтенда
│   └── app.py              # Gradio приложение
├── infra/                  # Инфраструктура и конфигурация
│   ├── .env                # Переменные окружения
│   └── nginx/              # Nginx конфигурация
├── Dockerfile.mcp          # Dockerfile для MCP сервера
├── Dockerfile.agent        # Dockerfile для агентной системы
├── Dockerfile.frontend     # Dockerfile для фронтенда
└── docker-compose.yml      # Оркестрация всех сервисов
```

## Компоненты системы

### 1. MCP Server (порт 8004)

**Назначение**: Предоставляет инструменты для работы с данными о ремонтах, гарантиях и технической документации через MCP (Model Context Protocol).

**Основные функции**:
- Получение истории ремонтов автомобиля
- Проверка гарантийных условий
- Анализ дней простоя
- Поиск в базе знаний (RAG)

**Зависимости**:
- fastmcp>=2.13.3
- mcp>=1.3.2
- starlette>=0.41.3
- httpx>=0.27.0
- pydantic>=2.5.0

**Health endpoint**: `http://localhost:8004/health`

### 2. Agent System (порт 8005)

**Назначение**: Мульти-агентная система для интеллектуального анализа гарантийных обращений с использованием LangGraph и GigaChat.

**Основные функции**:
- Классификация запросов пользователей
- Анализ дней в ремонте
- Проверка соответствия гарантийным условиям
- Анализ истории дилеров
- Генерация итоговых отчетов

**Зависимости**:
- langchain>=0.1.0
- langgraph>=0.0.40
- langchain-gigachat>=0.1.0
- fastapi>=0.109.0
- uvicorn[standard]>=0.34.0

**Health endpoint**: `http://localhost:8005/health`

### 3. Frontend (порт 7860)

**Назначение**: Web-интерфейс на базе Gradio для взаимодействия с агентной системой.

**Основные функции**:
- Интерактивный чат-интерфейс
- Отображение результатов анализа
- История диалогов

**Зависимости**:
- gradio>=4.0.0
- httpx>=0.27.0
- pydantic>=2.5.0

**Endpoint**: `http://localhost:7860`

## Docker образы

### Multi-stage сборка

Все три Dockerfile используют multi-stage сборку для оптимизации размера образов:

1. **Builder stage**: Устанавливает build-зависимости и собирает Python зависимости в виртуальном окружении
2. **Runtime stage**: Копирует только скомпилированные зависимости и код приложения

### Особенности образов

#### Dockerfile.mcp
```dockerfile
# Копирует только MCP сервер
COPY backend/mcp_server/ /app/mcp_server/

# Запускает сервер
CMD ["python", "-m", "mcp_server.server"]
```

#### Dockerfile.agent
```dockerfile
# Копирует только агентную систему
COPY backend/agent/ /app/agent/

# Запускает агентов
CMD ["python", "-m", "agent.main"]
```

#### Dockerfile.frontend
```dockerfile
# Копирует только фронтенд
COPY frontend/ /app/frontend/

# Запускает Gradio
CMD ["python", "app.py"]
```

### Безопасность

Все образы:
- Используют non-root пользователя `appuser` (UID 1000)
- Минимизированы для уменьшения поверхности атаки
- Включают только необходимые runtime зависимости
- Имеют health checks для мониторинга

## Docker Compose

### Режимы запуска

Docker Compose использует профили для гибкого управления компонентами системы.

#### 1. Только MCP Server (mcp profile)

```bash
docker compose --profile mcp up
```

Запускается только MCP сервер на порту 8004.

**Использование**:
- Разработка инструментов MCP
- Тестирование MCP endpoints
- Независимое использование MCP сервера

**Порты**: 8004

#### 2. Полная система (full profile)

```bash
docker compose --profile full up
```

Запускает все компоненты:
- MCP Server (8004)
- Agent System (8005)
- Frontend (7860)
- Nginx (80, 443)

**Использование**: Production deployment с полным стеком

**Порты**: 8004, 8005, 7860, 80, 443

#### 3. MCP + Agent (agent profile)

```bash
docker compose --profile agent up
```

Запускает:
- MCP Server (8004)
- Agent System (8005)

**Использование**: API-based интеграция без UI

**Порты**: 8004, 8005

#### 4. Полная система с UI (frontend profile)

```bash
docker compose --profile frontend up
```

Запускает все компоненты с фронтендом (без nginx):
- MCP Server (8004)
- Agent System (8005)
- Frontend (7860)

**Использование**: Разработка и тестирование с UI

**Порты**: 8004, 8005, 7860

#### 5. С Nginx Reverse Proxy (nginx profile)

```bash
docker compose --profile nginx up
```

Запускает:
- MCP Server (8004)
- Nginx (80, 443)

**Использование**: Production deployment с reverse proxy

**Порты**: 8004 (внутренний), 80, 443 (внешние)

### Сетевое взаимодействие

Все сервисы работают в изолированной сети `mcp-network`:

```
┌──────────────┐
│   Frontend   │ :7860
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Agent     │ :8005
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  MCP Server  │ :8004
└──────────────┘
```

### Dependencies и Health Checks

```yaml
agent:
  depends_on:
    mcp-server:
      condition: service_healthy

frontend:
  depends_on:
    agent:
      condition: service_healthy
```

Health checks обеспечивают:
- Правильный порядок запуска
- Готовность сервисов перед началом зависимых
- Автоматический restart при сбоях

## Управление зависимостями

### Разделение зависимостей

Каждый компонент имеет свой `requirements.txt`:

**backend/mcp_server/requirements.txt**:
- Только MCP и web framework зависимости
- Минимальный набор для работы с данными

**backend/agent/requirements.txt**:
- LangChain, LangGraph
- GigaChat
- FastAPI для API

**frontend/requirements.txt**:
- Gradio
- HTTP клиент для взаимодействия с Agent API

### Преимущества разделения

1. **Меньший размер образов**: Каждый контейнер содержит только необходимые зависимости
2. **Быстрая сборка**: Изменения в одном компоненте не требуют пересборки других
3. **Безопасность**: Минимизация зависимостей = меньше уязвимостей
4. **Масштабируемость**: Независимое масштабирование компонентов

## Конфигурация

### Переменные окружения

Все сервисы используют файл `infra/.env`:

```bash
# MCP Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8004
MCP_TRANSPORT=http

# Agent System
API_HOST=0.0.0.0
API_PORT=8005
GIGACHAT_API_KEY=your-key-here

# Frontend
UI_SERVER_NAME=0.0.0.0
UI_SERVER_PORT=7860
API_BASE_URL=http://agent:8005
```

### Конфигурация через docker-compose

Переменные окружения можно переопределить в `docker-compose.yml`:

```yaml
environment:
  - MCP_SERVER_URL=http://mcp-server:8004
  - API_BASE_URL=http://agent:8005
```

## Команды для работы

### Сборка образов

```bash
# Сборка всех образов
docker-compose build

# Сборка конкретного образа
docker-compose build mcp-server
docker-compose build agent
docker-compose build frontend
```

### Запуск сервисов

```bash
# Только MCP Server
docker-compose up mcp-server

# Весь стек
docker-compose --profile full up

# В фоновом режиме
docker-compose --profile full up -d

# С пересборкой
docker-compose --profile full up --build
```

### Остановка и очистка

```bash
# Остановка всех сервисов
docker-compose down

# Остановка с удалением volumes
docker-compose down -v

# Удаление образов
docker-compose down --rmi all
```

### Просмотр логов

```bash
# Все логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f mcp-server
docker-compose logs -f agent
docker-compose logs -f frontend
```

### Мониторинг

```bash
# Статус сервисов
docker-compose ps

# Использование ресурсов
docker stats
```

## SSL/TLS Configuration

### Генерация Self-Signed сертификатов

Для локальной разработки и тестирования используйте скрипт генерации self-signed сертификатов:

```bash
./infra/scripts/generate-ssl-certs.sh
```

Скрипт создаст:
- `/infra/certs/mcp-server.crt` - SSL сертификат
- `/infra/certs/mcp-server.key` - приватный ключ

**Важно**: Self-signed сертификаты предназначены только для разработки!

### Настройка HTTPS в nginx

1. Сгенерируйте сертификаты (см. выше)
2. Отредактируйте `infra/nginx/conf.d/mcp-server.conf`:
   - Раскомментируйте блок HTTPS сервера
   - Раскомментируйте редирект с HTTP на HTTPS
3. Перезапустите nginx:
   ```bash
   docker compose --profile nginx restart nginx
   ```

### Production SSL сертификаты

Для production используйте:

1. **Let's Encrypt** (рекомендуется):
   ```bash
   # Используйте certbot для получения бесплатного сертификата
   certbot certonly --standalone -d yourdomain.com
   ```

2. **Корпоративный CA**:
   - Получите сертификат от вашего IT отдела
   - Поместите файлы в `infra/certs/`

3. **Обновите пути в nginx конфигурации**:
   ```nginx
   ssl_certificate /etc/nginx/certs/your-cert.crt;
   ssl_certificate_key /etc/nginx/certs/your-key.key;
   ```

## Production Deployment

### Рекомендации

1. **Используйте .env файл для секретов**:
   - Не коммитьте `.env` в git
   - Используйте Docker secrets или Kubernetes secrets

2. **Настройте reverse proxy (Nginx)**:
   - Включен в `docker-compose.yml` с профилем `nginx`
   - Конфигурация в `infra/nginx/`
   - SSL/TLS опционален (см. раздел SSL/TLS Configuration)

3. **Мониторинг и логирование**:
   - Health checks настроены для всех сервисов
   - Интегрируйте с системой мониторинга (Prometheus, Grafana)
   - Логи nginx доступны в `infra/nginx/logs/`

4. **Backup и восстановление**:
   - Регулярный backup БД (если используется)
   - Backup конфигурационных файлов
   - Backup SSL сертификатов

5. **Масштабирование**:
   ```bash
   # Запуск нескольких экземпляров agent
   docker compose --profile full up --scale agent=3
   ```

6. **Обновления**:
   ```bash
   # Blue-green deployment
   docker compose --profile full up -d --no-deps --build agent
   ```

7. **Безопасность**:
   - Используйте HTTPS в production (см. раздел SSL/TLS)
   - Настройте firewall правила
   - Регулярно обновляйте образы и зависимости
   - Включите rate limiting в nginx

## Troubleshooting

### Проблема: Контейнер не запускается

```bash
# Проверьте логи
docker-compose logs mcp-server

# Проверьте health check
docker inspect mcp-repairs-server | grep Health -A 10
```

### Проблема: Нет соединения между сервисами

```bash
# Проверьте сеть
docker network inspect mcp-network

# Проверьте DNS resolution
docker-compose exec agent ping mcp-server
```

### Проблема: Ошибки импорта модулей

```bash
# Пересоберите образ
docker-compose build --no-cache agent

# Проверьте структуру файлов в контейнере
docker-compose run --rm agent ls -la /app/
```

### Проблема: Health check fails

```bash
# Проверьте endpoint вручную
docker-compose exec mcp-server curl http://localhost:8004/health

# Увеличьте start_period если сервис долго запускается
```

## Дополнительная информация

### Размеры образов

После оптимизации multi-stage сборки:
- `mcp-server`: ~200-300 MB
- `agent`: ~400-500 MB (из-за ML библиотек)
- `frontend`: ~300-400 MB

### Performance

- Health checks не влияют на производительность
- Изолированные сети обеспечивают безопасность
- Restart policy `unless-stopped` для автоматического восстановления

## Следующие шаги

1. Настройте CI/CD pipeline для автоматической сборки
2. Интегрируйте с Kubernetes для orchestration
3. Добавьте автоматическое тестирование в pipeline
4. Настройте мониторинг и алертинг
5. Реализуйте rate limiting и caching
