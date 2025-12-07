"""MCP Server для истории ремонтов и обслуживания автомобилей."""

import asyncio
import time
import httpx
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from fastmcp.server.auth import StaticTokenVerifier
from mcp.types import TextContent
from loguru import logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server.models import (
    RepairYear,
    WarrantyDaysStructured,
    WarrantyRecord,
    WarrantyHistoryStructured,
    Dealer,
    ReplacedPart,
    Operation,
    FaultPart,
    MaintenanceRecord,
    MaintenanceHistoryStructured,
    VehicleRepairRecord,
    VehicleRepairsHistoryStructured,
    RAGDocument,
    ComplianceRAGStructured,
)
from mcp_server.formatters import (
    format_warranty_days_text,
    format_warranty_history_text,
    format_maintenance_history_text,
    format_vehicle_repairs_history_text,
    format_compliance_rag_text,
)

try:
    from config import settings
except ImportError:
    from backend.config import settings


# ============================================================================
# MCP Server Initialization
# ============================================================================

# Настройка аутентификации
auth_provider = None
if settings.mcp_auth_enabled:
    if not settings.mcp_auth_token:
        raise ValueError(
            'MCP_AUTH_TOKEN must be set when MCP_AUTH_ENABLED is True'
        )
    # Используем StaticTokenVerifier для простой проверки токена
    auth_provider = StaticTokenVerifier(
        tokens={
            settings.mcp_auth_token: {
                'client_id': 'mcp-client',
                'scopes': ['read', 'write'],
            }
        }
    )
    logger.info('✅ Bearer token authentication enabled')

mcp = FastMCP(
    'Vehicle Repairs History MCP Server',
    auth=auth_provider,
)


# ============================================================================
# Health Check Endpoint
# ============================================================================


@mcp.custom_route('/health', methods=['GET'])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint для Docker и мониторинга."""
    return JSONResponse({'status': 'ok'})


# Глобальные переменные для RAG
_access_token: str | None = None
_access_token_lock = asyncio.Lock()


# ============================================================================
# Вспомогательные функции для работы с API
# ============================================================================


async def get_warranty_days(vin: str) -> dict[str, Any]:
    """Получить статистику дней в ремонте по годам владения."""
    url = f'{settings.api_url}/api/warranty/{vin}'
    headers = {'Authorization': f'Bearer {settings.api_key}'}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f'HTTP error {e.response.status_code}: {e}')
            if e.response.status_code == 404:
                return {'error': f'VIN {vin} не найден'}
            elif e.response.status_code == 401:
                return {'error': 'Ошибка аутентификации'}
            else:
                return {'error': f'HTTP ошибка: {e.response.status_code}'}
        except httpx.TimeoutException:
            logger.error(f'Timeout при запросе к {url}')
            return {'error': 'Превышено время ожидания запроса'}
        except Exception as e:
            logger.error(f'Ошибка при запросе к {url}: {e}')
            return {'error': str(e)}


async def get_warranty_history(vin: str) -> dict[str, Any]:
    """Получить историю гарантийных обращений."""
    url = f'{settings.api_url}/api/warranty/records/{vin}'
    headers = {'Authorization': f'Bearer {settings.api_key}'}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f'HTTP error {e.response.status_code}: {e}')
            if e.response.status_code == 404:
                return {'error': f'VIN {vin} не найден'}
            elif e.response.status_code == 401:
                return {'error': 'Ошибка аутентификации'}
            else:
                return {'error': f'HTTP ошибка: {e.response.status_code}'}
        except httpx.TimeoutException:
            logger.error(f'Timeout при запросе к {url}')
            return {'error': 'Превышено время ожидания запроса'}
        except Exception as e:
            logger.error(f'Ошибка при запросе к {url}: {e}')
            return {'error': str(e)}


async def get_maintenance_history(vin: str) -> list[dict[str, Any]]:
    """Получить историю технического обслуживания."""
    url = f'{settings.api_url}/api/maintenance/{vin}'
    headers = {'Authorization': f'Bearer {settings.api_key}'}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f'HTTP error {e.response.status_code}: {e}')
            if e.response.status_code == 404:
                return [{'error': f'VIN {vin} не найден'}]
            elif e.response.status_code == 401:
                return [{'error': 'Ошибка аутентификации'}]
            else:
                return [{'error': f'HTTP ошибка: {e.response.status_code}'}]
        except httpx.TimeoutException:
            logger.error(f'Timeout при запросе к {url}')
            return [{'error': 'Превышено время ожидания запроса'}]
        except Exception as e:
            logger.error(f'Ошибка при запросе к {url}: {e}')
            return [{'error': str(e)}]


async def get_vehicle_repairs_history(vin: str) -> list[dict[str, Any]]:
    """Получить историю ремонтов из дилерской сети (DNM records)."""
    url = f'{settings.api_url}/api/dnm/{vin}'
    headers = {'Authorization': f'Bearer {settings.api_key}'}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f'VIN {vin} не найден в DNM records')
                return []
            elif e.response.status_code == 401:
                logger.error('Ошибка аутентификации API')
                return [{'error': 'Ошибка аутентификации'}]
            else:
                logger.error(f'HTTP error {e.response.status_code}: {e}')
                return [{'error': f'HTTP ошибка: {e.response.status_code}'}]
        except httpx.TimeoutException:
            logger.error(f'Timeout при запросе к {url}')
            return [{'error': 'Превышено время ожидания запроса'}]
        except Exception as e:
            logger.error(f'Ошибка при запросе к {url}: {e}')
            return [{'error': str(e)}]


def _parse_retrieve_limit(value: str | None, default: int = 6) -> int:
    """Парсинг значения retrieve_limit с обработкой ошибок."""
    if value is None:
        return default
    try:
        limit = int(value)
        if limit <= 0:
            return default
        return limit
    except (TypeError, ValueError):
        return default


async def get_access_token() -> str:
    """Получение access token для RAG API."""
    async with _access_token_lock:
        global _access_token
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                token_response = await client.post(
                    settings.auth_url,
                    data={
                        'grant_type': 'client_credentials',
                        'client_id': settings.key_id,
                        'client_secret': settings.key_secret,
                    },
                )
                token_response.raise_for_status()
                access_token = token_response.json().get('access_token')
                if not access_token:
                    raise ValueError(
                        'Ответ аутентификации не содержит access_token'
                    )
                _access_token = access_token
                return access_token
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f'Ошибка при получении access token. '
                f'Статус: {e.response.status_code}; '
                f'Сообщение: {e.response.text}'
            )
        except httpx.TimeoutException:
            raise RuntimeError('Таймаут при получении access token.')
        except httpx.RequestError as e:
            raise RuntimeError(f'Сетевая ошибка аутентификации: {e}')
        except Exception as e:
            raise RuntimeError(f'Неожиданная ошибка аутентификации: {e}')


# ============================================================================
# MCP Tools с ToolResult и output_schema
# ============================================================================


@mcp.tool(
    output_schema={
        'type': 'object',
        'properties': {
            'vin': {'type': 'string', 'description': 'VIN номер автомобиля'},
            'total_years': {
                'type': 'integer',
                'description': 'Общее количество лет владения'
            },
            'repair_years': {
                'type': 'array',
                'description': 'Список годов владения с днями в ремонте',
                'items': {
                    'type': 'object',
                    'properties': {
                        'year_number': {
                            'type': 'integer',
                            'description': 'Номер года владения'
                        },
                        'is_current_year': {
                            'type': 'boolean',
                            'description': 'Является ли год текущим'
                        },
                        'days_in_repair': {
                            'type': 'integer',
                            'description': 'Количество дней в ремонте'
                        }
                    },
                    'required': [
                        'year_number',
                        'is_current_year',
                        'days_in_repair'
                    ]
                }
            },
            'current_year_days': {
                'type': ['integer', 'null'],
                'description': 'Дней в ремонте в текущем году'
            },
            'total_days_in_repair': {
                'type': 'integer',
                'description': 'Общее количество дней в ремонте'
            }
        },
        'required': [
            'vin',
            'total_years',
            'repair_years',
            'total_days_in_repair'
        ]
    }
)
async def warranty_days(vin: str) -> ToolResult:
    """
    Получить статистику дней в ремонте по годам владения автомобиля.

    Args:
        vin: VIN номер автомобиля

    Returns:
        ToolResult с текстовым описанием, структурированными данными
        и метаданными выполнения
    """
    start_time = time.time()
    logger.info(f'Tool warranty_days вызван с VIN: {vin}')
    data = await get_warranty_days(vin)

    # Обработка ошибок
    if 'error' in data:
        logger.error(f'warranty_days: ошибка для VIN {vin}: {data["error"]}')
        return ToolResult(
            content=[
                TextContent(type='text', text=f'Ошибка: {data["error"]}')
                ],
            is_error=True,
            meta={
                'vin': vin,
                'error_type': 'api_error',
                'execution_time_ms': int((time.time() - start_time) * 1000)
            }
        )

    # Нет данных
    if not data.get('repair_data'):
        logger.info(f'warranty_days: записи не найдены для VIN {vin}')
        structured = WarrantyDaysStructured(
            vin=vin,
            total_years=0,
            repair_years=[],
            current_year_days=None,
            total_days_in_repair=0
        )
        return ToolResult(
            content=[
                TextContent(
                    type='text',
                    text=f'Для VIN {vin}: записи не найдены'
                )
            ],
            structured_content=structured.model_dump(),
            meta={
                'vin': vin,
                'data_source': 'warranty_api',
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'record_count': 0,
                'timestamp': time.strftime(
                    '%Y-%m-%dT%H:%M:%SZ',
                    time.gmtime()
                )
            }
        )

    # Формируем структурированные данные
    repair_years = [
        RepairYear(
            year_number=record['year_number'],
            is_current_year=record['is_current_year'],
            days_in_repair=record['days_in_repair']
        )
        for record in data['repair_data']
    ]

    current_year_days = next(
        (r.days_in_repair for r in repair_years if r.is_current_year),
        None
    )

    total_days = sum(r.days_in_repair for r in repair_years)

    structured = WarrantyDaysStructured(
        vin=vin,
        total_years=len(repair_years),
        repair_years=repair_years,
        current_year_days=current_year_days,
        total_days_in_repair=total_days
    )

    # Текстовое описание
    text_summary = format_warranty_days_text(vin, repair_years, total_days)

    logger.info(
        f'warranty_days: найдено {len(repair_years)} записей для VIN {vin}'
    )

    return ToolResult(
        content=[TextContent(type='text', text=text_summary)],
        structured_content=structured.model_dump(),
        meta={
            'vin': vin,
            'data_source': 'warranty_api',
            'execution_time_ms': int((time.time() - start_time) * 1000),
            'record_count': len(repair_years),
            'api_endpoint': settings.api_url,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
    )


@mcp.tool(
    output_schema={
        'type': 'object',
        'properties': {
            'vin': {'type': 'string', 'description': 'VIN номер автомобиля'},
            'records': {
                'type': 'array',
                'description': 'Список гарантийных обращений',
                'items': {'type': 'object'}
            },
            'total_records': {
                'type': 'integer',
                'description': 'Общее количество гарантийных обращений'
            },
            'total_parts_replaced': {
                'type': 'integer',
                'description': 'Общее количество замененных деталей'
            },
            'total_operations': {
                'type': 'integer',
                'description': 'Общее количество выполненных работ'
            }
        },
        'required': [
            'vin',
            'records',
            'total_records',
            'total_parts_replaced',
            'total_operations'
        ]
    }
)
async def warranty_history(vin: str) -> ToolResult:
    """
    Получить историю гарантийных обращений автомобиля.

    Args:
        vin: VIN номер автомобиля

    Returns:
        ToolResult с текстовым описанием, структурированными данными
        и метаданными выполнения
    """
    start_time = time.time()
    logger.info(f'Tool warranty_history вызван с VIN: {vin}')
    data = await get_warranty_history(vin)

    # Обработка ошибок
    if 'error' in data:
        logger.error(
            f'warranty_history: ошибка для VIN {vin}: {data["error"]}'
        )
        return ToolResult(
            content=[
                TextContent(type='text', text=f'Ошибка: {data["error"]}')
                ],
            is_error=True,
            meta={
                'vin': vin,
                'error_type': 'api_error',
                'execution_time_ms': int((time.time() - start_time) * 1000)
            }
        )

    # Нет данных
    if not data.get('records'):
        logger.info(f'warranty_history: записи не найдены для VIN {vin}')
        structured = WarrantyHistoryStructured(
            vin=vin,
            records=[],
            total_records=0,
            total_parts_replaced=0,
            total_operations=0
        )
        return ToolResult(
            content=[
                TextContent(
                    type='text',
                    text=f'Для VIN {vin}: записи не найдены'
                )
            ],
            structured_content=structured.model_dump(),
            meta={
                'vin': vin,
                'data_source': 'warranty_api',
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'record_count': 0,
                'timestamp': time.strftime(
                    '%Y-%m-%dT%H:%M:%SZ',
                    time.gmtime()
                )
            }
        )

    # Обработка записей
    warranty_records = []
    total_parts = 0
    total_ops = 0

    for record in data['records']:
        replaced_parts = [
            ReplacedPart(
                part_number=part['replace_part'],
                description=part['replace_part_descr']
            )
            for part in record.get('replaced_parts', [])
        ]

        operations = [
            Operation(
                code=op['op_code'],
                description=op['op_code_descr']
            )
            for op in record.get('op_codes', [])
        ]

        warranty_record = WarrantyRecord(
            serial=record['serial'],
            date=record['ro_open_date'],
            odometer=record['odometr'],
            dealer=Dealer(
                name=record['dealer']['name'],
                code=record['dealer'].get('code'),
                city=record['dealer']['city']
            ),
            fault_part=FaultPart(
                part_number=record['casual_part'],
                description=record['casual_part_descr']
            ),
            replaced_parts=replaced_parts,
            operations=operations
        )

        warranty_records.append(warranty_record)
        total_parts += len(replaced_parts)
        total_ops += len(operations)

    structured = WarrantyHistoryStructured(
        vin=vin,
        records=warranty_records,
        total_records=len(warranty_records),
        total_parts_replaced=total_parts,
        total_operations=total_ops
    )

    # Текстовое описание
    text_summary = format_warranty_history_text(
        vin,
        warranty_records,
        total_parts,
        total_ops
    )

    logger.info(
        f'warranty_history: найдено {len(warranty_records)} '
        f'записей для VIN {vin}'
    )

    return ToolResult(
        content=[TextContent(type='text', text=text_summary)],
        structured_content=structured.model_dump(),
        meta={
            'vin': vin,
            'data_source': 'warranty_api',
            'execution_time_ms': int((time.time() - start_time) * 1000),
            'record_count': len(warranty_records),
            'api_endpoint': settings.api_url,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
    )


@mcp.tool(
    output_schema={
        'type': 'object',
        'properties': {
            'vin': {'type': 'string', 'description': 'VIN номер автомобиля'},
            'records': {
                'type': 'array',
                'description': 'Список записей о техническом обслуживании',
                'items': {'type': 'object'}
            },
            'total_records': {
                'type': 'integer',
                'description': 'Общее количество записей о ТО'
            },
            'maintenance_types': {
                'type': 'array',
                'description': 'Уникальные типы проведенного ТО',
                'items': {'type': 'string'}
            }
        },
        'required': ['vin', 'records', 'total_records', 'maintenance_types']
    }
)
async def maintenance_history(vin: str) -> ToolResult:
    """
    Получить историю технического обслуживания автомобиля.

    Args:
        vin: VIN номер автомобиля

    Returns:
        ToolResult с текстовым описанием, структурированными данными
        и метаданными выполнения
    """
    start_time = time.time()
    logger.info(f'Tool maintenance_history вызван с VIN: {vin}')
    data = await get_maintenance_history(vin)

    # Обработка ошибок
    if data and 'error' in data[0]:
        logger.error(
            f'maintenance_history: ошибка для VIN {vin}: {data[0]["error"]}'
        )
        return ToolResult(
            content=[
                TextContent(type='text', text=f'Ошибка: {data[0]["error"]}')
            ],
            is_error=True,
            meta={
                'vin': vin,
                'error_type': 'api_error',
                'execution_time_ms': int((time.time() - start_time) * 1000)
            }
        )

    # Нет данных
    if not data:
        logger.info(f'maintenance_history: записи не найдены для VIN {vin}')
        structured = MaintenanceHistoryStructured(
            vin=vin,
            records=[],
            total_records=0,
            maintenance_types=[]
        )
        return ToolResult(
            content=[
                TextContent(
                    type='text',
                    text=f'Для VIN {vin}: записи не найдены'
                )
            ],
            structured_content=structured.model_dump(),
            meta={
                'vin': vin,
                'data_source': 'maintenance_api',
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'record_count': 0,
                'timestamp': time.strftime(
                    '%Y-%m-%dT%H:%M:%SZ',
                    time.gmtime()
                )
            }
        )

    # Обработка записей
    maintenance_records = [
        MaintenanceRecord(
            vin=record['vin'],
            maintenance_type=record['maintenance_type'],
            date=record['ro_date'],
            odometer=record['odometer'],
            dealer=Dealer(
                name=record['dealer']['name'],
                code=record['dealer'].get('code'),
                city=record['dealer']['city']
            )
        )
        for record in data
    ]

    unique_types = list(
        set(record.maintenance_type for record in maintenance_records)
    )

    structured = MaintenanceHistoryStructured(
        vin=vin,
        records=maintenance_records,
        total_records=len(maintenance_records),
        maintenance_types=unique_types
    )

    # Текстовое описание
    text_summary = format_maintenance_history_text(vin, maintenance_records)

    logger.info(
        f'maintenance_history: найдено {len(maintenance_records)} '
        f'записей для VIN {vin}'
    )

    return ToolResult(
        content=[TextContent(type='text', text=text_summary)],
        structured_content=structured.model_dump(),
        meta={
            'vin': vin,
            'data_source': 'maintenance_api',
            'execution_time_ms': int((time.time() - start_time) * 1000),
            'record_count': len(maintenance_records),
            'api_endpoint': settings.api_url,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
    )


@mcp.tool(
    output_schema={
        'type': 'object',
        'properties': {
            'vin': {'type': 'string', 'description': 'VIN номер автомобиля'},
            'records': {
                'type': 'array',
                'description': 'Список записей о ремонтах DNM',
                'items': {'type': 'object'}
            },
            'total_records': {
                'type': 'integer',
                'description': 'Общее количество записей о ремонтах'
            },
            'repair_types': {
                'type': 'array',
                'description': 'Уникальные типы ремонтов',
                'items': {'type': 'string'}
            }
        },
        'required': ['vin', 'records', 'total_records', 'repair_types']
    }
)
async def vehicle_repairs_history(vin: str) -> ToolResult:
    """
    Получить историю ремонтов из дилерской сети (DNM records).

    Args:
        vin: VIN номер автомобиля

    Returns:
        ToolResult с текстовым описанием, структурированными данными
        и метаданными выполнения
    """
    start_time = time.time()
    logger.info(f'Tool vehicle_repairs_history вызван с VIN: {vin}')
    data = await get_vehicle_repairs_history(vin)

    # Обработка ошибок
    if data and 'error' in data[0]:
        logger.error(
            f'vehicle_repairs_history: ошибка для VIN {vin}: '
            f'{data[0]["error"]}'
        )
        return ToolResult(
            content=[
                TextContent(type='text', text=f'Ошибка: {data[0]["error"]}')
            ],
            is_error=True,
            meta={
                'vin': vin,
                'error_type': 'api_error',
                'execution_time_ms': int((time.time() - start_time) * 1000)
            }
        )

    # Нет данных
    if not data:
        logger.info(
            f'vehicle_repairs_history: записи не найдены для VIN {vin}'
        )
        structured = VehicleRepairsHistoryStructured(
            vin=vin,
            records=[],
            total_records=0,
            repair_types=[]
        )
        return ToolResult(
            content=[
                TextContent(
                    type='text',
                    text=f'Для VIN {vin}: записи не найдены'
                )
            ],
            structured_content=structured.model_dump(),
            meta={
                'vin': vin,
                'data_source': 'dnm_api',
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'record_count': 0,
                'timestamp': time.strftime(
                    '%Y-%m-%dT%H:%M:%SZ',
                    time.gmtime()
                )
            }
        )

    # Обработка записей
    repair_records = [
        VehicleRepairRecord(
            dealer_name=record['dealer_name'],
            date=record['ro_close_date'],
            odometer=record['odometer'],
            repair_type=record['repair_type'],
            visit_reason=record['visit_reason'],
            recommendations=record['recomendations']
        )
        for record in data
    ]

    unique_types = list(set(record.repair_type for record in repair_records))

    structured = VehicleRepairsHistoryStructured(
        vin=vin,
        records=repair_records,
        total_records=len(repair_records),
        repair_types=unique_types
    )

    # Текстовое описание
    text_summary = format_vehicle_repairs_history_text(vin, repair_records)

    logger.info(
        f'vehicle_repairs_history: найдено {len(repair_records)} '
        f'записей для VIN {vin}'
    )

    return ToolResult(
        content=[TextContent(type='text', text=text_summary)],
        structured_content=structured.model_dump(),
        meta={
            'vin': vin,
            'data_source': 'dnm_api',
            'execution_time_ms': int((time.time() - start_time) * 1000),
            'record_count': len(repair_records),
            'api_endpoint': settings.api_url,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
    )


@mcp.tool(
    output_schema={
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'Исходный запрос пользователя'
            },
            'documents': {
                'type': 'array',
                'description': 'Список релевантных документов',
                'items': {
                    'type': 'object',
                    'properties': {
                        'content': {
                            'type': 'string',
                            'description': 'Содержимое документа'
                        },
                        'metadata': {
                            'type': 'object',
                            'description': 'Метаданные документа'
                        },
                        'relevance_score': {
                            'type': ['number', 'null'],
                            'description': 'Оценка релевантности'
                        }
                    }
                }
            },
            'total_documents': {
                'type': 'integer',
                'description': 'Общее количество найденных документов'
            },
            'knowledge_base_version': {
                'type': 'string',
                'description': 'Версия базы знаний'
            }
        },
        'required': [
            'query',
            'documents',
            'total_documents',
            'knowledge_base_version'
        ]
    }
)
async def compliance_rag(query: str) -> ToolResult:
    """
    Инструмент обращается к API Базы Знаний и получает
    релевантные документы по запросу пользователя.

    Args:
        query: Запрос пользователя

    Returns:
        ToolResult с текстовым описанием, структурированными данными
        и метаданными выполнения. При ошибке возвращается ToolResult
        с is_error=True и описанием проблемы
    """
    start_time = time.time()
    logger.info(f'Tool compliance_rag вызван с запросом: {query}')

    retrieve_limit = _parse_retrieve_limit(
        str(settings.retrieve_limit) if settings.retrieve_limit else None,
        default=3
    )
    global _access_token

    async def do_rag_request(access_token: str):
        async with httpx.AsyncClient(timeout=20.0) as client:
            payload = {
                'query': query,
                'knowledge_base_version': settings.knowledge_base_version_id,
                'retrieval_configuration': {
                    'number_of_results': retrieve_limit,
                    'retrieval_type': 'SEMANTIC'
                }
            }
            return await client.post(
                settings.retrieve_url_template,
                json=payload,
                headers={'Authorization': f'Bearer {access_token}'},
            )

    # Попытка получить access token
    try:
        if _access_token is None:
            await get_access_token()
    except Exception as e:
        error_msg = f'Ошибка аутентификации: {str(e)}'
        logger.error(f'compliance_rag: {error_msg}')
        return ToolResult(
            content=[TextContent(type='text', text=error_msg)],
            is_error=True,
            meta={
                'query': query,
                'error_type': 'authentication_error',
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
        )

    try:
        response = await do_rag_request(_access_token)
        if response.status_code == 401:
            await get_access_token()
            response = await do_rag_request(_access_token)
            if response.status_code == 401:
                error_msg = (
                    'Аутентификация не удалась: '
                    'повторный 401 при запросе к базе знаний. '
                    'Проверьте настройки доступа к RAG API.'
                )
                logger.error(f'compliance_rag: {error_msg}')
                return ToolResult(
                    content=[TextContent(type='text', text=error_msg)],
                    is_error=True,
                    meta={
                        'query': query,
                        'error_type': 'authentication_failed',
                        'execution_time_ms': int(
                            (time.time() - start_time) * 1000
                        ),
                        'timestamp': time.strftime(
                            '%Y-%m-%dT%H:%M:%SZ',
                            time.gmtime()
                        )
                    }
                )
        response.raise_for_status()
        retrieve_result = response.json()
        logger.info(
            f'compliance_rag: успешно получен ответ от RAG API, '
            f'результатов: {len(retrieve_result.get("results", []))}'
        )
    except httpx.HTTPStatusError as e:
        status = (
            e.response.status_code if e.response is not None else 'unknown'
        )
        message = (
            e.response.text if e.response is not None else 'no message'
        )
        error_msg = (
            f'Не удалось получить релевантные документы. '
            f'HTTP ошибка {status}: {message}'
        )
        logger.error(f'compliance_rag: {error_msg}')
        return ToolResult(
            content=[TextContent(type='text', text=error_msg)],
            is_error=True,
            meta={
                'query': query,
                'error_type': 'http_error',
                'http_status': status,
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
        )
    except httpx.TimeoutException:
        error_msg = (
            'База знаний временно недоступна (таймаут запроса). '
            'Пожалуйста, попробуйте позже или обратитесь к администратору.'
        )
        logger.error(f'compliance_rag: {error_msg}')
        return ToolResult(
            content=[TextContent(type='text', text=error_msg)],
            is_error=True,
            meta={
                'query': query,
                'error_type': 'timeout',
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
        )
    except httpx.RequestError as e:
        error_msg = (
            f'Сетевая ошибка при обращении к базе знаний: {str(e)}. '
            f'Проверьте подключение к сети или настройки API.'
        )
        logger.error(f'compliance_rag: {error_msg}')
        return ToolResult(
            content=[TextContent(type='text', text=error_msg)],
            is_error=True,
            meta={
                'query': query,
                'error_type': 'network_error',
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
        )
    except Exception as e:
        error_msg = (
            f'Неожиданная ошибка при запросе к базе знаний: {str(e)}. '
            f'Обратитесь к администратору.'
        )
        logger.error(f'compliance_rag: {error_msg}')
        return ToolResult(
            content=[TextContent(type='text', text=error_msg)],
            is_error=True,
            meta={
                'query': query,
                'error_type': 'unexpected_error',
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
        )

    # Обработка результатов
    results = retrieve_result.get('results', [])
    documents = [
        RAGDocument(
            content=el.get('content', ''),
            metadata=el.get('metadata', {}),
            relevance_score=el.get('score')
        )
        for el in results
    ]

    structured = ComplianceRAGStructured(
        query=query,
        documents=documents,
        total_documents=len(documents),
        knowledge_base_version=settings.knowledge_base_version_id
    )

    # Текстовое описание
    text_summary = format_compliance_rag_text(query, documents)

    logger.info(
        f'compliance_rag: успешно обработан результат для запроса: {query}'
    )

    return ToolResult(
        content=[TextContent(type='text', text=text_summary)],
        structured_content=structured.model_dump(),
        meta={
            'query': query,
            'knowledge_base_version': settings.knowledge_base_version_id,
            'retrieval_limit': retrieve_limit,
            'execution_time_ms': int((time.time() - start_time) * 1000),
            'api_endpoint': settings.retrieve_url_template,
            'document_count': len(documents),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
    )


# ============================================================================
# Запуск сервера
# ============================================================================


if __name__ == '__main__':
    import signal
    import sys

    def signal_handler(sig, frame):
        """Обработчик сигналов для graceful shutdown."""
        print('\n🛑 Получен сигнал завершения, останавливаем сервер...')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Определяем URL сервера
    server_url = (
        f'http://{settings.mcp_server_host}:{settings.mcp_server_port}'
    )

    print('🚗 Запуск MCP сервера истории ремонтов и обслуживания...')
    print(f'📡 Транспорт: {settings.mcp_transport.upper()} (Streamable HTTP)')
    print(f'🌐 Сервер: {server_url}')
    print(f'🔗 Endpoint: {server_url}/mcp/v1/')
    print(f'🏠 Host: {settings.mcp_server_host}')
    print(f'🔌 Port: {settings.mcp_server_port}')
    print()
    print('🛠️  Доступные инструменты:')
    print('   - warranty_days(vin) - статистика дней в ремонте по годам')
    print('   - warranty_history(vin) - история гарантийных обращений')
    print('   - maintenance_history(vin) - история техобслуживания')
    print('   - vehicle_repairs_history(vin) - история ремонтов DNM')
    print('   - compliance_rag(query) - поиск в базе знаний')
    print()
    print(f'🔑 Backend API: {settings.api_url}')
    print()

    # Информация о безопасности
    print('🔐 Безопасность:')
    if settings.mcp_auth_enabled:
        print('   ✅ Bearer token аутентификация: ВКЛЮЧЕНА')
        print('   ⚠️  Требуется заголовок: Authorization: Bearer <token>')
    else:
        print(
            '   ⚠️ Bearer token аутентификация: ОТКЛЮЧЕНА (не для production!)'
        )

    print(
        '   💡 Для HTTPS используйте nginx reverse proxy '
        '(см. docker-compose.yml)'
    )

    print()
    print('✨ Все tools возвращают структурированные JSON-ответы')
    print('📚 Документация: backend/mcp_server/README.md')
    print()

    try:
        # Запуск сервера
        mcp.run(
            transport=settings.mcp_transport,
            host=settings.mcp_server_host,
            port=settings.mcp_server_port
        )
    except KeyboardInterrupt:
        print('\n🛑 Сервер остановлен')
    except Exception as e:
        logger.error(f'❌ Ошибка запуска сервера: {e}')
        sys.exit(1)
