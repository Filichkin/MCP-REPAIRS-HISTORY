'''
Модуль конфигурации для системы гарантийных агентов.

Этот модуль обрабатывает все настройки, связанные с агентами,
включая GigaChat LLM, поведение агентов и настройки API.
'''

import os
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    '''Настройки системы агентов загружены из переменных окружения.'''

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../../infra/.env'
        ),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # MCP Server Configuration (for client connection)
    mcp_server_url: str = 'http://localhost:8004'
    mcp_transport: str = 'http'
    mcp_timeout: int = Field(
        default=30,
        ge=1,
        description='Таймаут MCP API в секундах'
    )
    mcp_max_retries: int = Field(
        default=3,
        ge=1,
        description='Максимальное количество попыток для MCP API'
    )
    mcp_cache_ttl: int = Field(
        default=300,
        ge=0,
        description='TTL кэша MCP ответов в секундах'
    )

    # MCP Security Configuration
    mcp_auth_enabled: bool = Field(
        default=False,
        description='Включить аутентификацию Bearer токеном для MCP endpoints'
    )
    mcp_auth_token: str = Field(
        default='',
        description='Bearer токен для аутентификации MCP'
    )

    # GigaChat Configuration
    gigachat_api_key: str = Field(
        default='',
        description='GigaChat API key for langchain_gigachat'
    )
    gigachat_api_key_evolution: str = Field(
        default='',
        description='GigaChat API key for Evolution Platform (Api-Key)'
    )
    gigachat_scope: Literal['GIGACHAT_API_PERS', 'GIGACHAT_API_CORP'] = Field(
        default='GIGACHAT_API_PERS',
        description='GigaChat API scope'
    )
    gigachat_model: str = Field(
        default='GigaChat',
        description='GigaChat model name'
    )
    gigachat_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description='Temperature for GigaChat responses',
    )
    gigachat_timeout: int = Field(
        default=60,
        ge=1,
        description='Таймаут GigaChat API в секундах'
    )
    gigachat_max_retries: int = Field(
        default=3,
        ge=1,
        description='Максимальное количество попыток для GigaChat API'
    )

    # GigaChat API Method Selection
    gigachat_use_api: bool = Field(
        default=False,
        description=(
            'Использовать прямой API вместо langchain_gigachat. '
            'True - прямой API, False - langchain_gigachat'
        )
    )

    # GigaChat API Advanced Parameters (used only when use_api=True)
    gigachat_top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description='Параметр nucleus sampling для GigaChat API'
    )
    gigachat_max_tokens: int = Field(
        default=512,
        ge=1,
        description='Максимальное количество токенов в ответе'
    )
    gigachat_repetition_penalty: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description='Штраф за повторения в GigaChat API'
    )

    # Evolution Platform Configuration
    evolution_project_id: str

    # Agent Configuration
    agent_max_iterations: int = Field(
        default=10,
        ge=1,
        description='Максимальное количество итераций для выполнения агента'
    )
    agent_max_execution_time: int = Field(
        default=120,
        ge=1,
        description='Максимальное время выполнения в секундах'
    )
    agent_enable_streaming: bool = Field(
        default=True,
        description='Включить потоковую передачу ответов'
    )

    # Application Configuration
    app_name: str = Field(
        default='Warranty Agent System',
        description='Application name'
    )
    app_version: str = Field(
        default='0.1.0',
        description='Версия приложения'
    )
    app_debug: bool = Field(
        default=False,
        description='Режим отладки'
    )
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = (
        Field(
            default='INFO',
            description='Logging level'
        )
    )

    # API Configuration
    api_host: str = Field(default='0.0.0.0', description='FastAPI host')
    api_port: int = Field(
        default=8005,
        ge=1024,
        le=65535,
        description='FastAPI port'
    )
    api_reload: bool = Field(
        default=False,
        description='Включить автоперезагрузку для разработки'
    )
    api_cors_origins: list[str] = Field(
        default=['*'],
        description='Разрешенные источники CORS'
    )

    @field_validator('gigachat_top_p', mode='before')
    @classmethod
    def validate_top_p(cls, value: any) -> Optional[float]:
        '''
        Преобразовать пустые строки в None для gigachat_top_p.
        '''
        if value == '' or value is None:
            return None
        return float(value)

    @field_validator('gigachat_api_key')
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        '''
        Проверить, что API ключ не пустой (пропустить, если не установлен).
        '''
        if value and value == 'your-api-key-here':
            raise ValueError(
                'GIGACHAT_API_KEY должен быть установлен в .env файле'
            )
        return value

    @field_validator('mcp_server_url')
    @classmethod
    def validate_mcp_url(cls, value: str) -> str:
        '''Проверить, что URL MCP сервера начинается с http:// или https://.'''
        if not value.startswith(('http://', 'https://')):
            raise ValueError(
                'MCP_SERVER_URL должен начинаться с http:// или https://'
            )
        return value.rstrip('/')


# Global settings instance
settings = AgentConfig()


# Agent role configurations
class AgentRoles:
    '''Определения ролей агентов и их целей.'''

    CLASSIFIER = {
        'name': 'Query Classifier',
        'description': 'Классифицирует запросы и определяет нужных агентов',
        'temperature': 0.0,
    }

    REPAIR_DAYS = {
        'name': 'Repair Days Tracker',
        'description': 'Анализирует дни простоя и прогнозирует риски',
        'temperature': 0.0,
    }

    COMPLIANCE = {
        'name': 'Warran(ty Compliance',
        'description': (
            'Интерпретирует гарантийную политику и стандарты клиентской службы'
        ),
        'temperature': 0.0,
    }

    DEALER_INSIGHTS = {
        'name': 'Dealer Insights',
        'description': 'Анализирует историю ремонтов и выявляет паттерны',
        'temperature': 0.0,
    }

    REPORT_SUMMARY = {
        'name': 'Report & Summary',
        'description': 'Генерирует итоговые отчёты и справки',
        'temperature': 0.0,
    }


# MCP Tool names
class MCPTools:
    '''Идентификаторы MCP инструментов.'''

    WARRANTY_DAYS = 'warranty_days'
    WARRANTY_HISTORY = 'warranty_history'
    MAINTENANCE_HISTORY = 'maintenance_history'
    VEHICLE_REPAIRS_HISTORY = 'vehicle_repairs_history'
    COMPLIANCE_RAG = 'compliance_rag'

    @classmethod
    def all_tools(cls) -> list[str]:
        '''Возвращает список всех доступных MCP инструментов.'''
        return [
            cls.WARRANTY_DAYS,
            cls.WARRANTY_HISTORY,
            cls.MAINTENANCE_HISTORY,
            cls.VEHICLE_REPAIRS_HISTORY,
            cls.COMPLIANCE_RAG,
        ]


# Graph node names
class GraphNodes:
    '''LangGraph node identifiers.'''

    CLASSIFIER = 'classifier'
    REPAIR_DAYS = 'repair_days_tracker'
    COMPLIANCE = 'warranty_compliance'
    DEALER_INSIGHTS = 'dealer_insights'
    REPORT_SUMMARY = 'report_summary'
    AGGREGATOR = 'response_aggregator'
    END = 'END'
