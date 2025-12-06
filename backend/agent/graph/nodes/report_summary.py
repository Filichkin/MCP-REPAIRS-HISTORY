'''
Отчётный узел для графа гарантийного агента.

Этот узел генерирует окончательные отчёты
и сводки на основе всех результатов агентов.
'''

from datetime import datetime
from typing import Any

from loguru import logger

from backend.agent.graph.state import AgentState
from backend.agent.llm.gigachat_setup import get_report_summary_llm
from backend.agent.llm.prompts import get_report_summary_prompt
from backend.config import GraphNodes


async def report_summary_node(state: AgentState) -> AgentState:
    '''
    Генерирует окончательные отчёты и сводки
    на основе всех результатов агентов.

    Args:
        state: Текущее состояние агента с всеми результатами агентов

    Returns:
        Обновленное состояние с окончательным ответом
    '''
    logger.info('Узел отчёт и сводка запущен')

    try:
        # Get LLM and prompt
        llm = get_report_summary_llm()
        prompt = get_report_summary_prompt()

        # Prepare agent results
        repair_days_analysis = _get_analysis_text(state.repair_days_result)
        compliance_analysis = _get_analysis_text(state.compliance_result)
        dealer_insights_analysis = _get_analysis_text(
            state.dealer_insights_result
        )

        # Format prompt
        messages = prompt.format_messages(
            query=state.query,
            vin=state.vin or 'Не указан',
            repair_days_analysis=repair_days_analysis,
            compliance_analysis=compliance_analysis,
            dealer_insights_analysis=dealer_insights_analysis,
        )

        # Invoke LLM
        logger.debug('Вызов отчёт и сводка LLM')
        response = await llm.ainvoke(messages)
        final_report = response.content

        logger.info('Генерация отчёта завершена')

        # Update state
        state.final_response = final_report
        state.end_time = datetime.now()

        # Add metadata
        state.metadata.update({
            'agents_used': [
                result.agent_name
                for result in state.get_all_results()
                if result.success
            ],
            'execution_time_seconds': state.get_execution_time(),
            'has_errors': state.has_errors(),
        })

        # Mark step completed
        state.mark_step_completed(GraphNodes.REPORT_SUMMARY)

        return state

    except Exception as e:
        error_msg = f'Report & Summary error: {str(e)}'
        logger.error(error_msg)
        state.add_error(error_msg)

        # Create fallback response
        state.final_response = _create_fallback_response(state)
        state.end_time = datetime.now()

        state.mark_step_completed(GraphNodes.REPORT_SUMMARY)
        return state


def _get_analysis_text(result: Any) -> str:
    '''
    Извлечь текст анализа из результата агента.

    Args:
        result: Agent result object

    Returns:
        Analysis text or default message
    '''
    if result is None:
        return 'Анализ не проводился'

    if not result.success:
        return f'Ошибка: {result.error or "Неизвестная ошибка"}'

    if 'analysis' in result.data:
        return result.data['analysis']

    return 'Результат получен, но анализ недоступен'


def _create_fallback_response(state: AgentState) -> str:
    '''
    Создать fallback ответ, когда генерация отчёта не удалась.

    Args:
        state: Текущее состояние агента

    Returns:
        Fallback ответ текст
    '''
    lines = [
        '# ОТЧЁТ ПО ЗАПРОСУ',
        '',
        f'**Запрос:** {state.query}',
        f'**VIN:** {state.vin or "Не указан"}',
        f'**Дата запроса:** {state.start_time.strftime("%d.%m.%Y %H:%M")}',
        '',
        '## Результаты анализа',
        '',
    ]

    # Add results from each agent
    for result in state.get_all_results():
        lines.append(f'### {result.agent_name}')
        if result.success:
            lines.append('Статус: Выполнено успешно')
            if 'analysis' in result.data:
                lines.append('')
                lines.append(result.data['analysis'])
        else:
            lines.append(f'Статус: Ошибка - {result.error}')
        lines.append('')

    # Add errors if any
    if state.has_errors():
        lines.append('## Ошибки')
        for error in state.errors:
            lines.append(f'- {error}')
        lines.append('')

    lines.append('---')
    lines.append('*Отчёт сгенерирован автоматически*')

    return '\n'.join(lines)
