'''
Прямой API-клиент для GigaChat Evolution Platform.

Этот модуль предоставляет реализацию взаимодействия
с GigaChat через прямые HTTP API вызовы с использованием
Api-Key аутентификации.

Основные возможности:
- Прямые вызовы GigaChat API v1/chat/completions
- Аутентификация через Api-Key (без OAuth2)
- Конвертация LangChain message format в GigaChat API format
- Поддержка расширенных параметров (top_p, repetition_penalty)
- Совместимость с LangChain интерфейсом (ainvoke)

Пример использования:
    client = GigaChatAPIClient(
        api_key='your-api-key',
        project_id='your-project-id',
        model='GigaChat',
        temperature=0.1,
    )
    response = await client.ainvoke(messages)
    print(response.content)
'''

from typing import Any, Optional

import httpx
from loguru import logger


class GigaChatAPIError(Exception):
    '''Базовое исключение для ошибок GigaChat API.'''

    pass


class MessageContent:
    '''Простой класс для имитации response.content от LangChain.'''

    def __init__(self, content: str):
        self.content = content

    def __str__(self) -> str:
        return self.content


class GigaChatAPIClient:
    '''
    Клиент для прямого взаимодействия с GigaChat API.

    Этот клиент обрабатывает:
    - Асинхронные вызовы chat/completions API
    - Конвертацию LangChain message format в GigaChat API format
    - Поддержку расширенных параметров GigaChat
    - Аутентификацию через Api-Key
    '''

    CHAT_API_URL = (
        'https://gigachat.api.cloud.ru/api/gigachat/'
        'v1/chat/completions'
    )

    def __init__(
        self,
        api_key: str,
        project_id: str,
        model: str = 'GigaChat',
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        max_tokens: int = 512,
        repetition_penalty: float = 1.0,
        timeout: int = 60,
        verify_ssl_certs: bool = False,
    ) -> None:
        '''
        Инициализация GigaChat API клиента.

        Args:
            api_key: API ключ для аутентификации (Api-Key)
            project_id: ID проекта для Evolution Platform
            model: Название модели GigaChat
            temperature: Температура для генерации (0.0-2.0)
            top_p: Nucleus sampling parameter
            max_tokens: Максимальное количество токенов в ответе
            repetition_penalty: Штраф за повторения
            timeout: Таймаут запросов в секундах
            verify_ssl_certs: Проверять SSL сертификаты
        '''
        self.api_key = api_key
        self.project_id = project_id
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.repetition_penalty = repetition_penalty
        self.timeout = timeout
        self.verify_ssl_certs = verify_ssl_certs

        logger.info(
            f'GigaChat API клиент инициализирован: '
            f'model={model}, temp={temperature}, '
            f'project_id={project_id[:8]}...'
        )

    def _convert_messages(self, messages: list[Any]) -> list[dict[str, str]]:
        '''
        Конвертация LangChain messages в формат GigaChat API.

        Args:
            messages: Список LangChain message объектов

        Returns:
            Список словарей с полями role и content
        '''
        api_messages = []

        for msg in messages:
            # Handle different message types
            role = 'user'  # default
            content = ''

            # Check if it's LangChain message object
            if hasattr(msg, 'type'):
                msg_type = msg.type
                if msg_type == 'system':
                    role = 'system'
                elif msg_type == 'human':
                    role = 'user'
                elif msg_type == 'ai':
                    role = 'assistant'

                content = msg.content if hasattr(msg, 'content') else str(msg)

            # Handle dict format
            elif isinstance(msg, dict):
                role = msg.get('role', 'user')
                content = msg.get('content', '')

            # Handle tuple format (role, content)
            elif isinstance(msg, tuple) and len(msg) == 2:
                role, content = msg

            # Handle string format
            elif isinstance(msg, str):
                content = msg

            api_messages.append({'role': role, 'content': content})

        return api_messages

    async def ainvoke(
        self, messages: list[Any], **kwargs: Any
    ) -> MessageContent:
        '''
        Асинхронный вызов GigaChat API (совместим с LangChain интерфейсом).

        Args:
            messages: Список сообщений (LangChain format или dict)
            **kwargs: Дополнительные параметры (переопределяют настройки)

        Returns:
            Объект с атрибутом content, содержащий ответ модели

        Raises:
            GigaChatAPIError: При ошибке вызова API
        '''
        try:
            # Convert messages to API format
            api_messages = self._convert_messages(messages)

            # Build request payload согласно документации
            payload: dict[str, Any] = {
                'messages': api_messages,
                'model': kwargs.get('model', self.model),
                'options': {
                    'temperature': kwargs.get('temperature', self.temperature),
                    'max_tokens': kwargs.get('max_tokens', self.max_tokens),
                    'repetition_penalty': kwargs.get(
                        'repetition_penalty', self.repetition_penalty
                    ),
                    'max_alternatives': 1,
                },
                'project_id': kwargs.get('project_id', self.project_id),
            }

            # Add optional parameters to options
            top_p_value = kwargs.get('top_p', self.top_p)
            if top_p_value is not None:
                payload['options']['top_p'] = top_p_value

            logger.info(
                f'Вызов GigaChat API: model={payload["model"]}, '
                f'messages_count={len(api_messages)}'
            )
            logger.debug(f'Full payload: {payload}')

            # Make API request с Api-Key аутентификацией
            async with httpx.AsyncClient(
                verify=self.verify_ssl_certs,
                timeout=self.timeout,
            ) as client:
                response = await client.post(
                    self.CHAT_API_URL,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Api-Key {self.api_key}',
                    },
                    json=payload,
                )

                logger.info(f'Response status: {response.status_code}')
                if response.status_code != 200:
                    logger.error(f'Response body: {response.text[:500]}')

                response.raise_for_status()
                result = response.json()

                logger.debug(f'Full API response: {result}')

                # Extract content from response
                # Evolution API использует 'alternatives' вместо 'choices'
                alternatives = (
                    result.get('alternatives') or result.get('choices', [])
                )
                if not alternatives:
                    logger.error(
                        f'No alternatives/choices in response: {result}'
                        )
                    raise GigaChatAPIError(
                        f'Ответ API не содержит alternatives/choices: {result}'
                    )

                message = alternatives[0].get('message', {})
                content = message.get('content', '')

                logger.debug(
                    f'GigaChat API ответил успешно, '
                    f'длина ответа: {len(content)} символов'
                )

                return MessageContent(content)

        except httpx.HTTPStatusError as e:
            error_msg = (
                f'HTTP ошибка при вызове GigaChat API. '
                f'Статус: {e.response.status_code}; '
                f'Сообщение: {e.response.text}'
            )
            logger.error(error_msg)
            raise GigaChatAPIError(error_msg) from e

        except httpx.TimeoutException as e:
            error_msg = 'Таймаут при вызове GigaChat API'
            logger.error(error_msg)
            raise GigaChatAPIError(error_msg) from e

        except Exception as e:
            error_msg = f'Неожиданная ошибка при вызове GigaChat API: {e}'
            logger.error(error_msg, exc_info=True)
            raise GigaChatAPIError(error_msg) from e

    async def invoke(
        self,
        messages: list[Any],
        **kwargs: Any
    ) -> MessageContent:
        '''
        Синхронный интерфейс для совместимости.

        Args:
            messages: Список сообщений
            **kwargs: Дополнительные параметры

        Returns:
            Объект с атрибутом content
        '''
        return await self.ainvoke(messages, **kwargs)
