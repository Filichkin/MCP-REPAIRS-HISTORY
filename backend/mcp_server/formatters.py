"""Функции форматирования текстовых описаний для MCP tools."""

from typing import List
from mcp_server.models import (
    RepairYear,
    WarrantyRecord,
    MaintenanceRecord,
    VehicleRepairRecord,
    RAGDocument,
)


def format_warranty_days_text(
    vin: str,
    repair_years: List[RepairYear],
    total_days: int
) -> str:
    """
    Форматирует статистику дней в ремонте в виде Markdown таблицы.

    Args:
        vin: VIN номер автомобиля
        repair_years: Список годов владения с днями в ремонте
        total_days: Общее количество дней в ремонте

    Returns:
        Отформатированная таблица Markdown
    """
    if not repair_years:
        return f'Для VIN {vin}: записи не найдены'

    lines = ['## СТАТИСТИКА ДНЕЙ В РЕМОНТЕ']
    lines.append('')
    lines.append('| Год владения | Дней в ремонте |')
    lines.append('|--------------|----------------|')

    for year in repair_years:
        year_label = f'{year.year_number}-й год'
        if year.is_current_year:
            year_label += ' (текущий)'
        days_label = f'{year.days_in_repair} дней'
        lines.append(f'| {year_label:<20} | {days_label:<14} |')

    lines.append('')
    lines.append(f'**Итого за все годы: {total_days} дней**')

    return '\n'.join(lines)


def format_warranty_history_text(
    vin: str,
    records: List[WarrantyRecord],
    total_parts: int,
    total_operations: int
) -> str:
    """
    Форматирует текстовое описание истории гарантийных обращений.

    Args:
        vin: VIN номер автомобиля
        records: Список гарантийных обращений
        total_parts: Общее количество замененных деталей
        total_operations: Общее количество выполненных работ

    Returns:
        Отформатированный текст для отображения
    """
    if not records:
        return f'Для VIN {vin}: записи не найдены'

    lines = [f'История гарантийных обращений VIN {vin}']
    lines.append(f'Всего обращений: {len(records)}')
    lines.append(f'Всего заменено деталей: {total_parts}')
    lines.append(f'Всего выполнено работ: {total_operations}')
    lines.append('')

    for idx, record in enumerate(records, 1):
        lines.append(f'═══ Обращение {idx} ═══')
        lines.append(
            f'Гарантийное требование {record.serial} от {record.date}'
        )
        lines.append(f'Пробег: {record.odometer:,} км')
        lines.append(
            f'Дилер: {record.dealer.name} ({record.dealer.city})'
        )
        lines.append('')

        lines.append(
            f'Деталь-виновник: {record.fault_part.part_number}'
        )
        lines.append(f'Описание: {record.fault_part.description}')
        lines.append('')

        if record.replaced_parts:
            lines.append('Замененные детали:')
            for part in record.replaced_parts:
                lines.append(
                    f'  • {part.part_number}: {part.description}'
                )
            lines.append('')

        if record.operations:
            lines.append('Выполненные работы:')
            for op in record.operations:
                lines.append(f'  • {op.code}: {op.description}')
            lines.append('')

    return '\n'.join(lines)


def format_maintenance_history_text(
    vin: str,
    records: List[MaintenanceRecord]
) -> str:
    """
    Форматирует текстовое описание истории технического обслуживания.

    Args:
        vin: VIN номер автомобиля
        records: Список записей о ТО

    Returns:
        Отформатированный текст для отображения
    """
    if not records:
        return f'Для VIN {vin}: записи не найдены'

    lines = [f'История технического обслуживания VIN {vin}']
    lines.append(f'Всего записей: {len(records)}')
    lines.append('')

    for idx, record in enumerate(records, 1):
        lines.append(f'{idx}. {record.maintenance_type}')
        lines.append(f'   Дата: {record.date}')
        lines.append(f'   Пробег: {record.odometer:,} км')
        lines.append(
            f'   Дилер: {record.dealer.name}, '
            f'код {record.dealer.code or "N/A"} '
            f'({record.dealer.city})'
        )
        lines.append('')

    return '\n'.join(lines)


def format_vehicle_repairs_history_text(
    vin: str,
    records: List[VehicleRepairRecord]
) -> str:
    """
    Форматирует текстовое описание истории ремонтов DNM.

    Args:
        vin: VIN номер автомобиля
        records: Список записей о ремонтах DNM

    Returns:
        Отформатированный текст для отображения
    """
    if not records:
        return f'Для VIN {vin}: записи не найдены'

    lines = [f'История ремонтов из дилерской сети для VIN {vin}']
    lines.append(f'Всего визитов: {len(records)}')
    lines.append('')

    for idx, record in enumerate(records, 1):
        lines.append(f'═══ Визит {idx} ═══')
        lines.append(f'Дилер: {record.dealer_name}')
        lines.append(f'Дата: {record.date}')
        lines.append(f'Пробег: {record.odometer:,} км')
        lines.append(f'Тип ремонта: {record.repair_type}')
        lines.append(f'Причина визита: {record.visit_reason}')
        lines.append(f'Рекомендации: {record.recommendations}')
        lines.append('')

    return '\n'.join(lines)


def format_compliance_rag_text(
    query: str,
    documents: List[RAGDocument],
    max_content_length: int = 300
) -> str:
    """
    Форматирует текстовое описание результатов поиска в базе знаний.

    Args:
        query: Исходный запрос пользователя
        documents: Список найденных документов
        max_content_length: Максимальная длина содержимого документа

    Returns:
        Отформатированный текст для отображения
    """
    if not documents:
        return f'По запросу "{query}" документы не найдены'

    lines = [f'Результаты поиска по запросу: "{query}"']
    lines.append(f'Найдено документов: {len(documents)}')
    lines.append('')

    for idx, doc in enumerate(documents, 1):
        lines.append(f'─── Документ {idx} ───')

        content = doc.content
        if len(content) > max_content_length:
            content = content[:max_content_length] + '...'
        lines.append(f'Содержание: {content}')

        if doc.metadata:
            metadata_str = ', '.join(
                f'{k}: {v}' for k, v in doc.metadata.items()
            )
            lines.append(f'Метаданные: {metadata_str}')

        if doc.relevance_score is not None:
            lines.append(f'Релевантность: {doc.relevance_score:.2f}')

        lines.append('')

    return '\n'.join(lines)
