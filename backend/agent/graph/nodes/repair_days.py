'''
Узел дней в ремонте для графа гарантийного агента.

Этот узел анализирует дни в ремонте
и проверяет соответствие 30-дневному лимиту.
'''

import json

from loguru import logger

from backend.agent.graph.state import AgentState, AgentResult
from backend.agent.llm.gigachat_setup import get_repair_days_llm
from backend.agent.llm.prompts import get_repair_days_prompt
from backend.agent.tools.mcp_client import get_mcp_client
from backend.config import GraphNodes, AgentRoles


async def repair_days_node(state: AgentState) -> AgentState:
    '''
    Анализировать дни в ремонте и проверять соответствие 30-дневному лимиту.

    Args:
        state: Текущее состояние агента

    Returns:
        Обновленное состояние с результатом анализа дней в ремонте
    '''
    logger.info('Узел дней в ремонте запущен')

    try:
        # Check if VIN is available
        if not state.vin:
            error_msg = 'VIN требуется для анализа дней в ремонте'
            logger.warning(error_msg)
            state.repair_days_result = AgentResult(
                agent_name=AgentRoles.REPAIR_DAYS['name'],
                success=False,
                error=error_msg,
            )
            state.mark_step_completed(GraphNodes.REPAIR_DAYS)
            return state

        # Get MCP client and fetch data
        logger.debug(f'Получение данных дней в ремонте для VIN: {state.vin}')
        client = await get_mcp_client()
        warranty_days_data = await client.warranty_days(state.vin)

        # Check for errors in data
        if 'error' in warranty_days_data:
            error_msg = f'MCP error: {warranty_days_data["error"]}'
            logger.error(error_msg)
            state.repair_days_result = AgentResult(
                agent_name=AgentRoles.REPAIR_DAYS['name'],
                success=False,
                error=error_msg,
                data=warranty_days_data,
            )
            state.mark_step_completed(GraphNodes.REPAIR_DAYS)
            return state

        # Get LLM and prompt
        llm = get_repair_days_llm()
        prompt = get_repair_days_prompt()

        # Format data for LLM
        data_formatted = json.dumps(
            warranty_days_data, ensure_ascii=False, indent=2
        )

        # Format prompt
        messages = prompt.format_messages(
            query=state.query,
            vin=state.vin,
            warranty_days_data=data_formatted,
        )

        # Invoke LLM
        logger.debug('Вызов дней в ремонте LLM')
        response = await llm.ainvoke(messages)
        analysis = response.content

        logger.info('Анализ дней в ремонте завершен')

        # Create result
        state.repair_days_result = AgentResult(
            agent_name=AgentRoles.REPAIR_DAYS['name'],
            success=True,
            data={
                'analysis': analysis,
                'raw_data': warranty_days_data,
                'vin': state.vin,
            },
        )

        # Mark step completed
        state.mark_step_completed(GraphNodes.REPAIR_DAYS)

        return state

    except Exception as e:
        error_msg = f'Ошибка дней в ремонте: {str(e)}'
        logger.error(error_msg)
        state.add_error(error_msg)

        state.repair_days_result = AgentResult(
            agent_name=AgentRoles.REPAIR_DAYS['name'],
            success=False,
            error=error_msg,
        )

        state.mark_step_completed(GraphNodes.REPAIR_DAYS)
        return state
