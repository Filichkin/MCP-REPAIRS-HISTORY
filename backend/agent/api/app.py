'''
FastAPI application for the warranty agent system.

This module provides REST API endpoints
for interacting with the multi-agent system.
'''

from datetime import datetime
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend.config import settings
from backend.agent.api.schemas import (
    QueryRequest,
    QueryResponse,
    AgentResultResponse,
    HealthCheckResponse,
    ErrorResponse,
)
from backend.agent.graph import execute_query
from backend.agent.tools.mcp_client import get_mcp_client, close_mcp_client
from backend.agent.utils.vin_validator import validate_vin


@asynccontextmanager
async def lifespan(app: FastAPI):
    '''Менеджер жизненного цикла приложения.'''
    # Startup
    logger.info('Запуск API гарантийного агента')
    logger.info(f'Среда: {settings.app_name} v{settings.app_version}')

    # Initialize MCP client
    try:
        await get_mcp_client()
        logger.info('MCP клиент инициализирован')
    except Exception as e:
        logger.error(f'Не удалось инициализировать MCP клиент: {e}')

    yield

    # Shutdown
    logger.info('Завершение работы API гарантийного агента')
    await close_mcp_client()
    logger.info('MCP клиент закрыт')


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description='Многоагентный системный анализ гарантийных обращений',
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get(
    '/health',
    response_model=HealthCheckResponse,
    tags=['System'],
    summary='Проверка здоровья',
)
async def health_check() -> HealthCheckResponse:
    '''
    Проверить статус компонентов.

    Возвращает статус здоровья:
    - API сервис
    - Подключение MCP сервера
    - Доступность LLM
    '''
    # Check MCP server
    mcp_status = 'unknown'
    try:
        client = await get_mcp_client()
        health = await client.health_check()
        mcp_status = health.get('status', 'unknown')
    except Exception as e:
        logger.warning(f'Проверка здоровья MCP сервера failed: {e}')
        mcp_status = 'error'

    # Check LLM (basic check)
    llm_status = 'ready'
    try:
        from backend.agent.llm.gigachat_setup import get_classifier_llm

        _ = get_classifier_llm()
    except Exception as e:
        logger.warning(f'LLM check failed: {e}')
        llm_status = 'error'

    return HealthCheckResponse(
        status='healthy',
        version=settings.app_version,
        timestamp=datetime.now(),
        mcp_server_status=mcp_status,
        llm_status=llm_status,
    )


@app.post(
    '/agent/query',
    response_model=QueryResponse,
    tags=['Agent'],
    summary='Выполнить запрос агента',
    status_code=status.HTTP_200_OK,
)
async def execute_agent_query(request: QueryRequest) -> QueryResponse:
    '''
    Выполнить запрос через многоагентную систему.

    Этот endpoint:
    1. Проверяет входные данные (запрос и опциональный VIN)
    2. Передает запрос через соответствующих агентов
    3. Возвращает комплексный анализ и ответ

    Args:
        request: Запрос с текстом запроса, опциональным VIN и контекстом

    Returns:
        Ответ с анализом от соответствующих агентов

    Raises:
        HTTPException: Для ошибок валидации или системных сбоев
    '''
    try:
        # Validate VIN if provided
        if request.vin:
            is_valid, error_msg = validate_vin(request.vin)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f'Некорректный VIN: {error_msg}',
                )

        logger.info(
            f'Обработка запроса: {request.query[:100]}... '
            f'VIN: {request.vin or "Не указан"}'
        )

        # Execute query through graph
        final_state = await execute_query(
            query=request.query,
            vin=request.vin,
            user_context=request.context,
        )

        # Convert agent results to response format
        agent_results = [
            AgentResultResponse(
                agent_name=result.agent_name,
                success=result.success,
                data=result.data,
                error=result.error,
                timestamp=result.timestamp,
            )
            for result in final_state.get_all_results()
        ]

        # Build response
        response = QueryResponse(
            success=not final_state.has_errors(),
            query=final_state.query,
            vin=final_state.vin,
            response=final_state.final_response or 'Ответ не сгенерирован',
            agents_used=final_state.metadata.get('agents_used', []),
            agent_results=agent_results,
            execution_time_seconds=final_state.get_execution_time(),
            steps_completed=final_state.steps_completed,
            errors=final_state.errors,
            start_time=final_state.start_time,
            end_time=final_state.end_time,
        )

        exec_time = response.execution_time_seconds
        logger.info(
            f'Запрос выполнен. Success: {response.success}, '
            f'Время: {exec_time:.2f}s' if exec_time else 'Время: N/A'
        )

        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f'Выполнение запроса failed: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Внутренняя ошибка сервера: {str(e)}',
        )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Any,
    exc: Exception
) -> JSONResponse:
    '''Глобальный обработчик ошибок.'''
    logger.error(f'Необработанная ошибка: {exc}', exc_info=True)

    error_response = ErrorResponse(
        error=type(exc).__name__,
        message=str(exc),
        detail='Непредвиденная ошибка',
        timestamp=datetime.now(),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


@app.get('/', tags=['System'])
async def root() -> dict[str, str]:
    '''Root endpoint с информацией о API.'''
    return {
        'service': settings.app_name,
        'version': settings.app_version,
        'status': 'running',
        'docs': '/docs',
    }


# For development
if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'backend.agent.api.app:app',
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
