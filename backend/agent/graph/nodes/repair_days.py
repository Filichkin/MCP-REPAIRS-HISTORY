'''
Узел дней в ремонте для графа гарантийного агента.

Этот узел получает статистику дней в ремонте из MCP сервера.
Данные возвращаются в виде готовой Markdown таблицы без обработки LLM.
'''

import json

from loguru import logger

from agent.graph.state import AgentState, AgentResult
from agent.tools.mcp_client import get_mcp_client
from agent.config import GraphNodes, AgentRoles


async def repair_days_node(state: AgentState) -> AgentState:
    '''
    Получить статистику дней в ремонте в виде готовой Markdown таблицы.

    Args:
        state: Текущее состояние агента

    Returns:
        Обновленное состояние с таблицей статистики дней в ремонте
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

        # Extract formatted table directly from MCP response
        # MCP server already returns a formatted Markdown table in 'result' field
        # No LLM processing needed - just use the table as-is
        analysis = warranty_days_data.get(
            'result',
            json.dumps(warranty_days_data, ensure_ascii=False, indent=2)
        )

        logger.info('Данные дней в ремонте получены (без LLM)')

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
