'''
LangChain tool wrappers for MCP tools.

This module provides LangChain-compatible tool wrappers around the MCP client
for use with LangGraph agents.
'''

from typing import Any, Optional
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from loguru import logger

from backend.agent.tools.mcp_client import get_mcp_client
from backend.agent.utils.vin_validator import validate_vin


class WarrantyDaysInput(BaseModel):
    '''Input schema for warranty_days tool.'''

    vin: str = Field(
        description='VIN автомобиля (17 символов, латинские буквы и цифры)'
    )


class WarrantyDaysTool(BaseTool):
    '''Tool for getting warranty repair days statistics.'''

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
        '''Sync version - not implemented.'''
        raise NotImplementedError('Use async version (ainvoke)')

    async def _arun(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''
        Async execution of warranty_days tool.

        Args:
            vin: Vehicle Identification Number
            run_manager: Callback manager

        Returns:
            Warranty days statistics
        '''
        # Validate VIN
        is_valid, error_msg = validate_vin(vin)
        if not is_valid:
            logger.warning(f'Invalid VIN: {vin}, error: {error_msg}')
            return {'error': error_msg, 'vin': vin}

        try:
            client = await get_mcp_client()
            result = await client.warranty_days(vin)
            logger.info(f'warranty_days executed for VIN: {vin}')
            return result
        except Exception as e:
            logger.error(f'Error executing warranty_days: {e}')
            return {'error': str(e), 'vin': vin}


class WarrantyHistoryInput(BaseModel):
    '''Input schema for warranty_history tool.'''

    vin: str = Field(description='VIN автомобиля')


class WarrantyHistoryTool(BaseTool):
    '''Tool for getting warranty claims history.'''

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
        '''Sync version - not implemented.'''
        raise NotImplementedError('Use async version (ainvoke)')

    async def _arun(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Async execution of warranty_history tool.'''
        is_valid, error_msg = validate_vin(vin)
        if not is_valid:
            logger.warning(f'Invalid VIN: {vin}, error: {error_msg}')
            return {'error': error_msg, 'vin': vin}

        try:
            client = await get_mcp_client()
            result = await client.warranty_history(vin)
            logger.info(f'warranty_history executed for VIN: {vin}')
            return result
        except Exception as e:
            logger.error(f'Error executing warranty_history: {e}')
            return {'error': str(e), 'vin': vin}


class MaintenanceHistoryInput(BaseModel):
    '''Input schema for maintenance_history tool.'''

    vin: str = Field(description='VIN автомобиля')


class MaintenanceHistoryTool(BaseTool):
    '''Tool for getting maintenance history.'''

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
        '''Sync version - not implemented.'''
        raise NotImplementedError('Use async version (ainvoke)')

    async def _arun(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Async execution of maintenance_history tool.'''
        is_valid, error_msg = validate_vin(vin)
        if not is_valid:
            logger.warning(f'Invalid VIN: {vin}, error: {error_msg}')
            return {'error': error_msg, 'vin': vin}

        try:
            client = await get_mcp_client()
            result = await client.maintenance_history(vin)
            logger.info(f'maintenance_history executed for VIN: {vin}')
            return result
        except Exception as e:
            logger.error(f'Error executing maintenance_history: {e}')
            return {'error': str(e), 'vin': vin}


class VehicleRepairsHistoryInput(BaseModel):
    '''Input schema for vehicle_repairs_history tool.'''

    vin: str = Field(description='VIN автомобиля')


class VehicleRepairsHistoryTool(BaseTool):
    '''Tool for getting complete vehicle repairs history.'''

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
        '''Sync version - not implemented.'''
        raise NotImplementedError('Use async version (ainvoke)')

    async def _arun(
        self,
        vin: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Async execution of vehicle_repairs_history tool.'''
        is_valid, error_msg = validate_vin(vin)
        if not is_valid:
            logger.warning(f'Invalid VIN: {vin}, error: {error_msg}')
            return {'error': error_msg, 'vin': vin}

        try:
            client = await get_mcp_client()
            result = await client.vehicle_repairs_history(vin)
            logger.info(f'vehicle_repairs_history executed for VIN: {vin}')
            return result
        except Exception as e:
            logger.error(f'Error executing vehicle_repairs_history: {e}')
            return {'error': str(e), 'vin': vin}


class ComplianceRAGInput(BaseModel):
    '''Input schema for compliance_rag tool.'''

    query: str = Field(
        description='Запрос для поиска в базе знаний гарантийной политики'
    )


class ComplianceRAGTool(BaseTool):
    '''Tool for searching warranty compliance knowledge base.'''

    name: str = 'compliance_rag'
    description: str = '''
    Поиск информации в базе знаний гарантийной политики и законодательства.
    Используй этот инструмент для:
    - Интерпретации условий гарантии
    - Поиска релевантных статей закона о защите прав потребителей
    - Объяснения прав владельца автомобиля
    - Получения информации о гарантийных обязательствах
    
    Входные данные: текстовый запрос на русском языке
    '''
    args_schema: type[BaseModel] = ComplianceRAGInput

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Sync version - not implemented.'''
        raise NotImplementedError('Use async version (ainvoke)')

    async def _arun(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict[str, Any]:
        '''Async execution of compliance_rag tool.'''
        if not query or not query.strip():
            return {'error': 'Query cannot be empty'}

        try:
            client = await get_mcp_client()
            result = await client.compliance_rag(query)
            logger.info(f'compliance_rag executed for query: {query[:50]}...')
            return result
        except Exception as e:
            logger.error(f'Error executing compliance_rag: {e}')
            return {'error': str(e), 'query': query}


def get_all_tools() -> list[BaseTool]:
    '''
    Get list of all available LangChain tools.

    Returns:
        List of tool instances
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
    Get tool by name.

    Args:
        name: Tool name

    Returns:
        Tool instance or None if not found
    '''
    tools = get_all_tools()
    for tool in tools:
        if tool.name == name:
            return tool
    return None
