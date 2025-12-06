'''
Глобальный менеджер GigaChat LLM для setup и initialization.

Этот модуль обрабатывает инициализацию и конфигурацию GigaChat
для использования с LangChain агентами.
'''

from typing import Optional
from langchain_gigachat import GigaChat
from loguru import logger

from backend.config import settings


class GigaChatManager:
    '''Manager for GigaChat LLM instances.'''

    _instances: dict[str, GigaChat] = {}

    @classmethod
    def get_llm(
        cls,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        streaming: bool = False,
    ) -> GigaChat:
        '''
        Получить или создать экземпляр GigaChat с указанными параметрами.

        Args:
            temperature: Температура для ответов (0.0-2.0)
            model: Название модели (по умолчанию из settings)
            streaming: Включить потоковые ответы

        Returns:
            Настроенный экземпляр GigaChat
        '''
        temp = temperature or settings.gigachat_temperature
        model_name = model or settings.gigachat_model

        # Create cache key
        cache_key = f'{model_name}_{temp}_{streaming}'

        if cache_key not in cls._instances:
            logger.info(
                f'Создаем новый экземпляр GigaChat: '
                f'model={model_name}, temp={temp}, streaming={streaming}'
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

            cls._instances[cache_key] = llm
            logger.debug(f'Экземпляр GigaChat создан и кэширован: {cache_key}')

        return cls._instances[cache_key]

    @classmethod
    def clear_cache(cls) -> None:
        '''Очистить все кэшированные экземпляры LLM.'''
        cls._instances.clear()
        logger.info('Кэш экземпляров GigaChat очищен')


def get_classifier_llm() -> GigaChat:
    '''
    Получить LLM для агента Query Classifier.

    Returns:
        Экземпляр GigaChat с низкой температурой для точного классификации
    '''
    from backend.config import AgentRoles

    return GigaChatManager.get_llm(
        temperature=AgentRoles.CLASSIFIER['temperature']
    )


def get_repair_days_llm() -> GigaChat:
    '''
    Получить LLM для агента Repair Days Tracker.

    Returns:
        Экземпляр GigaChat с настройками для анализа дней в ремонте
    '''
    from backend.config import AgentRoles

    return GigaChatManager.get_llm(
        temperature=AgentRoles.REPAIR_DAYS['temperature']
    )


def get_compliance_llm() -> GigaChat:
    '''
    Получить LLM для агента Warranty Compliance.

    Returns:
        Экземпляр GigaChat с настройками для интерпретации соответствия
    '''
    from backend.config import AgentRoles

    return GigaChatManager.get_llm(
        temperature=AgentRoles.COMPLIANCE['temperature']
    )


def get_dealer_insights_llm() -> GigaChat:
    '''
    Получить LLM для агента Dealer Insights.

    Returns:
        Экземпляр GigaChat с настройками для анализа шаблонов
    '''
    from backend.config import AgentRoles

    return GigaChatManager.get_llm(
        temperature=AgentRoles.DEALER_INSIGHTS['temperature']
    )


def get_report_summary_llm() -> GigaChat:
    '''
    Получить LLM для агента Report & Summary.

    Returns:
        Экземпляр GigaChat с настройками для генерации отчёта
    '''
    from backend.config import AgentRoles

    return GigaChatManager.get_llm(
        temperature=AgentRoles.REPORT_SUMMARY['temperature']
    )
