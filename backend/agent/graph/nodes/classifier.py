'''
Запросный классификатор узел для графа гарантийного агента.

Этот узел анализирует пользовательские запросы и определяет,
какие агенты должны быть вызваны.
'''

import json
import re

from loguru import logger

from backend.agent.graph.state import AgentState, AgentClassification
from backend.agent.llm.gigachat_setup import get_classifier_llm
from backend.agent.llm.prompts import get_classifier_prompt
from backend.config import GraphNodes


async def classifier_node(state: AgentState) -> AgentState:
    '''
    Классифицировать пользовательский запрос
    и определить, какие агенты должны быть вызваны.

    Args:
        state: Текущее состояние агента

    Returns:
        Обновленное состояние с результатом классификации
    '''
    logger.info('Узел классификации запущен')

    try:
        # Get LLM and prompt
        llm = get_classifier_llm()
        prompt = get_classifier_prompt()

        # Prepare context
        context = json.dumps(state.user_context, ensure_ascii=False)

        # Format prompt
        messages = prompt.format_messages(
            query=state.query,
            context=context if context != '{}' else 'Нет',
        )

        # Invoke LLM
        logger.debug(
            f'Вызов классификатора LLM для запроса: '
            f'{state.query[:100]}'
            )
        response = await llm.ainvoke(messages)
        response_text = response.content

        logger.debug(f'Классификатор ответ: {response_text}')

        # Parse JSON response
        classification_data = _parse_classification_response(response_text)

        # Create classification object
        classification = AgentClassification(**classification_data)

        # Update state
        state.classification = classification

        # If VIN was extracted, update state VIN
        if classification.vin and not state.vin:
            state.vin = classification.vin
            logger.info(f'VIN извлечен из запроса: {classification.vin}')

        # Mark step completed
        state.mark_step_completed(GraphNodes.CLASSIFIER)

        logger.info(
            f'Классификация завершена: '
            f'repair_days={classification.needs_repair_days}, '
            f'compliance={classification.needs_compliance}, '
            f'dealer_insights={classification.needs_dealer_insights}'
        )

        return state

    except Exception as e:
        error_msg = f'Ошибка классификации: {str(e)}'
        logger.error(error_msg)
        state.add_error(error_msg)

        # Fallback: create default classification
        state.classification = AgentClassification(
            needs_repair_days=False,
            needs_compliance=False,
            needs_dealer_insights=False,
            reasoning=(
                'Ошибка классификации, используются значения '
                'по умолчанию'
                ),
        )

        state.mark_step_completed(GraphNodes.CLASSIFIER)
        return state


def _parse_classification_response(response: str) -> dict:
    '''
    Парсинг ответа классификатора LLM в структурированные данные.

    Args:
        response: Raw LLM ответ

    Returns:
        Словарь с данными классификации
    '''
    # Try to extract JSON from response
    try:
        # Look for JSON block
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
        else:
            # Try parsing entire response as JSON
            data = json.loads(response)

        # Validate required fields
        return {
            'needs_repair_days': bool(data.get('needs_repair_days', False)),
            'needs_compliance': bool(data.get('needs_compliance', False)),
            'needs_dealer_insights': bool(
                data.get('needs_dealer_insights', False)
            ),
            'vin': data.get('vin') or None,
            'reasoning': str(data.get('reasoning', '')),
        }

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f'Не удалось парсить JSON классификации: {e}')

        # Fallback: try to infer from text
        response_lower = response.lower()

        return {
            'needs_repair_days': any(
                keyword in response_lower
                for keyword in ['дней', 'простой', 'лимит', '30']
            ),
            'needs_compliance': any(
                keyword in response_lower
                for keyword in ['закон', 'право', 'гарантия', 'политика']
            ),
            'needs_dealer_insights': any(
                keyword in response_lower
                for keyword in ['история', 'ремонт', 'проблем', 'паттерн']
            ),
            'vin': _extract_vin_from_text(response),
            'reasoning': 'Классификация на основе ключевых слов',
        }


def _extract_vin_from_text(text: str) -> str | None:
    '''
    Попытаться извлечь VIN из текста используя regex.

    Args:
        text: Текст для поиска

    Returns:
        VIN строка или None
    '''
    # VIN pattern: 17 alphanumeric characters (excluding I, O, Q)
    vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
    match = re.search(vin_pattern, text.upper())
    if match:
        return match.group(0)
    return None
