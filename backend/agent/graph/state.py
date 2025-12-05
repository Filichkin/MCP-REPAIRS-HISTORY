'''
Состояние управления для графа гарантийного агента.

Этот модуль определяет схему состояния, используемую в LangGraph workflow.
'''

from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AgentClassification(BaseModel):
    '''Результат классификации от Query Classifier.'''

    needs_repair_days: bool = Field(
        default=False, description='Нужен ли агент дней в ремонте'
    )
    needs_compliance: bool = Field(
        default=False, description='Нужен ли агент соответствия'
    )
    needs_dealer_insights: bool = Field(
        default=False, description='Нужен ли агент дилерских insights'
    )
    vin: Optional[str] = Field(
        default=None, description='Извлеченный VIN, если присутствует'
    )
    reasoning: str = Field(
        default='', description='Обоснование для классификации'
    )


class AgentResult(BaseModel):
    '''Результат от отдельного агента.'''

    agent_name: str = Field(description='Название агента')
    success: bool = Field(description='Был ли выполнен успешно')
    data: dict[str, Any] = Field(
        default_factory=dict, description='Результат данных'
    )
    error: Optional[str] = Field(
        default=None, description='Сообщение об ошибке, если не выполнен'
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description='Время выполнения'
    )


class AgentState(BaseModel):
    '''
    Основной объект состояния, передаваемый через LangGraph workflow.

    Это состояние накапливает информацию, как запрос проходит через
    различные агенты и узлы в графе.
    '''

    # Input
    query: str = Field(description='Исходный запрос пользователя')
    vin: Optional[str] = Field(
        default=None,
        escription='Извлеченный VIN из запроса или предоставленный явно'
    )
    user_context: dict[str, Any] = Field(
        default_factory=dict,
        description='Дополнительный контекст, предоставленный пользователем',
    )

    # Classification
    classification: Optional[AgentClassification] = Field(
        default=None, description='Результат классификации запроса'
    )

    # Execution tracking
    current_step: str = Field(
        default='start', description='Текущий шаг выполнения'
    )
    steps_completed: list[str] = Field(
        default_factory=list, description='Список завершенных шагов'
    )

    # Agent results
    repair_days_result: Optional[AgentResult] = Field(
        default=None, description='Результат от агента дней в ремонте'
    )
    compliance_result: Optional[AgentResult] = Field(
        default=None, description='Результат от агента соответствия'
    )
    dealer_insights_result: Optional[AgentResult] = Field(
        default=None, description='Результат от агента дилерских insights'
    )

    # Aggregated response
    final_response: Optional[str] = Field(
        default=None, description='Окончательный агрегированный ответ'
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description='Дополнительные метаданные'
    )

    # Error tracking
    errors: list[str] = Field(
        default_factory=list,
        description='Список ошибок, возникших при выполнении'
    )

    # Execution metrics
    start_time: datetime = Field(
        default_factory=datetime.now,
        description='Время начала выполнения запроса',
    )
    end_time: Optional[datetime] = Field(
        default=None, description='Время окончания выполнения запроса'
    )

    class Config:
        '''Конфигурация Pydantic.'''

        arbitrary_types_allowed = True

    def add_error(self, error: str) -> None:
        '''Добавить ошибку в список ошибок.'''
        self.errors.append(error)

    def mark_step_completed(self, step: str) -> None:
        '''Отметить шаг как завершенный.'''
        if step not in self.steps_completed:
            self.steps_completed.append(step)
        self.current_step = step

    def get_all_results(self) -> list[AgentResult]:
        '''Получить все результаты агентов, которые были заполнены.'''
        results = []
        if self.repair_days_result:
            results.append(self.repair_days_result)
        if self.compliance_result:
            results.append(self.compliance_result)
        if self.dealer_insights_result:
            results.append(self.dealer_insights_result)
        return results

    def has_errors(self) -> bool:
        '''Проверить, есть ли ошибки.'''
        return len(self.errors) > 0

    def get_execution_time(self) -> Optional[float]:
        '''Получить общее время выполнения в секундах.'''
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def to_dict(self) -> dict[str, Any]:
        '''Преобразовать состояние в словарь.'''
        return self.model_dump()
