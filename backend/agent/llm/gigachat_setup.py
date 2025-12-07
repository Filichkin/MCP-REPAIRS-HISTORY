'''
Глобальный менеджер GigaChat LLM для setup и initialization.

Этот модуль обрабатывает инициализацию и конфигурацию GigaChat
для использования с LangChain агентами.

Поддерживает два метода:
1. langchain_gigachat (по умолчанию) - через библиотеку
2. Прямой API GigaChat - через gigachat_api_client

Переключение метода:
    В .env файле установите:
    GIGACHAT_USE_API=false  # для langchain_gigachat
    GIGACHAT_USE_API=true   # для прямого API

Расширенные параметры API (только для GIGACHAT_USE_API=true):
    GIGACHAT_TOP_P=0.9
    GIGACHAT_MAX_TOKENS=1024
    GIGACHAT_REPETITION_PENALTY=1.1
'''

from typing import Optional, Union
from langchain_gigachat import GigaChat
from loguru import logger

from backend.config import AgentRoles, settings
from backend.agent.llm.gigachat_api_client import (
    GigaChatAPIClient
)


class GigaChatManager:
    '''
    Manager for GigaChat LLM instances.
    Supports two methods: langchain_gigachat and direct API.
    '''

    _instances: dict[str, Union[GigaChat, GigaChatAPIClient]] = {}

    @classmethod
    def get_llm(
        cls,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        streaming: bool = False,
    ) -> Union[GigaChat, GigaChatAPIClient]:
        '''
        Получить или создать экземпляр GigaChat.

        Метод автоматически выбирает между langchain_gigachat
        и прямым API на основе settings.gigachat_use_api.

        Args:
            temperature: Температура для ответов (0.0-2.0)
            model: Название модели (по умолчанию из settings)
            streaming: Включить потоковые ответы
                (только для langchain_gigachat)

        Returns:
            Настроенный экземпляр GigaChat
            или GigaChatAPIClient
        '''

        temp = temperature or settings.gigachat_temperature
        model_name = model or settings.gigachat_model
        use_api = settings.gigachat_use_api

        # Create cache key
        cache_key = f'{model_name}_{temp}_{streaming}_{use_api}'

        if cache_key not in cls._instances:
            # Очищаем старый кэш при первом создании с новым методом
            if use_api and cls._instances:
                logger.info('Очищаем старый кэш LLM при переключении на API')
                cls._instances.clear()

            if use_api:
                # Для Evolution API используем только модель GigaChat
                api_model = 'GigaChat'
                logger.info(
                    f'Создаем новый экземпляр GigaChat API Client: '
                    f'model={api_model}, temp={temp}'
                )

                llm = GigaChatAPIClient(
                    api_key=settings.gigachat_api_key_evolution,
                    project_id=settings.evolution_project_id,
                    model=api_model,
                    temperature=temp,
                    top_p=settings.gigachat_top_p,
                    max_tokens=settings.gigachat_max_tokens,
                    repetition_penalty=(
                        settings.gigachat_repetition_penalty
                    ),
                    timeout=settings.gigachat_timeout,
                    verify_ssl_certs=False,  # For development
                )

                logger.debug(
                    f'GigaChat API Client создан: {cache_key}'
                )
            else:
                logger.info(
                    f'Создаем новый экземпляр GigaChat (langchain): '
                    f'model={model_name}, temp={temp}, '
                    f'streaming={streaming}'
                )

                llm = GigaChat(
                    credentials=settings.gigachat_api_key,
                    scope=settings.gigachat_scope,
                    model=model_name,
                    temperature=temp,
                    timeout=settings.gigachat_timeout,
                    verify_ssl_certs=False,  # For development
                    streaming=streaming,
                )

                logger.debug(
                    f'Экземпляр GigaChat (langchain) создан и '
                    f'кэширован: {cache_key}'
                )

            cls._instances[cache_key] = llm

        return cls._instances[cache_key]

    @classmethod
    def clear_cache(cls) -> None:
        '''Очистить все кэшированные экземпляры LLM.'''
        cls._instances.clear()
        logger.info('Кэш экземпляров GigaChat очищен')


def get_classifier_llm() -> Union[GigaChat, GigaChatAPIClient]:
    '''
    Получить LLM для агента Query Classifier.

    Returns:
        Экземпляр GigaChat или GigaChatAPIClient
        с низкой температурой для точной классификации
    '''

    return GigaChatManager.get_llm(
        temperature=AgentRoles.CLASSIFIER['temperature']
    )


def get_repair_days_llm() -> Union[GigaChat, GigaChatAPIClient]:
    '''
    Получить LLM для агента Repair Days Tracker.

    Returns:
        Экземпляр GigaChat или GigaChatAPIClient
        с настройками для анализа дней в ремонте
    '''

    return GigaChatManager.get_llm(
        temperature=AgentRoles.REPAIR_DAYS['temperature']
    )


def get_compliance_llm() -> Union[GigaChat, GigaChatAPIClient]:
    '''
    Получить LLM для агента Warranty Compliance.

    Returns:
        Экземпляр GigaChat или GigaChatAPIClient
        с настройками для интерпретации соответствия
    '''

    return GigaChatManager.get_llm(
        temperature=AgentRoles.COMPLIANCE['temperature']
    )


def get_dealer_insights_llm() -> Union[GigaChat, GigaChatAPIClient]:
    '''
    Получить LLM для агента Dealer Insights.

    Returns:
        Экземпляр GigaChat или GigaChatAPIClient
        с настройками для анализа шаблонов
    '''

    return GigaChatManager.get_llm(
        temperature=AgentRoles.DEALER_INSIGHTS['temperature']
    )


def get_report_summary_llm() -> Union[GigaChat, GigaChatAPIClient]:
    '''
    Получить LLM для агента Report & Summary.

    Returns:
        Экземпляр GigaChat или GigaChatAPIClient
        с настройками для генерации отчёта
    '''

    return GigaChatManager.get_llm(
        temperature=AgentRoles.REPORT_SUMMARY['temperature']
    )
