'''
Валидация VIN (Vehicle Identification Number) номеров.

Этот модуль предоставляет функции для валидации VIN номеров в соответствии
с международными стандартами.
'''

import re
from typing import Optional


class VINValidator:
    '''Валидатор для VIN номеров.'''

    # VIN должен содержать ровно 17 символов, за исключением I, O, Q
    VIN_PATTERN = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')

    # Значения транслитерации для расчета контрольной цифры VIN
    TRANSLITERATION = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
        'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9,
        'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9,
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
        '8': 8, '9': 9,
    }

    # Весовые коэффициенты для расчета контрольной цифры
    WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

    @classmethod
    def validate(cls, vin: str) -> tuple[bool, Optional[str]]:
        '''
        Валидация VIN номера.

        Args:
            vin: VIN номер для валидации

        Returns:
            Кортеж из (is_valid, error_message)
            Если валидный, error_message равен None
            Если невалидный, error_message описывает проблему
        '''
        if not vin:
            return False, 'VIN не может быть пустым'

        # Convert to uppercase and strip whitespace
        vin = vin.upper().strip()

        # Check length
        if len(vin) != 17:
            return (
                False,
                f'VIN должен содержать 17 символов, получено: {len(vin)}',
                )

        # Check pattern
        if not cls.VIN_PATTERN.match(vin):
            invalid_chars = set(
                c for c in vin if c in 'IOQ' or not c.isalnum()
                )
            if invalid_chars:
                return (
                    False,
                    f'VIN содержит недопустимые символы: '
                    f'{", ".join(invalid_chars)}',
                )
            return False, 'VIN содержит недопустимые символы'

        return True, None

    @classmethod
    def normalize(cls, vin: str) -> str:
        '''
        Нормализация VIN путем преобразования
        в верхний регистр и удаления пробелов.

        Args:
            vin: VIN номер для нормализации

        Returns:
            Нормализованный VIN строка
        '''
        return vin.upper().strip()

    @classmethod
    def extract_info(cls, vin: str) -> dict[str, str]:
        '''
        Извлечение основной информации из VIN.

        Args:
            vin: Валидный VIN номер

        Returns:
            Словарь с компонентами VIN:
            - wmi: World Manufacturer Identifier (позиции 1-3)
            - vds: Vehicle Descriptor Section (позиции 4-9)
            - vis: Vehicle Identifier Section (позиции 10-17)
            - year_code: Model year code (позиция 10)
            - plant_code: Assembly plant code (позиция 11)
            - serial: Serial number (позиции 12-17)
        '''
        vin = cls.normalize(vin)

        return {
            'wmi': vin[0:3],
            'vds': vin[3:9],
            'vis': vin[9:17],
            'year_code': vin[9],
            'plant_code': vin[10],
            'serial': vin[11:17],
        }


def validate_vin(vin: str) -> tuple[bool, Optional[str]]:
    '''
    Удобная функция для валидации VIN.

    Args:
        vin: VIN номер для валидации

    Returns:
        Кортеж из (is_valid, error_message)
    '''
    return VINValidator.validate(vin)


def normalize_vin(vin: str) -> str:
    '''
    Удобная функция для нормализации VIN.

    Args:
        vin: VIN номер для нормализации

    Returns:
        Нормализованный VIN строка
    '''
    return VINValidator.normalize(vin)
