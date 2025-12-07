"""Pydantic модели для структурированных ответов MCP tools."""
from typing import List, Optional, Any

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Модели для warranty_days
# ============================================================================


class RepairYear(BaseModel):
    """Информация о годе владения и днях в ремонте."""

    year_number: int = Field(description='Номер года владения')
    is_current_year: bool = Field(description='Является ли год текущим')
    days_in_repair: int = Field(description='Количество дней в ремонте')


class WarrantyDaysStructured(BaseModel):
    """Структурированный ответ для warranty_days tool."""

    vin: str = Field(description='VIN номер автомобиля')
    total_years: int = Field(description='Общее количество лет владения')
    repair_years: List[RepairYear] = Field(
        description='Список годов владения с днями в ремонте'
    )
    current_year_days: Optional[int] = Field(
        None, description='Дней в ремонте в текущем году'
    )
    total_days_in_repair: int = Field(
        description='Общее количество дней в ремонте за все годы'
    )


# ============================================================================
# Модели для warranty_history
# ============================================================================


class Dealer(BaseModel):
    """Информация о дилере."""

    name: str = Field(description='Название дилера')
    code: Optional[str] = Field(None, description='Код дилера')
    city: str = Field(description='Город')

    @field_validator('code', mode='before')
    @classmethod
    def convert_code_to_string(cls, value: Any) -> Optional[str]:
        """Конвертирует code из int в str при необходимости."""
        if value is None:
            return None
        return str(value)


class ReplacedPart(BaseModel):
    """Информация о замененной детали."""

    part_number: str = Field(description='Каталожный номер детали')
    description: str = Field(description='Описание детали')


class Operation(BaseModel):
    """Информация о выполненной операции."""

    code: str = Field(description='Код операции')
    description: str = Field(description='Описание выполненной работы')


class FaultPart(BaseModel):
    """Информация о детали-виновнике."""

    part_number: str = Field(description='Каталожный номер детали-виновника')
    description: str = Field(description='Описание детали-виновника')


class WarrantyRecord(BaseModel):
    """Запись о гарантийном обращении."""

    serial: str = Field(description='Номер гарантийного требования')
    date: str = Field(description='Дата открытия требования')
    odometer: int = Field(description='Пробег в километрах')
    dealer: Dealer = Field(description='Информация о дилере')
    fault_part: FaultPart = Field(description='Деталь-виновник')
    replaced_parts: List[ReplacedPart] = Field(
        default_factory=list,
        description='Список замененных деталей'
    )
    operations: List[Operation] = Field(
        default_factory=list,
        description='Список выполненных работ'
    )


class WarrantyHistoryStructured(BaseModel):
    """Структурированный ответ для warranty_history tool."""

    vin: str = Field(description='VIN номер автомобиля')
    records: List[WarrantyRecord] = Field(
        description='Список гарантийных обращений'
    )
    total_records: int = Field(
        description='Общее количество гарантийных обращений'
    )
    total_parts_replaced: int = Field(
        description='Общее количество замененных деталей'
    )
    total_operations: int = Field(
        description='Общее количество выполненных работ'
    )


# ============================================================================
# Модели для maintenance_history
# ============================================================================


class MaintenanceRecord(BaseModel):
    """Запись о техническом обслуживании."""

    vin: str = Field(description='VIN номер автомобиля')
    maintenance_type: str = Field(description='Тип технического обслуживания')
    date: str = Field(description='Дата проведения ТО')
    odometer: int = Field(description='Пробег в километрах')
    dealer: Dealer = Field(description='Информация о дилере')


class MaintenanceHistoryStructured(BaseModel):
    """Структурированный ответ для maintenance_history tool."""

    vin: str = Field(description='VIN номер автомобиля')
    records: List[MaintenanceRecord] = Field(
        description='Список записей о техническом обслуживании'
    )
    total_records: int = Field(
        description='Общее количество записей о ТО'
    )
    maintenance_types: List[str] = Field(
        description='Уникальные типы проведенного ТО'
    )


# ============================================================================
# Модели для vehicle_repairs_history
# ============================================================================


class VehicleRepairRecord(BaseModel):
    """Запись о ремонте из дилерской сети (DNM)."""

    dealer_name: str = Field(description='Название дилера')
    date: str = Field(description='Дата закрытия ремонтного заказа')
    odometer: int = Field(description='Пробег в километрах')
    repair_type: str = Field(description='Тип ремонта')
    visit_reason: str = Field(description='Причина визита')
    recommendations: str = Field(description='Рекомендации дилера')


class VehicleRepairsHistoryStructured(BaseModel):
    """Структурированный ответ для vehicle_repairs_history tool."""

    vin: str = Field(description='VIN номер автомобиля')
    records: List[VehicleRepairRecord] = Field(
        description='Список записей о ремонтах DNM'
    )
    total_records: int = Field(
        description='Общее количество записей о ремонтах'
    )
    repair_types: List[str] = Field(
        description='Уникальные типы ремонтов'
    )


# ============================================================================
# Модели для compliance_rag
# ============================================================================


class RAGDocument(BaseModel):
    """Документ из базы знаний."""

    content: str = Field(description='Содержимое документа')
    metadata: dict = Field(
        default_factory=dict,
        description='Метаданные документа'
    )
    relevance_score: Optional[float] = Field(
        None,
        description='Оценка релевантности (если доступна)'
    )


class ComplianceRAGStructured(BaseModel):
    """Структурированный ответ для compliance_rag tool."""

    query: str = Field(description='Исходный запрос пользователя')
    documents: List[RAGDocument] = Field(
        description='Список релевантных документов'
    )
    total_documents: int = Field(
        description='Общее количество найденных документов'
    )
    knowledge_base_version: str = Field(
        description='Версия базы знаний'
    )
