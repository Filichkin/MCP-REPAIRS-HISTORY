'''
Configuration module for the MCP server and warranty agent system.

This module handles all configuration settings including MCP server,
Cloud-RAG integration, GigaChat LLM, and agent system settings.
'''

import os
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    '''Application settings loaded from environment variables.'''

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../infra/.env'
        ),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # MCP Server Configuration
    mcp_server_url: str = 'http://localhost:8004'
    mcp_transport: str = 'sse'
    mcp_server_port: int = 8004
    mcp_server_host: str = '127.0.0.1'
    mcp_timeout: int = Field(
        default=30,
        ge=1,
        description='MCP API timeout in seconds'
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

    # Cloud-RAG Configuration
    key_id: str
    key_secret: str
    auth_url: str
    retrieve_url_template: str
    knowledge_base_id: str
    knowledge_base_version_id: str = 'latest'
    retrieve_limit: int = 10
    evolution_project_id: str

    # External API Configuration
    api_key: str = 'your-api-key'
    api_url: str = 'http://127.0.0.1:8000'

    # GigaChat Configuration
    gigachat_api_key: str = Field(
        default='',
        description='Ключ аутентификации GigaChat API'
    )
    gigachat_scope: Literal['GIGACHAT_API_PERS', 'GIGACHAT_API_CORP'] = Field(
        default='GIGACHAT_API_PERS',
        description='Область доступа GigaChat API'
    )
    gigachat_model: str = Field(
        default='GigaChat',
        description='Имя модели GigaChat'
    )
    gigachat_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description='Температура для ответов GigaChat',
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
        description='Включение потоковой передачи ответов'
    )

    # Application Configuration
    app_name: str = Field(
        default='Warranty Agent System',
        description='Имя приложения'
    )
    app_version: str = Field(default='0.1.0', description='Версия приложения')
    app_debug: bool = Field(default=False, description='Режим отладки')
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = (
        Field(
            default='INFO',
            description='Уровень логирования'
        )
    )

    # API Configuration
    api_host: str = Field(default='0.0.0.0', description='FastAPI host')
    api_port: int = Field(
        default=8005,
        ge=1024,
        le=65535,
        description='Порт FastAPI'
    )
    api_reload: bool = Field(
        default=False,
        description='Включение автоперезагрузки для разработки'
    )
    api_cors_origins: list[str] = Field(
        default=['*'],
        description='Разрешенные источники CORS'
    )

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
settings = Config()


# Agent role configurations
class AgentRoles:
    '''Определения ролей агентов и их целей.'''

    CLASSIFIER = {
        'name': 'Query Classifier',
        'description': 'Классифицирует запросы и определяет нужных агентов',
        'temperature': 0.3,
    }

    REPAIR_DAYS = {
        'name': 'Repair Days Tracker',
        'description': 'Анализирует дни простоя и прогнозирует риски',
        'temperature': 0.5,
    }

    COMPLIANCE = {
        'name': 'Warranty Compliance',
        'description': 'Интерпретирует гарантийную политику и права',
        'temperature': 0.4,
    }

    DEALER_INSIGHTS = {
        'name': 'Dealer Insights',
        'description': 'Анализирует историю ремонтов и выявляет паттерны',
        'temperature': 0.6,
    }

    REPORT_SUMMARY = {
        'name': 'Report & Summary',
        'description': 'Генерирует итоговые отчёты и справки',
        'temperature': 0.5,
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
        '''Return list of all available MCP tools.'''
        return [
            cls.WARRANTY_DAYS,
            cls.WARRANTY_HISTORY,
            cls.MAINTENANCE_HISTORY,
            cls.VEHICLE_REPAIRS_HISTORY,
            cls.COMPLIANCE_RAG,
        ]


# Graph node names
class GraphNodes:
    '''Идентификаторы узлов LangGraph.'''

    CLASSIFIER = 'classifier'
    REPAIR_DAYS = 'repair_days_tracker'
    COMPLIANCE = 'warranty_compliance'
    DEALER_INSIGHTS = 'dealer_insights'
    REPORT_SUMMARY = 'report_summary'
    AGGREGATOR = 'response_aggregator'
    END = 'END'
