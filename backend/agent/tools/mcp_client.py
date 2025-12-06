'''
MCP (Model Context Protocol) клиент для сервиса гарантийных инструментов.

Этот модуль предоставляет клиент для взаимодействия с MCP сервером,
который предоставляет инструменты и данные для работы с гарантийными вопросами.
'''

from typing import Any, Optional
from datetime import datetime, timedelta

import httpx
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from backend.config import settings, MCPTools


class MCPClientError(Exception):
    '''Базовое исключение для ошибок MCP клиента.'''

    pass


class MCPConnectionError(MCPClientError):
    '''Исключение при ошибке соединения с MCP сервером.'''

    pass


class MCPToolNotFoundError(MCPClientError):
    '''Исключение при ошибке не найденного инструмента.'''

    pass


class MCPValidationError(MCPClientError):
    '''Исключение при ошибке валидации входных данных инструмента.'''

    pass


class MCPClient:
    '''
    Клиент для взаимодействия с MCP сервером.

    Этот клиент обрабатывает:
    - Поиск и валидацию инструментов
    - Асинхронное выполнение инструментов
    - Логику повторных попыток и обработку ошибок
    - Опциональное кэширование ответов
    '''

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        enable_cache: bool = True,
    ) -> None:
        '''
        Инициализация MCP клиента.

        Args:
            base_url: Базовый URL MCP сервера (по умолчанию из settings)
            timeout: Таймаут запроса в секундах (по умолчанию из settings)
            max_retries: Максимальное количество повторных попыток
            (по умолчанию из settings)
            enable_cache: Включить кэширование ответов
        '''
        self.base_url = base_url or settings.mcp_server_url
        self.timeout = timeout or settings.mcp_timeout
        self.max_retries = max_retries or settings.mcp_max_retries
        self.enable_cache = enable_cache

        # Simple in-memory cache
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(seconds=settings.mcp_cache_ttl)

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

        logger.info(f'MCP клиент инициализирован с base_url={self.base_url}')

    async def __aenter__(self) -> 'MCPClient':
        '''Асинхронный контекстный менеджер входа.'''
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> None:
        '''Асинхронный контекстный менеджер выхода.'''
        await self.close()

    async def connect(self) -> None:
        '''Установление соединения с MCP сервером.'''
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True,
            )
            logger.debug('MCP HTTP клиент создан')

    async def close(self) -> None:
        '''Закрытие соединения с MCP сервером.'''
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug('MCP HTTP клиент закрыт')

    def _get_cache_key(self, tool_name: str, **kwargs: Any) -> str:
        '''Генерация ключа кэша из названия инструмента и аргументов.'''
        # Simple cache key: tool_name + sorted args
        args_str = '_'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))
        return f'{tool_name}:{args_str}'

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        '''Получение значения из кэша, если оно не истекло.'''
        if not self.enable_cache:
            return None

        if cache_key in self._cache:
            value, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.debug(f'Кэш hit для ключа: {cache_key}')
                return value
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
                logger.debug(f'Кэш истек для ключа: {cache_key}')

        return None

    def _put_to_cache(self, cache_key: str, value: Any) -> None:
        '''Добавление значения в кэш с текущей временной меткой.'''
        if self.enable_cache:
            self._cache[cache_key] = (value, datetime.now())
            logger.debug(f'Значение добавлено в кэш для ключа: {cache_key}')

    def clear_cache(self) -> None:
        '''Очистка всех кэшированных ответов.'''
        self._cache.clear()
        logger.info('Кэш очищен')

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.NetworkError)
            ),
        reraise=True,
    )
    async def _call_tool(
        self, tool_name: str, **kwargs: Any
    ) -> dict[str, Any]:
        '''
        Вызов MCP инструмента с логикой повторных попыток.

        Args:
            tool_name: Название инструмента для вызова
            **kwargs: Аргументы инструмента

        Returns:
            Данные ответа инструмента

        Raises:
            MCPConnectionError: Если соединение не установлено
            MCPToolNotFoundError: Если инструмент не найден
            MCPValidationError: Если валидация не прошла
        '''
        if self._client is None:
            await self.connect()

        assert self._client is not None

        try:
            # MCP server endpoint format: /tools/{tool_name}
            endpoint = f'/tools/{tool_name}'

            logger.debug(
                f'Вызов MCP инструмента: {tool_name} с аргументами: '
                f'{kwargs}'
            )

            response = await self._client.post(
                endpoint,
                json=kwargs,
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

            logger.debug(f'MCP инструмент {tool_name} ответил')
            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise MCPToolNotFoundError(
                    f'Инструмент не найден: {tool_name}'
                ) from e
            elif e.response.status_code == 422:
                raise MCPValidationError(
                    f'Ошибка валидации для инструмента {tool_name}: '
                    f'{e.response.text}'
                ) from e
            else:
                raise MCPConnectionError(
                    f'HTTP ошибка при вызове инструмента {tool_name}: {e}'
                ) from e

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise MCPConnectionError(
                f'Ошибка соединения при вызове инструмента {tool_name}: {e}'
            ) from e

        except Exception as e:
            raise MCPClientError(
                f'Неожиданная ошибка при вызове инструмента {tool_name}: {e}'
            ) from e

    async def warranty_days(self, vin: str) -> dict[str, Any]:
        '''
        Получить статистику дней в ремонте по годам владения автомобиля.

        Args:
            vin: VIN номер автомобиля

        Returns:
            Словарь с статистикой дней в ремонте по годам владения автомобиля
        '''
        cache_key = self._get_cache_key(MCPTools.WARRANTY_DAYS, vin=vin)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        result = await self._call_tool(MCPTools.WARRANTY_DAYS, vin=vin)
        self._put_to_cache(cache_key, result)
        return result

    async def warranty_history(self, vin: str) -> dict[str, Any]:
        '''
        Получить историю гарантийных обращений автомобиля.

        Args:
            vin: VIN номер автомобиля

        Returns:
            Словарь с историей гарантийных обращений автомобиля
        '''
        cache_key = self._get_cache_key(MCPTools.WARRANTY_HISTORY, vin=vin)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        result = await self._call_tool(MCPTools.WARRANTY_HISTORY, vin=vin)
        self._put_to_cache(cache_key, result)
        return result

    async def maintenance_history(self, vin: str) -> dict[str, Any]:
        '''
        Получить историю технического обслуживания автомобиля.

        Args:
            vin: VIN номер автомобиля

        Returns:
            Словарь с историей технического обслуживания автомобиля
        '''
        cache_key = self._get_cache_key(MCPTools.MAINTENANCE_HISTORY, vin=vin)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        result = await self._call_tool(MCPTools.MAINTENANCE_HISTORY, vin=vin)
        self._put_to_cache(cache_key, result)
        return result

    async def vehicle_repairs_history(self, vin: str) -> dict[str, Any]:
        '''
        Получить полную историю всех ремонтов автомобиля в дилерской сети.

        Args:
            vin: VIN номер автомобиля

        Returns:
            Словарь с полной историей всех ремонтов автомобиля в дилерской сети
        '''
        cache_key = self._get_cache_key(
            MCPTools.VEHICLE_REPAIRS_HISTORY, vin=vin
        )
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        result = await self._call_tool(
            MCPTools.VEHICLE_REPAIRS_HISTORY, vin=vin
        )
        self._put_to_cache(cache_key, result)
        return result

    async def compliance_rag(self, query: str) -> dict[str, Any]:
        '''
        Поиск информации в базе знаний гарантийной политики и законодательства.

        Args:
            query: Запрос для поиска в базе знаний гарантийной политики

        Returns:
            Словарь с релевантной информацией
            о гарантийной политике и законодательстве
        '''
        cache_key = self._get_cache_key(MCPTools.COMPLIANCE_RAG, query=query)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        result = await self._call_tool(MCPTools.COMPLIANCE_RAG, query=query)
        self._put_to_cache(cache_key, result)
        return result

    async def health_check(self) -> dict[str, Any]:
        '''
        Проверка здоровья MCP сервера.

        Returns:
            Словарь с результатом проверки здоровья MCP сервера
        '''
        if self._client is None:
            await self.connect()

        assert self._client is not None

        try:
            response = await self._client.get('/health')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f'Проверка здоровья MCP сервера failed: {e}')
            return {'status': 'unhealthy', 'error': str(e)}


# Global client instance
_mcp_client: Optional[MCPClient] = None


async def get_mcp_client() -> MCPClient:
    '''
    Получить глобальный экземпляр MCP клиента.

    Returns:
        Инициализированный MCP клиент
    '''
    global _mcp_client

    if _mcp_client is None:
        _mcp_client = MCPClient()
        await _mcp_client.connect()

    return _mcp_client


async def close_mcp_client() -> None:
    '''Закрытие глобального экземпляра MCP клиента.'''
    global _mcp_client

    if _mcp_client is not None:
        await _mcp_client.close()
        _mcp_client = None
