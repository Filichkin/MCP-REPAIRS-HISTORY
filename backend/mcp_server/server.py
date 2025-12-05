import asyncio
import httpx
from typing import Any, Dict

from fastmcp import FastMCP
from loguru import logger

try:
    from config import settings
except ImportError:
    from backend.config import settings


mcp = FastMCP('Vehicle Repairs History MCP Server')

# Глобальные переменные для RAG
_access_token: str | None = None
_access_token_lock = asyncio.Lock()


async def get_warranty_days(vin: str) -> dict[str, Any]:
    '''Получить статистику дней в ремонте по годам владения.'''
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
    '''Получить историю гарантийных обращений.'''
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
    '''Получить историю технического обслуживания.'''
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
    '''Получить историю ремонтов из дилерской сети (DNM records).'''
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
    '''Парсинг значения retrieve_limit с обработкой ошибок.'''
    if value is None:
        return default
    try:
        limit = int(value)
        if limit <= 0:
            return default
        return limit
    except (TypeError, ValueError):
        return default


async def postprocess_retrieve_result(
    retrieve_result: Dict[str, Any]
) -> str:
    '''Форматирование результатов из базы знаний.'''
    result_str = 'Context:\n\n'
    results = retrieve_result.get('results', [])
    for idx, el in enumerate(results, start=1):
        content = el.get('content', '')
        metadata = el.get('metadata', {})
        result_str += (
            f'Document {idx}:\n'
            f'Content: {content}\n'
            f'Metadata: {metadata}\n\n'
        )
    return result_str


async def get_access_token() -> str:
    '''Получение access token для RAG API.'''
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


@mcp.tool()
async def warranty_days(vin: str) -> str:
    '''
    Получить статистику дней в ремонте по годам владения автомобиля.

    Args:
        vin: VIN номер автомобиля

    Returns:
        Описание статистики ремонтов по годам владения на русском языке
    '''
    logger.info(f'Tool warranty_days вызван с VIN: {vin}')
    data = await get_warranty_days(vin)

    if 'error' in data:
        logger.error(f'warranty_days: ошибка для VIN {vin}: {data["error"]}')
        return f'Ошибка: {data["error"]}'

    if not data.get('repair_data'):
        logger.info(f'warranty_days: записи не найдены для VIN {vin}')
        return f'Для VIN {vin}: записи не найдены'

    descriptions = []
    for record in data['repair_data']:
        year_num = record['year_number']
        is_current = record['is_current_year']
        days = record['days_in_repair']

        current_marker = ' (текущий)' if is_current else ''
        desc = (
            f'Для VIN {vin}: год владения {year_num}{current_marker} - '
            f'{days} дней в ремонте'
        )
        descriptions.append(desc)

    logger.info(
        f'warranty_days: найдено {len(descriptions)} записей для VIN {vin}'
    )
    return '\n'.join(descriptions)


@mcp.tool()
async def warranty_history(vin: str) -> str:
    '''
    Получить историю гарантийных обращений автомобиля.

    Args:
        vin: VIN номер автомобиля

    Returns:
        Описание гарантийных обращений на русском языке
    '''
    logger.info(f'Tool warranty_history вызван с VIN: {vin}')
    data = await get_warranty_history(vin)

    if 'error' in data:
        logger.error(
            f'warranty_history: ошибка для VIN {vin}: {data["error"]}'
        )
        return f'Ошибка: {data["error"]}'

    if not data.get('records'):
        logger.info(f'warranty_history: записи не найдены для VIN {vin}')
        return f'Для VIN {vin}: записи не найдены'

    descriptions = []
    for record in data['records']:
        serial = record['serial']
        ro_open_date = record['ro_open_date']
        odometr = record['odometr']
        dealer_name = record['dealer']['name']
        dealer_city = record['dealer']['city']
        casual_part = record['casual_part']
        casual_part_descr = record['casual_part_descr']

        replaced_parts_descriptions = [
            f'Каталожный номер: {part["replace_part"]}, '
            f'Название: {part["replace_part_descr"]}\n'
            for part in record.get('replaced_parts', [])
        ]
        replaced_parts_str = (
            '; '.join(replaced_parts_descriptions)
            if replaced_parts_descriptions else 'нет'
        )

        op_codes_descriptions = [
            f'Код операции: {op["op_code"]}, '
            f'Описание работы: {op["op_code_descr"]}\n'
            for op in record.get('op_codes', [])
        ]
        op_codes_str = (
            '; '.join(op_codes_descriptions)
            if op_codes_descriptions else 'нет'
        )

        desc = (
            f'Гарантийное требование {serial} от {ro_open_date} '
            f'(пробег {odometr} км) у дилера {dealer_name} '
            f'({dealer_city}).\n\n'
            f'Деталь-виновник: {casual_part}. \n'
            f'Описание детали-виновника: {casual_part_descr}. \n\n'
            f'Заменённые детали: \n'
            f'{replaced_parts_str}. \n\n'
            f'Выполненные работы: \n'
            f'{op_codes_str}'
        )
        descriptions.append(desc)

    logger.info(
        f'warranty_history: найдено {len(descriptions)} записей для VIN {vin}'
    )
    return '\n\n'.join(descriptions)


@mcp.tool()
async def maintenance_history(vin: str) -> str:
    '''
    Получить историю технического обслуживания автомобиля.

    Args:
        vin: VIN номер автомобиля

    Returns:
        Описание истории техобслуживания на русском языке
    '''
    logger.info(f'Tool maintenance_history вызван с VIN: {vin}')
    data = await get_maintenance_history(vin)

    if data and 'error' in data[0]:
        logger.error(
            f'maintenance_history: ошибка для VIN {vin}: {data[0]["error"]}'
        )
        return f'Ошибка: {data[0]["error"]}'

    if not data:
        logger.info(f'maintenance_history: записи не найдены для VIN {vin}')
        return f'Для VIN {vin}: записи не найдены'

    descriptions = []
    for record in data:
        vehicle_vin = record['vin']
        maintenance_type = record['maintenance_type']
        dealer_name = record['dealer']['name']
        dealer_code = record['dealer']['code']
        dealer_city = record['dealer']['city']
        ro_date = record['ro_date']
        odometer = record['odometer']

        desc = (
            f'Для VIN {vehicle_vin} проводилось {maintenance_type} '
            f'{ro_date} при пробеге {odometer} км у дилера '
            f'{dealer_name}, код {dealer_code} в городе {dealer_city}'
        )
        descriptions.append(desc)

    logger.info(
        f'maintenance_history: найдено {len(descriptions)} записей '
        f'для VIN {vin}'
    )
    return '\n\n'.join(descriptions)


@mcp.tool()
async def vehicle_repairs_history(vin: str) -> str:
    '''
    Получить историю ремонтов из дилерской сети (DNM records).

    Args:
        vin: VIN номер автомобиля

    Returns:
        Описание истории ремонтов на русском языке
    '''
    logger.info(f'Tool vehicle_repairs_history вызван с VIN: {vin}')
    data = await get_vehicle_repairs_history(vin)

    if data and 'error' in data[0]:
        logger.error(
            f'vehicle_repairs_history: ошибка для VIN {vin}: '
            f'{data[0]["error"]}'
        )
        return f'Ошибка: {data[0]["error"]}'

    if not data:
        logger.info(
            f'vehicle_repairs_history: записи не найдены для VIN {vin}'
        )
        return f'Для VIN {vin}: записи не найдены'

    descriptions = []
    for record in data:
        dealer_name = record['dealer_name']
        ro_close_date = record['ro_close_date']
        odometer = record['odometer']
        repair_type = record['repair_type']
        visit_reason = record['visit_reason']
        recomendations = record['recomendations']

        desc = (
            f'Посещение {dealer_name} {ro_close_date} '
            f'(пробег {odometer} км).\n\n'
            f'Тип ремонта: {repair_type}.\n\n'
            f'Причина визита: {visit_reason}.\n\n'
            f'Рекомендации: {recomendations}.\n\n'
            f'Рекомендации: {recomendations}'
        )
        descriptions.append(desc)

    logger.info(
        f'vehicle_repairs_history: найдено {len(descriptions)} записей '
        f'для VIN {vin}'
    )
    return '\n\n'.join(descriptions)


@mcp.tool()
async def compliance_rag(query: str) -> str:
    '''
    Инструмент обращается к API Базы Знаний и получает
    релевантные документы по запросу пользователя.
    На выходе выдает релевантные документы, которые нужно использовать
    для ответа на вопрос пользователя.

    Args:
        query: Запрос пользователя.

    Returns:
        Отформатированная строка с релевантными документами из базы
        знаний.

    Raises:
        ValueError: Ошибки связанные с некорректными параметрами.
        RuntimeError: Серверная ошибка.
    '''
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

    if _access_token is None:
        await get_access_token()

    try:
        response = await do_rag_request(_access_token)
        if response.status_code == 401:
            # Токен истёк или неверен,
            # пробуем обновить токен и повторить попытку
            await get_access_token()  # обновит _access_token
            response = await do_rag_request(_access_token)
            if response.status_code == 401:
                # Второй 401 подряд = реальные проблемы.
                raise RuntimeError(
                    'Аутентификация не удалась: '
                    'повторный 401 при запросе к базе знаний.'
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
        logger.error(
            f'compliance_rag: HTTP ошибка {status} при запросе к RAG API: '
            f'{message}'
        )
        raise RuntimeError(
            f'Не удалось получить релевантные документы. '
            f'Статус: {status}; Сообщение: {message}'
        )
    except httpx.TimeoutException:
        logger.error('compliance_rag: таймаут при запросе к RAG API')
        raise RuntimeError(
            'Не удалось получить релевантные документы. '
            'Таймаут запроса к Managed RAG'
        )
    except httpx.RequestError as e:
        logger.error(f'compliance_rag: сетевая ошибка при запросе: {e}')
        raise RuntimeError(
            f'Не удалось получить релевантные документы. '
            f'Сетевая ошибка при запросе к Managed RAG: {e}'
        )
    except Exception as e:
        # Непредвиденная ошибка
        logger.error(f'compliance_rag: неожиданная ошибка: {e}')
        raise RuntimeError(
            f'Не удалось получить релевантные документы. '
            f'Неожиданная ошибка при запросе к Managed RAG: {e}'
        )

    postprocessed_retrieve_result = (
        await postprocess_retrieve_result(retrieve_result)
    )
    logger.info(
        f'compliance_rag: успешно обработан результат для запроса: {query}'
    )
    return postprocessed_retrieve_result


if __name__ == '__main__':
    import signal
    import sys

    def signal_handler(sig, frame):
        '''Обработчик сигналов для graceful shutdown.'''
        print('\n🛑 Получен сигнал завершения, останавливаем сервер...')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print('🚗 Запуск MCP сервера истории ремонтов и обслуживания...')
    print(f'📡 Сервер: {settings.mcp_server_url}')
    print(f'🔗 SSE endpoint: {settings.mcp_server_url}/sse')
    print(f'📧 Messages: {settings.mcp_server_url}/messages/')
    print('🛠️  Доступные инструменты:')
    print('   - warranty_days(vin) - статистика дней в ремонте по годам')
    print('   - warranty_history(vin) - история гарантийных обращений')
    print('   - maintenance_history(vin) - история техобслуживания')
    print('   - vehicle_repairs_history(vin) - история ремонтов DNM')
    print('   - compliance_rag(query) - поиск в базе знаний')
    print(f'🔑 API: {settings.api_url}')
    print('🔐 Используется Bearer token аутентификация')
    print()

    try:
        mcp.run(
            transport=settings.mcp_transport,
            host=settings.mcp_server_host,
            port=settings.mcp_server_port
        )
    except KeyboardInterrupt:
        print('\n🛑 Сервер остановлен')
