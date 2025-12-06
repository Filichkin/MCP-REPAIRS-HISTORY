'''
LangGraph StateGraph construction для системы гарантийного агента.

Этот модуль строит полный граф многоагентного workflow.
'''

from typing import Any
from langgraph.graph import StateGraph, END
from loguru import logger

from backend.agent.graph.state import AgentState
from backend.agent.graph.nodes.classifier import classifier_node
from backend.agent.graph.nodes.repair_days import repair_days_node
from backend.agent.graph.nodes.compliance import compliance_node
from backend.agent.graph.nodes.dealer_insights import dealer_insights_node
from backend.agent.graph.nodes.report_summary import report_summary_node
from backend.agent.graph.nodes.aggregator import aggregator_node
from backend.agent.graph.edges import (
    route_after_classifier,
    should_continue_to_report,
    route_to_end,
)
from backend.config import GraphNodes


def create_warranty_graph() -> StateGraph:
    '''
    Создать и скомпилировать граф StateGraph для гарантийного агента.

    Структура графа:

    START
      ↓
    Classifier (анализирует запрос, определяет необходимые агенты)
      ↓
    [Условная маршрутизация на основе необходимости]
      ↓
    Agent 1 (например, дни в ремонте)
      ↓
    [Проверить, нужны ли ещё агенты]
      ↓
    Agent 2 (например, соответствие) - если нужно
      ↓
    [Проверить, нужны ли ещё агенты]
      ↓
    Agent 3 (например, дилерские insights) - если нужно
      ↓
    [Все необходимые агенты завершены]
      ↓
    Report & Summary (агрегирует результаты, генерирует окончательный отчёт)
      ↓
    Aggregator (валидирует и завершает ответ)
      ↓
    END

    Примечание: Агенты выполняются последовательно
    на основе результатов классификации.
    Приоритетный порядок: дни в ремонте → соответствие → дилерские insights

    Returns:
        Скомпилированный StateGraph готов для выполнения
    '''
    logger.info('Строим граф агента')

    # Initialize graph with AgentState
    workflow = StateGraph(AgentState)

    # Добавляем узлы
    workflow.add_node(GraphNodes.CLASSIFIER, classifier_node)
    workflow.add_node(GraphNodes.REPAIR_DAYS, repair_days_node)
    workflow.add_node(GraphNodes.COMPLIANCE, compliance_node)
    workflow.add_node(GraphNodes.DEALER_INSIGHTS, dealer_insights_node)
    workflow.add_node(GraphNodes.REPORT_SUMMARY, report_summary_node)
    workflow.add_node(GraphNodes.AGGREGATOR, aggregator_node)

    # Устанавливаем точку входа
    workflow.set_entry_point(GraphNodes.CLASSIFIER)

    # Добавляем условные ребра от классификатора к первому агенту или отчёту
    workflow.add_conditional_edges(
        GraphNodes.CLASSIFIER,
        route_after_classifier,
        {
            GraphNodes.REPAIR_DAYS: GraphNodes.REPAIR_DAYS,
            GraphNodes.COMPLIANCE: GraphNodes.COMPLIANCE,
            GraphNodes.DEALER_INSIGHTS: GraphNodes.DEALER_INSIGHTS,
            GraphNodes.REPORT_SUMMARY: GraphNodes.REPORT_SUMMARY,
        },
    )

    # Добавляем условные ребра от узлов агентов к следующему агенту или отчёту
    # Агенты выполняются последовательно на основе приоритета
    workflow.add_conditional_edges(
        GraphNodes.REPAIR_DAYS,
        should_continue_to_report,
        {
            GraphNodes.REPAIR_DAYS: GraphNodes.REPAIR_DAYS,
            GraphNodes.COMPLIANCE: GraphNodes.COMPLIANCE,
            GraphNodes.DEALER_INSIGHTS: GraphNodes.DEALER_INSIGHTS,
            GraphNodes.REPORT_SUMMARY: GraphNodes.REPORT_SUMMARY,
        },
    )

    workflow.add_conditional_edges(
        GraphNodes.COMPLIANCE,
        should_continue_to_report,
        {
            GraphNodes.REPAIR_DAYS: GraphNodes.REPAIR_DAYS,
            GraphNodes.COMPLIANCE: GraphNodes.COMPLIANCE,
            GraphNodes.DEALER_INSIGHTS: GraphNodes.DEALER_INSIGHTS,
            GraphNodes.REPORT_SUMMARY: GraphNodes.REPORT_SUMMARY,
        },
    )

    workflow.add_conditional_edges(
        GraphNodes.DEALER_INSIGHTS,
        should_continue_to_report,
        {
            GraphNodes.REPAIR_DAYS: GraphNodes.REPAIR_DAYS,
            GraphNodes.COMPLIANCE: GraphNodes.COMPLIANCE,
            GraphNodes.DEALER_INSIGHTS: GraphNodes.DEALER_INSIGHTS,
            GraphNodes.REPORT_SUMMARY: GraphNodes.REPORT_SUMMARY,
        },
    )

    # Добавляем ребро от отчёта к агрегатору
    workflow.add_edge(GraphNodes.REPORT_SUMMARY, GraphNodes.AGGREGATOR)

    # Добавляем условные ребра от агрегатора к END
    workflow.add_conditional_edges(
        GraphNodes.AGGREGATOR,
        route_to_end,
        {
            END: END,
        },
    )

    # Скомпилируем граф
    compiled_graph = workflow.compile()

    logger.info('Граф агента скомпилирован успешно')

    return compiled_graph


# Глобальный экземпляр графа
_graph_instance: Any = None


def get_graph() -> Any:
    '''
    Get or create global graph instance.

    Returns:
        Compiled graph instance
    '''
    global _graph_instance

    if _graph_instance is None:
        _graph_instance = create_warranty_graph()

    return _graph_instance


async def execute_query(
    query: str,
    vin: str | None = None,
    user_context: dict[str, Any] | None = None,
) -> AgentState:
    '''
    Выполнить запрос через граф гарантийного агента.

    Args:
        query: Запрос пользователя
        vin: Optional VIN number
        user_context: Дополнительный контекст

    Returns:
        Конечное состояние агента с результатами
    '''
    logger.info(f'Выполняем запрос: {query[:100]}...')

    # Создаем начальное состояние
    initial_state = AgentState(
        query=query,
        vin=vin,
        user_context=user_context or {},
    )

    # Получаем граф
    graph = get_graph()

    # Выполняем граф
    try:
        final_state_dict = await graph.ainvoke(initial_state.model_dump())
        logger.info('Выполнение запроса завершено успешно')

        # Преобразуем dict обратно в AgentState
        final_state = AgentState(**final_state_dict)
        return final_state

    except Exception as e:
        logger.error(f'Ошибка выполнения графа: {e}', exc_info=True)
        # Update state with error
        initial_state.add_error(f'Graph execution failed: {str(e)}')
        initial_state.final_response = (
            f'Извините, произошла ошибка при обработке запроса: {str(e)}'
        )
        return initial_state


async def execute_query_stream(
    query: str,
    vin: str | None = None,
    user_context: dict[str, Any] | None = None,
):
    '''
    Выполнить запрос через граф с потоковыми обновлениями.

    Args:
        query: Запрос пользователя
        vin: Optional VIN number
        user_context: Дополнительный контекст

    Yields:
        Обновления состояния как граф выполняет
    '''
    logger.info(f'Выполняем запрос (потоковое): {query[:100]}...')

    # Создаем начальное состояние
    initial_state = AgentState(
        query=query,
        vin=vin,
        user_context=user_context or {},
    )

    # Получаем граф
    graph = get_graph()

    # Выполняем граф с потоковыми обновлениями
    try:
        async for update in graph.astream(initial_state):
            yield update

        logger.info('Выполнение запроса (потоковое) завершено')

    except Exception as e:
        logger.error(f'Ошибка выполнения графа (потоковое): {e}')
        yield {
            'error': str(e),
            'message': f'Про    изошла ошибка при обработке запроса: {str(e)}',
        }
