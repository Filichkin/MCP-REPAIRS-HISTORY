'''
MCP (Model Context Protocol) клиент для сервиса гарантийных инструментов.

Этот модуль предоставляет клиент для взаимодействия с MCP сервером,
который предоставляет инструменты и данные для работы с гарантийными вопросами.
'''

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from typing import Any, Optional
from datetime import datetime, timedelta

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from loguru import logger

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
        auth_token: Optional[str] = None,
    ) -> None:
        '''
        Инициализация MCP клиента.

        Args:
            base_url: Базовый URL MCP сервера (по умолчанию из settings)
            timeout: Таймаут запроса в секундах (по умолчанию из settings)
            max_retries: Максимальное количество повторных попыток
            (по умолчанию из settings)
            enable_cache: Включить кэширование ответов
            auth_token: Bearer токен для аутентификации
            (по умолчанию из settings)
        '''
        self.base_url = base_url or settings.mcp_server_url
        self.timeout = timeout or settings.mcp_timeout
        self.max_retries = max_retries or settings.mcp_max_retries
        self.enable_cache = enable_cache
        self.auth_token = auth_token or settings.mcp_auth_token

        # Simple in-memory cache
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(seconds=settings.mcp_cache_ttl)

        # MCP HTTP client
        self._stack: Optional[AsyncExitStack] = None
        self._session: Optional[ClientSession] = None

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
        if self._session is None:
            stack = AsyncExitStack()
            # Build URL with /mcp endpoint for Streamable HTTP transport
            url = f'{self.base_url}/mcp'

            # Prepare headers with auth token if provided
            headers: dict[str, str] | None = None
            if self.auth_token:
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                logger.debug(
                    'MCP клиент использует Bearer token аутентификацию'
                    )

            # Open Streamable HTTP streams
            read_stream, write_stream, _ = (
                await stack.enter_async_context(
                    streamablehttp_client(
                        url=url,
                        timeout=self.timeout,
                        headers=headers,
                    )
                )
            )
            # Open MCP session
            session = (
                await stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
            )
            await session.initialize()
            self._stack = stack
            self._session = session
            logger.debug('MCP HTTP клиент создан и инициализирован')

    async def close(self) -> None:
        '''Закрытие соединения с MCP сервером.'''
        if self._stack is not None:
            try:
                await self._stack.aclose()
            except (asyncio.CancelledError, GeneratorExit):
                pass
            except RuntimeError as e:
                if (
                    'exit cancel scope in a different task'
                    not in str(e).lower()
                ):
                    raise
            finally:
                self._stack = None
                self._session = None
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

    async def _call_tool(
        self, tool_name: str, **kwargs: Any
    ) -> dict[str, Any]:
        '''
        Вызов MCP инструмента через SSE.

        Args:
            tool_name: Название инструмента для вызова
            **kwargs: Аргументы инструмента

        Returns:
            Словарь с данными ответа инструмента:
            - result: текстовое содержимое (для обратной совместимости)
            - structured_content: структурированные JSON данные (если есть)
            - meta: метаданные выполнения (если есть)
            - is_error: флаг ошибки (если есть)

        Raises:
            MCPConnectionError: Если соединение не установлено
            MCPToolNotFoundError: Если инструмент не найден
            MCPClientError: При других ошибках
        '''
        if self._session is None:
            await self.connect()

        assert self._session is not None

        try:
            logger.debug(
                f'Вызов MCP инструмента: {tool_name} с аргументами: '
                f'{kwargs}'
            )

            # Вызываем инструмент через MCP session
            result = await self._session.call_tool(
                name=tool_name,
                arguments=kwargs
            )

            # Извлекаем текстовое содержимое из ответа
            blocks = getattr(result, 'content', [])
            texts: list[str] = []
            for block in blocks:
                text = getattr(block, 'text', None)
                if text:
                    texts.append(text)

            response_text = '\n'.join(texts).strip()

            # Извлекаем структурированные данные (если есть)
            structured_content = getattr(result, 'structured_content', None)

            # Извлекаем метаданные (если есть)
            meta = getattr(result, '_meta', None)

            # Проверяем флаг ошибки
            is_error = getattr(result, 'isError', False)

            logger.debug(
                f'MCP инструмент {tool_name} ответил '
                f'(is_error={is_error}, '
                f'has_structured={structured_content is not None})'
            )

            # Формируем расширенный ответ
            response = {
                'result': response_text,  # Обратная совместимость
            }

            # Добавляем дополнительные поля если они есть
            if structured_content is not None:
                response['structured_content'] = structured_content

            if meta is not None:
                response['meta'] = meta

            if is_error:
                response['is_error'] = is_error
                logger.warning(
                    f'MCP инструмент {tool_name} вернул ошибку: '
                    f'{response_text}'
                )

            return response

        except Exception as e:
            error_msg = str(e).lower()
            if 'not found' in error_msg or 'unknown tool' in error_msg:
                raise MCPToolNotFoundError(
                    f'Инструмент не найден: {tool_name}'
                ) from e
            else:
                raise MCPClientError(
                    f'Ошибка при вызове инструмента {tool_name}: {e}'
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
        logger.info(f'Health check для MCP сервера: {self.base_url}')
        try:
            # Пробуем подключиться и получить список инструментов
            if self._session is None:
                await self.connect()

            assert self._session is not None

            # Список инструментов - простой способ
            # проверить что сервер работает
            tools_response = await self._session.list_tools()
            tool_names = [t.name for t in tools_response.tools]

            logger.info(
                f'MCP сервер healthy - доступно {len(tool_names)} инструментов'
            )
            return {'status': 'healthy', 'tools_count': len(tool_names)}

        except asyncio.TimeoutError as e:
            logger.warning(f'Таймаут при проверке здоровья MCP сервера: {e}')
            return {'status': 'timeout', 'error': 'Connection timeout'}
        except Exception as e:
            logger.error(
                f'Проверка здоровья MCP сервера failed: {e}',
                exc_info=True
                )
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
