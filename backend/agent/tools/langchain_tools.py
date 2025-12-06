'''
LangChain инструменты для MCP сервера.

Этот модуль предоставляет LangChain-совместимые инструменты для MCP клиента
для использования с LangGraph агентами.
'''

from typing import Any, Optional

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from loguru import logger
from pydantic import BaseModel, Field

from backend.agent.tools.mcp_client import get_mcp_client
from backend.agent.utils.vin_validator import validate_vin


class WarrantyDaysInput(BaseModel):
    '''Схема входных данных для инструмента warranty_days.'''

    vin: str = Field(
        description='VIN автомобиля (17 символов, латинские буквы и цифры)'
    )


class WarrantyDaysTool(BaseTool):
    '''Инструмент для получения статистики дней простоя автомобиля в ремонте'''

    name: str = 'warranty_days'
    description: str = '''
    Получить статистику дней простоя автомобиля в ремонте по годам.
    Используй этот инструмент для анализа:
    - Сколько дней в году автомобиль находился в ремонте
    - Соблюдения 30-дневного лимита по закону о защите прав потребителей
    - Прогнозирования рисков превышения лимита

    Входные данные: VIN автомобиля (17 символов)
    '''
    args_schema: type[BaseModel] = WarrantyDaysInput

    def _run(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Синхронная версия - не реализована.'''
        raise NotImplementedError('Используй асинхронную версию (ainvoke)')

    async def _arun(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''
        Асинхронное выполнение инструмента warranty_days.

        Args:
            vin: VIN автомобиля
            run_manager: Менеджер обратных вызовов

        Returns:
            Статистика дней простоя автомобиля в ремонте
        '''
        # Validate VIN
        is_valid, error_msg = validate_vin(vin)
        if not is_valid:
            logger.warning(f'Неверный VIN: {vin}, ошибка: {error_msg}')
            return {'error': error_msg, 'vin': vin}

        try:
            client = await get_mcp_client()
            result = await client.warranty_days(vin)
            logger.info(f'warranty_days выполнен для VIN: {vin}')
            return result
        except Exception as e:
            logger.error(f'Ошибка при выполнении warranty_days: {e}')
            return {'error': str(e), 'vin': vin}


class WarrantyHistoryInput(BaseModel):
    '''Схема входных данных для инструмента warranty_history.'''

    vin: str = Field(description='VIN автомобиля')


class WarrantyHistoryTool(BaseTool):
    '''Инструмент для получения истории гарантийных обращений автомобиля.'''

    name: str = 'warranty_history'
    description: str = '''
    Получить полную историю гарантийных обращений автомобиля.
    Используй этот инструмент для:
    - Просмотра всех гарантийных ремонтов
    - Анализа типов неисправностей
    - Изучения дат и периодов ремонтов

    Входные данные: VIN автомобиля
    '''
    args_schema: type[BaseModel] = WarrantyHistoryInput

    def _run(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Синхронная версия - не реализована.'''
        raise NotImplementedError('Используй асинхронную версию (ainvoke)')

    async def _arun(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Асинхронное выполнение инструмента warranty_history.'''
        is_valid, error_msg = validate_vin(vin)
        if not is_valid:
            logger.warning(f'Неверный VIN: {vin}, ошибка: {error_msg}')
            return {'error': error_msg, 'vin': vin}

        try:
            client = await get_mcp_client()
            result = await client.warranty_history(vin)
            logger.info(f'warranty_history выполнен для VIN: {vin}')
            return result
        except Exception as e:
            logger.error(f'Ошибка при выполнении warranty_history: {e}')
            return {'error': str(e), 'vin': vin}


class MaintenanceHistoryInput(BaseModel):
    '''Схема входных данных для инструмента maintenance_history.'''

    vin: str = Field(description='VIN автомобиля')


class MaintenanceHistoryTool(BaseTool):
    '''Инструмент для получения истории технического обслуживания автомобиля'''

    name: str = 'maintenance_history'
    description: str = '''
    Получить историю технического обслуживания (ТО) автомобиля.
    Используй этот инструмент для:
    - Просмотра всех проведённых ТО
    - Проверки соблюдения регламента обслуживания
    - Анализа регулярности обслуживания

    Входные данные: VIN автомобиля
    '''
    args_schema: type[BaseModel] = MaintenanceHistoryInput

    def _run(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Синхронная версия - не реализована.'''
        raise NotImplementedError('Используй асинхронную версию (ainvoke)')

    async def _arun(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Асинхронное выполнение инструмента maintenance_history.'''
        is_valid, error_msg = validate_vin(vin)
        if not is_valid:
            logger.warning(f'Неверный VIN: {vin}, ошибка: {error_msg}')
            return {'error': error_msg, 'vin': vin}

        try:
            client = await get_mcp_client()
            result = await client.maintenance_history(vin)
            logger.info(f'maintenance_history выполнен для VIN: {vin}')
            return result
        except Exception as e:
            logger.error(f'Ошибка при выполнении maintenance_history: {e}')
            return {'error': str(e), 'vin': vin}


class VehicleRepairsHistoryInput(BaseModel):
    '''Схема входных данных для инструмента vehicle_repairs_history.'''

    vin: str = Field(description='VIN автомобиля')


class VehicleRepairsHistoryTool(BaseTool):
    '''
    Инструмент для получения полной истории
    всех ремонтов автомобиля в дилерской сети
    '''

    name: str = 'vehicle_repairs_history'
    description: str = '''
    Получить полную историю всех ремонтов автомобиля в дилерской сети.
    Используй этот инструмент для:
    - Комплексного анализа всех ремонтов (гарантийных и платных)
    - Выявления повторяющихся проблем
    - Анализа работы дилерских центров
    - Поиска паттернов неисправностей

    Входные данные: VIN автомобиля
    '''
    args_schema: type[BaseModel] = VehicleRepairsHistoryInput

    def _run(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Синхронная версия - не реализована.'''
        raise NotImplementedError('Используй асинхронную версию (ainvoke)')

    async def _arun(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Асинхронное выполнение инструмента vehicle_repairs_history.'''
        is_valid, error_msg = validate_vin(vin)
        if not is_valid:
            logger.warning(f'Неверный VIN: {vin}, ошибка: {error_msg}')
            return {'error': error_msg, 'vin': vin}

        try:
            client = await get_mcp_client()
            result = await client.vehicle_repairs_history(vin)
            logger.info(f'vehicle_repairs_history выполнен для VIN: {vin}')
            return result
        except Exception as e:
            logger.error(f'Ошибка при выполнении vehicle_repairs_history: {e}')
            return {'error': str(e), 'vin': vin}


class ComplianceRAGInput(BaseModel):
    '''Input sc hema for compliance_rag tool.'''

    query: str = Field(
        description='Запрос для поиска в базе знаний гарантийной политики'
    )


class ComplianceRAGTool(BaseTool):
    '''
    Инструмент для поиска информации в базе знаний
    гарантийной политики и законодательства.
    '''

    name: str = 'compliance_rag'
    description: str = '''
    Поиск информации в базе знаний гарантийной политики
    и стандартов клиентской службы дилера.
    Используй этот инструмент для:
    - Интерпретации условий гарантии
    - Поиска релевантных статей стандартов клиентской службы дилера
    - Объяснения действий клиентской службы дилера
    - Получения информации о гарантийных обязательствах

    Входные данные: текстовый запрос на русском языке
    '''
    args_schema: type[BaseModel] = ComplianceRAGInput

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Синхронная версия - не реализована.'''
        raise NotImplementedError('Используй асинхронную версию (ainvoke)')

    async def _arun(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Асинхронное выполнение инструмента compliance_rag.'''
        if not query or not query.strip():
            return {'error': 'Запрос не может быть пустым'}

        try:
            client = await get_mcp_client()
            result = await client.compliance_rag(query)
            logger.info(
                f'compliance_rag выполнен для запроса: {query[:50]}...'
                )
            return result
        except Exception as e:
            logger.error(f'Ошибка при выполнении compliance_rag: {e}')
            return {'error': str(e), 'query': query}


def get_all_tools() -> list[BaseTool]:
    '''
    Получить список всех доступных инструментов LangChain.

    Returns:
        Список экземпляров инструментов
    '''
    return [
        WarrantyDaysTool(),
        WarrantyHistoryTool(),
        MaintenanceHistoryTool(),
        VehicleRepairsHistoryTool(),
        ComplianceRAGTool(),
    ]


def get_tool_by_name(name: str) -> Optional[BaseTool]:
    '''
    Получить инструмент по названию.

    Args:
        name: Название инструмента

    Returns:
        Экземпляр инструмента или None, если инструмент не найден
    '''
    tools = get_all_tools()
    for tool in tools:
        if tool.name == name:
            return tool
    return None
