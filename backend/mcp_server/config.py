'''
Модуль конфигурации для MCP сервера.

Этот модуль обрабатывает специфические настройки MCP сервера,
включая интеграцию с Cloud-RAG.
'''

import os
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPConfig(BaseSettings):
    '''Настройки MCP сервера загружены из переменных окружения.'''

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../../infra/.env'
        ),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # MCP Server Configuration
    mcp_server_url: str = 'http://localhost:8004'
    mcp_transport: str = 'http'
    mcp_server_port: int = 8004
    mcp_server_host: str = '0.0.0.0'
    mcp_timeout: int = Field(
        default=30,
        ge=1,
        description='MCP API timeout в секундах'
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

    # Application Configuration
    app_name: str = Field(
        default='MCP Server',
        description='Application name'
    )
    app_version: str = Field(
        default='0.1.0',
        description='Версия приложения'
    )
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = (
        Field(
            default='INFO',
            description='Logging level'
        )
    )

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
settings = MCPConfig()


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
