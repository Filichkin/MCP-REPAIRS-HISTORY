'''
VIN (Vehicle Identification Number) validation utilities.

This module provides functions for validating VIN numbers according to
international standards.
'''

import re
from typing import Optional


class VINValidator:
    '''Validator for Vehicle Identification Numbers.'''

    # VIN should be exactly 17 characters, excluding I, O, Q
    VIN_PATTERN = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')

    # Transliteration values for VIN check digit calculation
    TRANSLITERATION = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
        'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9,
        'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9,
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
        '8': 8, '9': 9,
    }

    # Weight factors for check digit calculation
    WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

    @classmethod
    def validate(cls, vin: str) -> tuple[bool, Optional[str]]:
        '''
        Validate VIN number.

        Args:
            vin: VIN number to validate

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is None
            If invalid, error_message describes the issue
        '''
        if not vin:
            return False, 'VIN не может быть пустым'

        # Convert to uppercase and strip whitespace
        vin = vin.upper().strip()

        # Check length
        if len(vin) != 17:
            return False, f'VIN должен содержать 17 символов, получено: {len(vin)}'

        # Check pattern
        if not cls.VIN_PATTERN.match(vin):
            invalid_chars = set(c for c in vin if c in 'IOQ' or not c.isalnum())
            if invalid_chars:
                return (
                    False,
                    f'VIN содержит недопустимые символы: {", ".join(invalid_chars)}',
                )
            return False, 'VIN содержит недопустимые символы'

        return True, None

    @classmethod
    def normalize(cls, vin: str) -> str:
        '''
        Normalize VIN by converting to uppercase and stripping whitespace.

        Args:
            vin: VIN number to normalize

        Returns:
            Normalized VIN string
        '''
        return vin.upper().strip()

    @classmethod
    def extract_info(cls, vin: str) -> dict[str, str]:
        '''
        Extract basic information from VIN.

        Args:
            vin: Valid VIN number

        Returns:
            Dictionary with VIN components:
            - wmi: World Manufacturer Identifier (positions 1-3)
            - vds: Vehicle Descriptor Section (positions 4-9)
            - vis: Vehicle Identifier Section (positions 10-17)
            - year_code: Model year code (position 10)
            - plant_code: Assembly plant code (position 11)
            - serial: Serial number (positions 12-17)
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
    Convenience function to validate VIN.

    Args:
        vin: VIN number to validate

    Returns:
        Tuple of (is_valid, error_message)
    '''
    return VINValidator.validate(vin)


def normalize_vin(vin: str) -> str:
    '''
    Convenience function to normalize VIN.

    Args:
        vin: VIN number to normalize

    Returns:
        Normalized VIN string
    '''
    return VINValidator.normalize(vin)
