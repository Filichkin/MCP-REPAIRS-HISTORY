'''
Форматирование выходных данных для ответов агента.

Этот модуль предоставляет функции для форматирования выходных данных для
ответов агента в различных форматах, подходящих для разных аудиторий
(технических, пользовательских и т.д.).
'''

from typing import Any
from datetime import datetime, date
import json


def format_date(dt: datetime | date | str | None) -> str:
    '''
    Форматирование даты в русском стиле.

    Args:
        dt: Объект даты/datetime или ISO строка

    Returns:
        Форматированная дата строка (DD.MM.YYYY)
    '''
    if dt is None:
        return 'Не указано'

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt

    if isinstance(dt, (datetime, date)):
        return dt.strftime('%d.%m.%Y')

    return str(dt)


def format_currency(amount: float | int | None, currency: str = 'RUB') -> str:
    '''
    Форматирование суммы валюты.

    Args:
        amount: Сумма для форматирования
        currency: Код валюты (по умолчанию: RUB)

    Returns:
        Formatted currency string
    '''
    if amount is None:
        return 'Не указано'

    symbols = {
        'RUB': '₽',
        'USD': '$',
        'EUR': '€',
    }

    symbol = symbols.get(currency, currency)
    return f'{amount:,.2f} {symbol}'.replace(',', ' ')


def format_duration_days(days: int | None) -> str:
    '''
    Форматирование продолжительности в днях с правильным русским склонением.

    Args:
        days: Количество дней

    Returns:
        Форматированная строка (например, "5 дней", "1 день", "22 дня")
    '''
    if days is None:
        return 'Не указано'

    if days % 10 == 1 and days % 100 != 11:
        return f'{days} день'
    elif days % 10 in [2, 3, 4] and days % 100 not in [12, 13, 14]:
        return f'{days} дня'
    else:
        return f'{days} дней'


def format_warranty_status(is_active: bool) -> str:
    '''
    Форматирование статуса гарантии.

    Args:
        is_active: Является ли гарантия активной

    Returns:
        Форматированная строка статуса
    '''
    return 'Активна' if is_active else 'Истекла'


def format_json_output(data: Any, indent: int = 2) -> str:
    '''
    Форматирование данных в красивый JSON.

    Args:
        data: Данные для форматирования
        indent: Уровень отступа

    Returns:
        Строка JSON
    '''
    return json.dumps(data, ensure_ascii=False, indent=indent, default=str)


def format_table(
    headers: list[str], rows: list[list[Any]], max_width: int = 120
) -> str:
    '''
    Форматирование данных в ASCII таблицу.

    Args:
        headers: Заголовки столбцов
        rows: Строки данных
        max_width: Максимальная ширина таблицы

    Returns:
        Форматированная строка таблицы
    '''
    if not rows:
        return 'Нет данных'

    # Calculate column widths
    num_cols = len(headers)
    col_widths = [len(h) for h in headers]

    for row in rows:
        for i, cell in enumerate(row[:num_cols]):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Adjust if total width exceeds max_width
    total_width = sum(col_widths) + (num_cols - 1) * 3 + 4
    if total_width > max_width:
        reduction = (total_width - max_width) // num_cols
        col_widths = [max(10, w - reduction) for w in col_widths]

    # Build table
    separator = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'
    lines = [separator]

    # Headers
    header_line = (
        '| '
        + ' | '.join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        + ' |'
    )
    lines.append(header_line)
    lines.append(separator)

    # Rows
    for row in rows:
        cells = [str(cell) for cell in row[:num_cols]]
        # Truncate if needed
        cells = [
            (c[:col_widths[i] - 3] + '...' if len(c) > col_widths[i] else c)
            for i, c in enumerate(cells)
        ]
        row_line = (
            '| '
            + ' | '.join(cells[i].ljust(
                col_widths[i]) for i in range(num_cols)
                )
            + ' |'
        )
        lines.append(row_line)

    lines.append(separator)
    return '\n'.join(lines)


def format_bullet_list(items: list[str], indent: int = 0) -> str:
    '''
    Форматирование списка в список с маркерами.

    Args:
        items: Список элементов
        indent: Уровень отступа

    Returns:
        Форматированный список с маркерами
    '''
    prefix = ' ' * indent
    return '\n'.join(f'{prefix}• {item}' for item in items)


def format_numbered_list(items: list[str], indent: int = 0) -> str:
    '''
    Форматирование списка в нумерованный список.

    Args:
        items: Список элементов
        indent: Уровень отступа

    Returns:
        Форматированный нумерованный список
    '''
    prefix = ' ' * indent
    return (
        '\n'.join(f'{prefix}{i + 1}. {item}' for i, item in enumerate(items))
        )


def truncate_text(
    text: str,
    max_length: int = 100,
    suffix: str = '...',
) -> str:
    '''
    Обрезание текста до максимальной длины.

    Args:
        text: Текст для обрезки
        max_length: Максимальная длина
        suffix: Суффикс для добавления если обрезан

    Returns:
        Обрезанный текст
    '''
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def highlight_warning(text: str) -> str:
    '''
    Подсветка предупреждения.

    Args:
        text: Текст предупреждения

    Returns:
        Форматированный текст предупреждения
    '''
    return f'⚠️  ВНИМАНИЕ: {text}'


def highlight_error(text: str) -> str:
    '''
    Подсветка ошибки.

    Args:
        text: Текст ошибки

    Returns:
        Форматированный текст ошибки
    '''
    return f'❌ ОШИБКА: {text}'


def highlight_success(text: str) -> str:
    '''
    Подсветка успешного текста.

    Args:
        text: Текст успешного результата

    Returns:
        Форматированный текст успешного результата
    '''
    return f'✅ {text}'


def highlight_info(text: str) -> str:
    '''
    Подсветка информационного текста.

    Args:
        text: Текст информации

    Returns:
        Форматированный текст информации
    '''
    return f'ℹ️  {text}'
