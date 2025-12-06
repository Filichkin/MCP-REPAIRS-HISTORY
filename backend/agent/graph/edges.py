'''
Логика маршрутизации ребер для графа гарантийного агента.

Этот модуль определяет условную маршрутизацию между узлами на основе состояния.
'''

from typing import Literal
from langgraph.graph import END
from loguru import logger

from backend.agent.graph.state import AgentState
from backend.config import GraphNodes


def route_after_classifier(
    state: AgentState,
) -> Literal[
    'repair_days_tracker',
    'warranty_compliance',
    'dealer_insights',
    'report_summary',
    'multi_agent',
]:
    '''
    Маршрутизация после классификатора на основе результатов классификации.

    Определяет приоритетный агент для выполнения или режим multi-agent.

    Args:
        state: Текущее состояние агента с результатом классификации

    Returns:
        Название узла агента для выполнения
    '''
    if not state.classification:
        logger.warning('Классификация не найдена, маршрутизация к отчёту')
        return GraphNodes.REPORT_SUMMARY

    # Count how many agents are needed
    agents_needed = sum([
        state.classification.needs_repair_days,
        state.classification.needs_compliance,
        state.classification.needs_dealer_insights,
    ])

    # If no agents selected, go directly to report
    if agents_needed == 0:
        logger.info('Агенты не выбраны, маршрутизация к отчёту')
        return GraphNodes.REPORT_SUMMARY

    # If only one agent needed, route directly to it
    if agents_needed == 1:
        if state.classification.needs_repair_days:
            logger.info('Маршрутизация к узлу дней в ремонте')
            return GraphNodes.REPAIR_DAYS
        elif state.classification.needs_compliance:
            logger.info('Маршрутизация к узлу соответствия')
            return GraphNodes.COMPLIANCE
        elif state.classification.needs_dealer_insights:
            logger.info('Маршрутизация к узлу дилерских insights')
            return GraphNodes.DEALER_INSIGHTS

    # If multiple agents needed, use sequential execution
    # Priority: repair_days -> compliance -> dealer_insights
    logger.info(
        f'Требуется {agents_needed} агентов, последовательное выполнение'
        )

    if state.classification.needs_repair_days:
        return GraphNodes.REPAIR_DAYS
    elif state.classification.needs_compliance:
        return GraphNodes.COMPLIANCE
    else:
        return GraphNodes.DEALER_INSIGHTS


def should_continue_to_report(
    state: AgentState,
) -> Literal[
    'repair_days_tracker',
    'warranty_compliance',
    'dealer_insights',
    'report_summary',
]:
    '''
    Определить следующий шаг после выполнения агента.

    Если нужны другие агенты - маршрутизирует к ним.
    Если все агенты завершены - идет к генерации отчёта.

    Args:
        state: Текущее состояние агента

    Returns:
        Название следующего узла
    '''
    if not state.classification:
        logger.warning('Классификация не найдена, переход к отчёту')
        return GraphNodes.REPORT_SUMMARY

    # Check which agents still need to run
    needs_repair_days = (
        state.classification.needs_repair_days
        and GraphNodes.REPAIR_DAYS not in state.steps_completed
    )
    needs_compliance = (
        state.classification.needs_compliance
        and GraphNodes.COMPLIANCE not in state.steps_completed
    )
    needs_dealer_insights = (
        state.classification.needs_dealer_insights
        and GraphNodes.DEALER_INSIGHTS not in state.steps_completed
    )

    # Route to next required agent (priority order)
    if needs_repair_days:
        logger.info('Переход к агенту дней в ремонте')
        return GraphNodes.REPAIR_DAYS
    elif needs_compliance:
        logger.info('Переход к агенту соответствия')
        return GraphNodes.COMPLIANCE
    elif needs_dealer_insights:
        logger.info('Переход к агенту дилерских insights')
        return GraphNodes.DEALER_INSIGHTS

    # All agents completed, go to report
    logger.info('Все необходимые агенты завершены, переход к генерации отчёта')
    return GraphNodes.REPORT_SUMMARY


def route_to_end(state: AgentState):
    '''
    Финальная маршрутизация к END после агрегатора.

    Args:
        state: Текущее состояние агента

    Returns:
        END marker
    '''
    logger.info('Routing to END')
    return END
