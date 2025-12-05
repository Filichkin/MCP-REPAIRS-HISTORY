import httpx
from typing import Any

from fastmcp import FastMCP
from loguru import logger

try:
    from config import settings
except ImportError:
    from backend.config import settings


mcp = FastMCP('Vehicle Repairs History MCP Server')


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


@mcp.tool()
async def warranty_days(vin: str) -> str:
    '''
    Получить статистику дней в ремонте по годам владения автомобиля.

    Args:
        vin: VIN номер автомобиля

    Returns:
        Описание статистики ремонтов по годам владения на русском языке
    '''
    data = await get_warranty_days(vin)

    if 'error' in data:
        return f'Ошибка: {data["error"]}'

    if not data.get('repair_data'):
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
    data = await get_warranty_history(vin)

    if 'error' in data:
        return f'Ошибка: {data["error"]}'

    if not data.get('records'):
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
    data = await get_maintenance_history(vin)

    if data and 'error' in data[0]:
        return f'Ошибка: {data[0]["error"]}'

    if not data:
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
    data = await get_vehicle_repairs_history(vin)

    if data and 'error' in data[0]:
        return f'Ошибка: {data[0]["error"]}'

    if not data:
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

    return '\n\n'.join(descriptions)


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
