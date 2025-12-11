'''
Главная точка входа для системы агента гарантийных претензий.

Этот модуль предоставляет CLI интерфейс и запускает FastAPI сервер.
'''

import sys
import asyncio
from typing import Optional
import uvicorn
from loguru import logger

from agent.config import settings
from agent.graph import execute_query
from agent.tools.mcp_client import close_mcp_client


def setup_logging() -> None:
    '''Настройка логирования с помощью loguru.'''
    # Удаление default handler
    logger.remove()

    # Добавление console handler с форматом
    logger.add(
        sys.stderr,
        format=(
            '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | '
            '<level>{level: <8}</level> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>-'
            '<level>{message}</level>'
        ),
        level=settings.log_level,
        colorize=True,
    )

    # Добавление file handler если не в режиме debug
    if not settings.app_debug:
        logger.add(
            'logs/agent_{time:YYYY-MM-DD}.log',
            rotation='1 day',
            retention='7 days',
            level='INFO',
            format=(
                '{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | '
                '{name}:{function}:{line} - {message}'
            ),
        )

    logger.info('Логирование настроено')


async def test_query(query: str, vin: Optional[str] = None) -> None:
    '''
    Тестирование выполнения запроса (для разработки/тестирования).

    Args:
        query: Текст запроса
        vin: Опциональный VIN
    '''
    logger.info(f'Testing query: {query}')

    try:
        # Execute query
        result = await execute_query(query=query, vin=vin)

        # Print results
        print('\n' + '=' * 80)
        print('QUERY RESULTS')
        print('=' * 80)
        print(f'\nQuery: {result.query}')
        print(f'VIN: {result.vin or "N/A"}')
        print('\nClassification:')
        if result.classification:
            print(
                f'  - Repair Days: {result.classification.needs_repair_days}'
                )
            print(f'  - Compliance: {result.classification.needs_compliance}')
            print(
                f'  - Dealer Insights: '
                f'{result.classification.needs_dealer_insights}'
            )
            print(f'  - Reasoning: {result.classification.reasoning}')

        print(f'\nSteps completed: {", ".join(result.steps_completed)}')
        print(f'Execution time: {result.get_execution_time():.2f}s')

        if result.errors:
            print(f'\nErrors: {len(result.errors)}')
            for error in result.errors:
                print(f'  - {error}')

        print('\n' + '-' * 80)
        print('FINAL RESPONSE:')
        print('-' * 80)
        print(result.final_response)
        print('=' * 80 + '\n')

    finally:
        await close_mcp_client()


def run_server() -> None:
    '''Запуск FastAPI сервера.'''
    logger.info(
        f'Запуск сервера на {settings.api_host}:{settings.api_port}'
    )

    uvicorn.run(
        'agent.api.app:app',
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )


def main() -> None:
    '''Главная точка входа.'''
    setup_logging()

    logger.info(f'{settings.app_name} v{settings.app_version}')

    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'server':
            # Start server
            run_server()

        elif command == 'test':
            # Test mode
            if len(sys.argv) < 3:
                print(
                    'Использование: python -m agent.main test '
                    '"<query>" [VIN]'
                    )
                sys.exit(1)

            query = sys.argv[2]
            vin = sys.argv[3] if len(sys.argv) > 3 else None

            asyncio.run(test_query(query, vin))

        else:
            print(f'Неизвестная команда: {command}')
            print('Доступные команды: server, test')
            sys.exit(1)

    else:
        # Default: start server
        print('Запуск сервера... (используйте команду "server" или "test")')
        run_server()


if __name__ == '__main__':
    main()
