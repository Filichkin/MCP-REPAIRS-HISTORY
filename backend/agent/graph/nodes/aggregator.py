'''
Агрегатор результатов для графа гарантийного агента.

Этот узел агрегирует результаты от всех агентов и готовит окончательный вывод.
Примечание: Большинство агрегации теперь обрабатывается узлом report_summary.
Этот узел служит как окончательная проверка и валидатор.
'''

from datetime import datetime

from loguru import logger

from backend.agent.graph.state import AgentState
from backend.config import GraphNodes


async def aggregator_node(state: AgentState) -> AgentState:
    '''
    Агрегировать и валидировать все результаты агентов.

    Этот узел:
    1. Проверяет, что требуемые агенты были выполнены
    2. Гарантирует, что final_response установлен
    3. Выполняет окончательную очистку состояния
    4. Устанавливает end_time, если не установлен

    Args:
        state: Текущее состояние агента

    Returns:
        Окончательное проверенное состояние
    '''
    logger.info('Узел агрегации результатов запущен')

    try:
        # Set end time if not set
        if state.end_time is None:
            state.end_time = datetime.now()

        # Validate final response exists
        if not state.final_response:
            logger.warning('Нет окончательного ответа, создание summary')
            state.final_response = _create_summary_response(state)

        # Add final metadata
        state.metadata.update({
            'total_steps': len(state.steps_completed),
            'completed_steps': state.steps_completed,
            'total_errors': len(state.errors),
            'final_execution_time': state.get_execution_time(),
        })

        # Mark step completed
        state.mark_step_completed(GraphNodes.AGGREGATOR)

        logger.info(
            f'Агрегация завершена. '
            f'Шаги: {len(state.steps_completed)}, '
            f'Ошибки: {len(state.errors)}, '
            f'Время: {state.get_execution_time():.2f}s'
        )

        return state

    except Exception as e:
        error_msg = f'Ошибка агрегации: {str(e)}'
        logger.error(error_msg)
        state.add_error(error_msg)

        # Ensure we have some response
        if not state.final_response:
            state.final_response = (
                f'Извините, произошла ошибка при обработке запроса: '
                f'{error_msg}'
            )

        state.mark_step_completed(GraphNodes.AGGREGATOR)
        return state


def _create_summary_response(state: AgentState) -> str:
    '''
    Создать summary ответ, когда final_response отсутствует.

    Args:
        state: Текущее состояние агента

    Returns:
        Summary ответ текст
    '''
    lines = [
        '# Результаты анализа',
        '',
        f'Запрос: {state.query}',
        '',
    ]

    # Check which agents were supposed to run
    if state.classification:
        agents_planned = []
        if state.classification.needs_repair_days:
            agents_planned.append('Анализ дней простоя')
        if state.classification.needs_compliance:
            agents_planned.append('Анализ гарантийной политики')
        if state.classification.needs_dealer_insights:
            agents_planned.append('Анализ истории ремонтов')

        if agents_planned:
            lines.append('Запланированные анализы:')
            for agent in agents_planned:
                lines.append(f'- {agent}')
            lines.append('')

    # Add results from each agent
    results = state.get_all_results()
    if results:
        lines.append('## Результаты:')
        lines.append('')
        for result in results:
            status = '✓' if result.success else '✗'
            lines.append(f'{status} **{result.agent_name}**')

            if result.success and 'analysis' in result.data:
                # Add first paragraph of analysis
                analysis = result.data['analysis']
                first_para = analysis.split('\n\n')[0]
                lines.append(f'  {first_para[:200]}...')
            elif not result.success:
                lines.append(f'  Ошибка: {result.error}')

            lines.append('')

    # Add errors if any
    if state.errors:
        lines.append('## Возникшие ошибки:')
        for error in state.errors:
            lines.append(f'- {error}')
        lines.append('')

    return '\n'.join(lines)
