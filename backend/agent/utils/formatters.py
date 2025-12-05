'''
Output formatting utilities for agent responses.

This module provides functions for formatting agent outputs in various formats
suitable for different audiences (technical, user-friendly, etc.).
'''

from typing import Any
from datetime import datetime, date
import json


def format_date(dt: datetime | date | str | None) -> str:
    '''
    Format date in Russian locale style.

    Args:
        dt: Date/datetime object or ISO string

    Returns:
        Formatted date string (DD.MM.YYYY)
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
    Format currency amount.

    Args:
        amount: Amount to format
        currency: Currency code (default: RUB)

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
    Format duration in days with proper Russian declension.

    Args:
        days: Number of days

    Returns:
        Formatted string (e.g., "5 дней", "1 день", "22 дня")
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
    Format warranty status.

    Args:
        is_active: Whether warranty is active

    Returns:
        Formatted status string
    '''
    return 'Активна' if is_active else 'Истекла'


def format_json_output(data: Any, indent: int = 2) -> str:
    '''
    Format data as pretty JSON.

    Args:
        data: Data to format
        indent: Indentation level

    Returns:
        JSON string
    '''
    return json.dumps(data, ensure_ascii=False, indent=indent, default=str)


def format_table(
    headers: list[str], rows: list[list[Any]], max_width: int = 120
) -> str:
    '''
    Format data as ASCII table.

    Args:
        headers: Column headers
        rows: Data rows
        max_width: Maximum table width

    Returns:
        Formatted table string
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
            + ' | '.join(cells[i].ljust(col_widths[i]) for i in range(num_cols))
            + ' |'
        )
        lines.append(row_line)

    lines.append(separator)
    return '\n'.join(lines)


def format_bullet_list(items: list[str], indent: int = 0) -> str:
    '''
    Format items as bullet list.

    Args:
        items: List items
        indent: Indentation level

    Returns:
        Formatted bullet list
    '''
    prefix = ' ' * indent
    return '\n'.join(f'{prefix}• {item}' for item in items)


def format_numbered_list(items: list[str], indent: int = 0) -> str:
    '''
    Format items as numbered list.

    Args:
        items: List items
        indent: Indentation level

    Returns:
        Formatted numbered list
    '''
    prefix = ' ' * indent
    return '\n'.join(f'{prefix}{i + 1}. {item}' for i, item in enumerate(items))


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    '''
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    '''
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def highlight_warning(text: str) -> str:
    '''
    Highlight warning text.

    Args:
        text: Warning text

    Returns:
        Formatted warning
    '''
    return f'⚠️  ВНИМАНИЕ: {text}'


def highlight_error(text: str) -> str:
    '''
    Highlight error text.

    Args:
        text: Error text

    Returns:
        Formatted error
    '''
    return f'❌ ОШИБКА: {text}'


def highlight_success(text: str) -> str:
    '''
    Highlight success text.

    Args:
        text: Success text

    Returns:
        Formatted success message
    '''
    return f'✅ {text}'


def highlight_info(text: str) -> str:
    '''
    Highlight info text.

    Args:
        text: Info text

    Returns:
        Formatted info message
    '''
    return f'ℹ️  {text}'
