'''
Отчётный узел для графа гарантийного агента.

Этот узел генерирует окончательные отчёты
и сводки на основе всех результатов агентов.
'''

from datetime import datetime
from typing import Any

from loguru import logger

from agent.graph.state import AgentState
from agent.llm.gigachat_setup import get_report_summary_llm
from agent.llm.prompts import get_report_summary_prompt
from agent.config import GraphNodes


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

    # Проверяем, были ли выбраны какие-либо агенты
    if _no_agents_selected(state):
        logger.info('Агенты не были выбраны, возвращаем сообщение-подсказку')
        state.final_response = _create_no_agents_response(state)
        state.end_time = datetime.now()
        state.mark_step_completed(GraphNodes.REPORT_SUMMARY)
        return state

    try:
        # Get LLM and prompt
        llm = get_report_summary_llm()
        prompt = get_report_summary_prompt()

        # Prepare agent results - только для активированных агентов
        repair_days_analysis = _get_analysis_text(
            state.repair_days_result,
            was_requested=state.classification.needs_repair_days
            if state.classification else False
        )
        compliance_analysis = _get_analysis_text(
            state.compliance_result,
            was_requested=state.classification.needs_compliance
            if state.classification else False
        )
        dealer_insights_analysis = _get_analysis_text(
            state.dealer_insights_result,
            was_requested=state.classification.needs_dealer_insights
            if state.classification else False
        )

        # Собираем ТОЛЬКО непустые секции (без заголовков для пустых)
        agent_data_parts = []
        if repair_days_analysis:
            agent_data_parts.append(
                f'ДАННЫЕ О ДНЯХ В РЕМОНТЕ:\n{repair_days_analysis}'
            )
        if compliance_analysis:
            agent_data_parts.append(
                f'ГАРАНТИЙНАЯ ПОЛИТИКА:\n{compliance_analysis}'
            )
        if dealer_insights_analysis:
            agent_data_parts.append(
                f'ИСТОРИЯ РЕМОНТОВ:\n{dealer_insights_analysis}'
            )

        agent_data = '\n\n'.join(agent_data_parts) if agent_data_parts else (
            'Данные не найдены'
        )

        # Format prompt
        messages = prompt.format_messages(
            query=state.query,
            agent_data=agent_data,
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


def _no_agents_selected(state: AgentState) -> bool:
    '''
    Проверить, были ли выбраны какие-либо агенты классификатором.

    Args:
        state: Текущее состояние агента

    Returns:
        True если ни один агент не был выбран
    '''
    if not state.classification:
        return True

    return not any([
        state.classification.needs_repair_days,
        state.classification.needs_compliance,
        state.classification.needs_dealer_insights,
    ])


def _create_no_agents_response(state: AgentState) -> str:
    '''
    Создать ответ для случая, когда классификатор не выбрал агентов.

    Args:
        state: Текущее состояние агента

    Returns:
        Текст ответа с подсказками
    '''
    return (
        f'К сожалению, я не смог определить, какой тип анализа вам нужен '
        f'для запроса: "{state.query}".\n\n'
        f'Пожалуйста, уточните ваш запрос. Я могу помочь с:\n\n'
        f'**📊 Анализ дней в ремонте:**\n'
        f'- Сколько дней автомобиль был в ремонте?\n'
        f'- Есть ли превышение 30-дневного лимита?\n\n'
        f'**📋 Гарантийная политика и контакты:**\n'
        f'- Какие контакты клиентской службы?\n'
        f'- Какая процедура гарантийного обращения?\n'
        f'- Какие документы нужны?\n\n'
        f'**🔧 История ремонтов:**\n'
        f'- Покажи историю обслуживания автомобиля\n'
        f'- Какие ремонты были у дилера?\n'
    )


def _get_analysis_text(result: Any, was_requested: bool = True) -> str:
    '''
    Извлечь текст анализа из результата агента.

    Args:
        result: Agent result object
        was_requested: Был ли агент запрошен классификатором

    Returns:
        Analysis text or default message
    '''
    # Если агент не был запрошен - не показываем ничего
    if not was_requested:
        return ''

    if result is None:
        return 'Данные не найдены'

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
