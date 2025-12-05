'''
Гарантийный Compliance узел для графа гарантийного агента.

Этот узел интерпретирует гарантийную политику и объясняет права потребителя.
'''

import json

from loguru import logger

from backend.agent.graph.state import AgentState, AgentResult
from backend.agent.llm.gigachat_setup import get_compliance_llm
from backend.agent.llm.prompts import get_compliance_prompt
from backend.agent.tools.mcp_client import get_mcp_client
from backend.config import GraphNodes, AgentRoles


async def compliance_node(state: AgentState) -> AgentState:
    '''
    Интерпретировать стандарты клиентской службы.

    Args:
        state: Текущее состояние агента
    Returns:
        Обновленное состояние с результатом анализа соответствия
    '''
    logger.info('Узел соответствия запущен')

    try:
        # Build search query for compliance RAG
        # Use original query or build specific query
        search_query = _build_compliance_query(state)

        logger.debug(f'Запрос соответствия: {search_query}')

        # Get MCP client and fetch compliance data
        client = await get_mcp_client()
        compliance_data = await client.compliance_rag(search_query)

        # Check for errors in data
        if 'error' in compliance_data:
            error_msg = f'Ошибка MCP: {compliance_data["error"]}'
            logger.error(error_msg)
            state.compliance_result = AgentResult(
                agent_name=AgentRoles.COMPLIANCE['name'],
                success=False,
                error=error_msg,
                data=compliance_data,
            )
            state.mark_step_completed(GraphNodes.COMPLIANCE)
            return state

        # Get LLM and prompt
        llm = get_compliance_llm()
        prompt = get_compliance_prompt()

        # Format data for LLM
        data_formatted = json.dumps(
            compliance_data, ensure_ascii=False, indent=2
        )

        # Format prompt
        messages = prompt.format_messages(
            query=state.query, compliance_data=data_formatted
        )

        # Invoke LLM
        logger.debug('Вызов соответствия LLM')
        response = await llm.ainvoke(messages)
        analysis = response.content

        logger.info('Анализ соответствия завершен')

        # Create result
        state.compliance_result = AgentResult(
            agent_name=AgentRoles.COMPLIANCE['name'],
            success=True,
            data={
                'analysis': analysis,
                'raw_data': compliance_data,
                'search_query': search_query,
            },
        )

        # Mark step completed
        state.mark_step_completed(GraphNodes.COMPLIANCE)

        return state

    except Exception as e:
        error_msg = f'Ошибка соответствия: {str(e)}'
        logger.error(error_msg)
        state.add_error(error_msg)

        state.compliance_result = AgentResult(
            agent_name=AgentRoles.COMPLIANCE['name'],
            success=False,
            error=error_msg,
        )

        state.mark_step_completed(GraphNodes.COMPLIANCE)
        return state


def _build_compliance_query(state: AgentState) -> str:
    '''
    Создать запрос для соответствия RAG на основе состояния.

    Args:
        state: Текущее состояние агента

    Returns:
        Запрос соответствия строка
    '''
    # Use original query as base
    query = state.query

    # Add context if repair days analysis was done
    if state.repair_days_result and state.repair_days_result.success:
        data = state.repair_days_result.data
        if 'raw_data' in data:
            # Check if 30-day limit might be exceeded
            raw_data = data['raw_data']
            if isinstance(raw_data, dict):
                # Look for days counts
                for year, days in raw_data.items():
                    if isinstance(days, (int, float)) and days > 25:
                        query += (
                            ' 30 дней ремонте, как действовать '
                            'клиентской службе'
                            )
                        break

    return query
