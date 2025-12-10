'''
Дилерские insights узел для графа гарантийного агента.

Этот узел анализирует полную историю ремонтов и идентифицирует паттерны.
'''

import json

from loguru import logger

from agent.graph.state import AgentState, AgentResult
from agent.llm.gigachat_setup import get_dealer_insights_llm
from agent.llm.prompts import get_dealer_insights_prompt
from agent.tools.mcp_client import get_mcp_client
from agent.config import GraphNodes, AgentRoles


async def dealer_insights_node(state: AgentState) -> AgentState:
    '''
    Анализировать полную историю ремонтов и идентифицировать паттерны.

    Args:
        state: Текущее состояние агента

    Returns:
        Обновленное состояние с результатом анализа дилерских insights
    '''
    logger.info('Узел дилерских insights запущен')

    try:
        # Check if VIN is available
        if not state.vin:
            error_msg = 'VIN требуется для анализа дилерских insights'
            logger.warning(error_msg)
            state.dealer_insights_result = AgentResult(
                agent_name=AgentRoles.DEALER_INSIGHTS['name'],
                success=False,
                error=error_msg,
            )
            state.mark_step_completed(GraphNodes.DEALER_INSIGHTS)
            return state

        # Get MCP client
        client = await get_mcp_client()

        # Fetch all relevant data
        logger.debug(f'Получение данных истории ремонтов для VIN: {state.vin}')

        warranty_history = await client.warranty_history(state.vin)
        maintenance_history = await client.maintenance_history(state.vin)
        repairs_history = await client.vehicle_repairs_history(state.vin)

        # Check for errors
        errors = []
        if 'error' in warranty_history:
            errors.append(f'warranty_history: {warranty_history["error"]}')
        if 'error' in maintenance_history:
            errors.append(
                f'vehicle_maintenance_history: {maintenance_history["error"]}'
            )
        if 'error' in repairs_history:
            errors.append(
                f'vehicle_repairs_history: {repairs_history["error"]}'
            )

        if errors:
            error_msg = f'MCP errors: {"; ".join(errors)}'
            logger.error(error_msg)
            state.dealer_insights_result = AgentResult(
                agent_name=AgentRoles.DEALER_INSIGHTS['name'],
                success=False,
                error=error_msg,
                data={
                    'warranty_history': warranty_history,
                    'maintenance_history': maintenance_history,
                    'repairs_history': repairs_history,
                },
            )
            state.mark_step_completed(GraphNodes.DEALER_INSIGHTS)
            return state

        # Get LLM and prompt
        llm = get_dealer_insights_llm()
        prompt = get_dealer_insights_prompt()

        # Format data for LLM using text formatters
        # Extract 'result' field which contains formatted text
        warranty_formatted = warranty_history.get(
            'result',
            json.dumps(warranty_history, ensure_ascii=False, indent=2)
        )
        maintenance_formatted = maintenance_history.get(
            'result',
            json.dumps(maintenance_history, ensure_ascii=False, indent=2)
        )
        repairs_formatted = repairs_history.get(
            'result',
            json.dumps(repairs_history, ensure_ascii=False, indent=2)
        )

        # Format prompt
        messages = prompt.format_messages(
            query=state.query,
            vin=state.vin,
            warranty_history=warranty_formatted,
            maintenance_history=maintenance_formatted,
            repairs_history=repairs_formatted,
        )

        # Invoke LLM
        logger.debug('Вызов дилерских insights LLM')
        response = await llm.ainvoke(messages)
        analysis = response.content

        logger.info('Анализ дилерских insights завершен')

        # Create result
        state.dealer_insights_result = AgentResult(
            agent_name=AgentRoles.DEALER_INSIGHTS['name'],
            success=True,
            data={
                'analysis': analysis,
                'warranty_history': warranty_history,
                'maintenance_history': maintenance_history,
                'repairs_history': repairs_history,
                'vin': state.vin,
            },
        )

        # Mark step completed
        state.mark_step_completed(GraphNodes.DEALER_INSIGHTS)

        return state

    except Exception as e:
        error_msg = f'Ошибка дилерских insights: {str(e)}'
        logger.error(error_msg)
        state.add_error(error_msg)

        state.dealer_insights_result = AgentResult(
            agent_name=AgentRoles.DEALER_INSIGHTS['name'],
            success=False,
            error=error_msg,
        )

        state.mark_step_completed(GraphNodes.DEALER_INSIGHTS)
        return state
