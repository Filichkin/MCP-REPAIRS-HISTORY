'''
MCP (Model Context Protocol) client for warranty service tools.

This module provides a client for interacting with the MCP server that
exposes warranty-related tools and data sources.
'''

import asyncio
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
    '''Base exception for MCP client errors.'''

    pass


class MCPConnectionError(MCPClientError):
    '''Raised when connection to MCP server fails.'''

    pass


class MCPToolNotFoundError(MCPClientError):
    '''Raised when requested tool is not available.'''

    pass


class MCPValidationError(MCPClientError):
    '''Raised when tool input validation fails.'''

    pass


class MCPClient:
    '''
    Client for interacting with MCP server.

    This client handles:
    - Tool discovery and validation
    - Asynchronous tool execution
    - Retry logic and error handling
    - Optional response caching
    '''

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        enable_cache: bool = True,
    ) -> None:
        '''
        Initialize MCP client.

        Args:
            base_url: MCP server base URL (default from settings)
            timeout: Request timeout in seconds (default from settings)
            max_retries: Maximum retry attempts (default from settings)
            enable_cache: Enable response caching
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

        logger.info(f'MCP client initialized with base_url={self.base_url}')

    async def __aenter__(self) -> 'MCPClient':
        '''Async context manager entry.'''
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        '''Async context manager exit.'''
        await self.close()

    async def connect(self) -> None:
        '''Establish connection to MCP server.'''
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True,
            )
            logger.debug('MCP HTTP client created')

    async def close(self) -> None:
        '''Close connection to MCP server.'''
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug('MCP HTTP client closed')

    def _get_cache_key(self, tool_name: str, **kwargs: Any) -> str:
        '''Generate cache key from tool name and arguments.'''
        # Simple cache key: tool_name + sorted args
        args_str = '_'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))
        return f'{tool_name}:{args_str}'

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        '''Get value from cache if not expired.'''
        if not self.enable_cache:
            return None

        if cache_key in self._cache:
            value, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.debug(f'Cache hit for key: {cache_key}')
                return value
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
                logger.debug(f'Cache expired for key: {cache_key}')

        return None

    def _put_to_cache(self, cache_key: str, value: Any) -> None:
        '''Put value to cache with current timestamp.'''
        if self.enable_cache:
            self._cache[cache_key] = (value, datetime.now())
            logger.debug(f'Cached value for key: {cache_key}')

    def clear_cache(self) -> None:
        '''Clear all cached responses.'''
        self._cache.clear()
        logger.info('Cache cleared')

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True,
    )
    async def _call_tool(
        self, tool_name: str, **kwargs: Any
    ) -> dict[str, Any]:
        '''
        Call MCP tool with retry logic.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            Tool response data

        Raises:
            MCPConnectionError: If connection fails
            MCPToolNotFoundError: If tool not found
            MCPValidationError: If validation fails
        '''
        if self._client is None:
            await self.connect()

        assert self._client is not None

        try:
            # MCP server endpoint format: /tools/{tool_name}
            endpoint = f'/tools/{tool_name}'

            logger.debug(f'Calling MCP tool: {tool_name} with args: {kwargs}')

            response = await self._client.post(
                endpoint,
                json=kwargs,
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

            logger.debug(f'MCP tool {tool_name} response received')
            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise MCPToolNotFoundError(
                    f'Tool not found: {tool_name}'
                ) from e
            elif e.response.status_code == 422:
                raise MCPValidationError(
                    f'Validation error for tool {tool_name}: {e.response.text}'
                ) from e
            else:
                raise MCPConnectionError(
                    f'HTTP error calling tool {tool_name}: {e}'
                ) from e

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise MCPConnectionError(
                f'Connection error calling tool {tool_name}: {e}'
            ) from e

        except Exception as e:
            raise MCPClientError(
                f'Unexpected error calling tool {tool_name}: {e}'
            ) from e

    async def warranty_days(self, vin: str) -> dict[str, Any]:
        '''
        Get warranty repair days statistics by year.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Dictionary with yearly statistics of repair days
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
        Get warranty claims history.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Dictionary with warranty history records
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
        Get maintenance history.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Dictionary with maintenance records
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
        Get complete vehicle repairs history from dealer network.

        Args:
            vin: Vehicle Identification Number

        Returns:
            Dictionary with complete repair history
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
        Search warranty compliance knowledge base using RAG.

        Args:
            query: Search query

        Returns:
            Dictionary with relevant compliance information
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
        Check MCP server health.

        Returns:
            Health check response
        '''
        if self._client is None:
            await self.connect()

        assert self._client is not None

        try:
            response = await self._client.get('/health')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f'Health check failed: {e}')
            return {'status': 'unhealthy', 'error': str(e)}


# Global client instance
_mcp_client: Optional[MCPClient] = None


async def get_mcp_client() -> MCPClient:
    '''
    Get global MCP client instance.

    Returns:
        Initialized MCP client
    '''
    global _mcp_client

    if _mcp_client is None:
        _mcp_client = MCPClient()
        await _mcp_client.connect()

    return _mcp_client


async def close_mcp_client() -> None:
    '''Close global MCP client instance.'''
    global _mcp_client

    if _mcp_client is not None:
        await _mcp_client.close()
        _mcp_client = None
