'''
Pydantic schemas for FastAPI endpoints.

This module defines request and response models for the API.
'''

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    '''Схема запроса для endpoint агента запроса.'''

    query: str = Field(
        ...,
        description='Пользовательский запрос на русском языке',
        min_length=3,
        max_length=1000,
        examples=['Сколько дней автомобиль был в ремонте?'],
    )

    vin: Optional[str] = Field(
        default=None,
        description='Номер VIN автомобиля (опционально)',
        pattern=r'^[A-HJ-NPR-Z0-9]{17}$',
        examples=['Z94C251BBLR102931'],
    )

    context: dict[str, Any] = Field(
        default_factory=dict,
        description='Дополнительный контекст для запроса',
    )

    class Config:
        '''Конфигурация Pydantic.'''

        json_schema_extra = {
            'example': {
                'query': 'Сколько дней в 2023 году автомобиль был в ремонте?',
                'vin': 'Z94C251BBLR102931',
                'context': {},
            }
        }


class AgentResultResponse(BaseModel):
    '''Схема ответа для результата отдельного агента.'''

    agent_name: str = Field(description='Имя агента')
    success: bool = Field(description='Был ли выполнен успешно')
    data: dict[str, Any] = Field(
        default_factory=dict, description='Результат данных'
    )
    error: Optional[str] = Field(
        default=None,
        description='Сообщение об ошибке, если выполнение не удалось'
    )
    timestamp: datetime = Field(description='Execution timestamp')


class QueryResponse(BaseModel):
    '''Схема ответа для endpoint агента запроса.'''

    success: bool = Field(description='Общая успешность статус')
    query: str = Field(description='Исходный запрос')
    vin: Optional[str] = Field(
        default=None,
        description='VIN использованный в анализе'
        )
    response: str = Field(description='Финальный отформатированный ответ')

    # Agent results
    agents_used: list[str] = Field(
        default_factory=list,
        description='Список агентов, которые были вызваны'
    )
    agent_results: list[AgentResultResponse] = Field(
        default_factory=list,
        description='Подробные результаты от каждого агента'
    )

    # Execution metadata
    execution_time_seconds: Optional[float] = Field(
        default=None, description='Общее время выполнения'
    )
    steps_completed: list[str] = Field(
        default_factory=list, description='Шаги графа, которые были выполнены'
    )

    # Errors
    errors: list[str] = Field(
        default_factory=list,
        description='Список ошибок, которые были встречены'
    )

    # Timestamps
    start_time: datetime = Field(description='Время начала запроса')
    end_time: Optional[datetime] = Field(
        default=None, description='Время окончания запроса'
    )

    class Config:
        '''Pydantic configuration.'''

        json_schema_extra = {
            'example': {
                'success': True,
                'query': 'Сколько дней в 2025 году автомобиль был в ремонте?',
                'vin': 'Z94C251BBLR102931',
                'response': 'Анализ показывает, что в 2025 году автомобиль...',
                'agents_used': ['Repair Days Tracker'],
                'execution_time_seconds': 3.45,
                'errors': [],
                'start_time': '2024-01-15T10:30:00',
                'end_time': '2024-01-15T10:30:03',
            }
        }


class HealthCheckResponse(BaseModel):
    '''Схема ответа для endpoint проверки здоровья.'''

    status: str = Field(description='Статус сервиса', examples=['healthy'])
    version: str = Field(description='Версия приложения')
    timestamp: datetime = Field(description='Текущее время сервера')
    mcp_server_status: str = Field(
        description='Статус подключения MCP сервера',
        examples=['connected', 'disconnected', 'error'],
    )
    llm_status: str = Field(
        description='Статус доступности LLM', examples=['ready', 'error']
    )


class ErrorResponse(BaseModel):
    '''Схема ответа для ошибок.'''

    error: str = Field(description='Тип ошибки')
    message: str = Field(description='Сообщение об ошибке')
    detail: Optional[str] = Field(
        default=None,
        description='Дополнительные детали ошибки',
    )
    timestamp: datetime = Field(description='Время ошибки')

    class Config:
        '''Pydantic configuration.'''

        json_schema_extra = {
            'example': {
                'error': 'ValidationError',
                'message': 'Некорректный формат VIN',
                'detail': 'VIN должен быть ровно 17 символов',
                'timestamp': '2024-01-15T10:30:00',
            }
        }
