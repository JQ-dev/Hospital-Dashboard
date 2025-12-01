"""
Input validation utilities for Hospital Dashboard

Provides validation functions for user inputs including:
- Provider Numbers (CCN)
- Fiscal Years
- Benchmark Levels
- KPI Keys
"""

import logging
from typing import Optional, List, Union
import re

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_ccn(ccn: Union[str, int]) -> str:
    """
    Validate and normalize Provider Number (CCN)

    CCN must be:
    - 6 digits long (with leading zeros)
    - Valid integer between 1 and 999999

    Args:
        ccn: Provider number (can be string or int)

    Returns:
        str: Normalized 6-digit CCN with leading zeros

    Raises:
        ValidationError: If CCN is invalid

    Example:
        >>> validate_ccn('10001')
        '010001'
        >>> validate_ccn(10001)
        '010001'
        >>> validate_ccn('invalid')
        ValidationError: Invalid CCN format: invalid
    """
    if ccn is None:
        raise ValidationError("CCN cannot be None")

    if ccn == '' or (isinstance(ccn, str) and ccn.strip() == ''):
        raise ValidationError("CCN cannot be empty")

    try:
        # Convert to int to validate it's numeric
        ccn_int = int(ccn)

        # Check range
        if not (1 <= ccn_int <= 999999):
            raise ValidationError(
                f"CCN must be between 1 and 999999, got: {ccn_int}"
            )

        # Return as 6-digit string with leading zeros
        return str(ccn_int).zfill(6)

    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid CCN format: {ccn}") from e


def validate_fiscal_year(year: Union[str, int]) -> int:
    """
    Validate fiscal year

    Fiscal year must be:
    - Valid integer
    - Between 2000 and current year + 5
    - Typically between 2020 and 2024 for HCRIS data

    Args:
        year: Fiscal year

    Returns:
        int: Validated fiscal year

    Raises:
        ValidationError: If year is invalid

    Example:
        >>> validate_fiscal_year(2023)
        2023
        >>> validate_fiscal_year('2023')
        2023
        >>> validate_fiscal_year(1990)
        ValidationError: Fiscal year must be between 2000 and 2030, got: 1990
    """
    if year is None:
        raise ValidationError("Fiscal year cannot be None")

    try:
        year_int = int(year)

        # Reasonable range for HCRIS data
        MIN_YEAR = 2000
        MAX_YEAR = 2030  # Allow some future years

        if not (MIN_YEAR <= year_int <= MAX_YEAR):
            raise ValidationError(
                f"Fiscal year must be between {MIN_YEAR} and {MAX_YEAR}, got: {year_int}"
            )

        return year_int

    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid fiscal year format: {year}") from e


def validate_benchmark_level(level: str) -> str:
    """
    Validate benchmark level

    Valid benchmark levels:
    - National: All US hospitals
    - State: Same state
    - Hospital_Type: Same hospital type
    - State_Hospital_Type: Same state and type

    Args:
        level: Benchmark level

    Returns:
        str: Validated benchmark level

    Raises:
        ValidationError: If level is invalid

    Example:
        >>> validate_benchmark_level('National')
        'National'
        >>> validate_benchmark_level('Invalid')
        ValidationError: Invalid benchmark level: Invalid
    """
    VALID_LEVELS = {
        'National',
        'State',
        'Hospital_Type',
        'State_Hospital_Type'
    }

    if level is None:
        raise ValidationError("Benchmark level cannot be None")

    if not isinstance(level, str):
        raise ValidationError(f"Benchmark level must be string, got: {type(level)}")

    if level not in VALID_LEVELS:
        raise ValidationError(
            f"Invalid benchmark level: {level}. "
            f"Must be one of: {', '.join(VALID_LEVELS)}"
        )

    return level


def validate_kpi_key(kpi_key: str) -> str:
    """
    Validate KPI key format

    KPI keys should be:
    - Non-empty string
    - Alphanumeric with underscores
    - No spaces or special characters

    Args:
        kpi_key: KPI identifier key

    Returns:
        str: Validated KPI key

    Raises:
        ValidationError: If KPI key is invalid

    Example:
        >>> validate_kpi_key('Net_Income_Margin')
        'Net_Income_Margin'
        >>> validate_kpi_key('Invalid KPI!')
        ValidationError: KPI key contains invalid characters: Invalid KPI!
    """
    if kpi_key is None:
        raise ValidationError("KPI key cannot be None")

    if not isinstance(kpi_key, str):
        raise ValidationError(f"KPI key must be string, got: {type(kpi_key)}")

    if not kpi_key.strip():
        raise ValidationError("KPI key cannot be empty")

    # Check for valid characters (alphanumeric + underscore)
    if not re.match(r'^[A-Za-z0-9_]+$', kpi_key):
        raise ValidationError(
            f"KPI key contains invalid characters: {kpi_key}. "
            "Only alphanumeric characters and underscores allowed."
        )

    return kpi_key


def validate_state_code(state_code: Union[str, int]) -> str:
    """
    Validate state code (first 2 digits of CCN)

    State codes must be:
    - 2 digits
    - Between 01 and 99

    Args:
        state_code: State code (2 digits)

    Returns:
        str: Validated 2-digit state code

    Raises:
        ValidationError: If state code is invalid

    Example:
        >>> validate_state_code('03')
        '03'
        >>> validate_state_code(3)
        '03'
        >>> validate_state_code('100')
        ValidationError: State code must be 2 digits, got: 100
    """
    if state_code is None:
        raise ValidationError("State code cannot be None")

    try:
        state_int = int(state_code)

        if not (1 <= state_int <= 99):
            raise ValidationError(
                f"State code must be between 01 and 99, got: {state_int}"
            )

        return str(state_int).zfill(2)

    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid state code format: {state_code}") from e


def validate_positive_number(value: Union[int, float], name: str = "Value") -> Union[int, float]:
    """
    Validate that a number is positive

    Args:
        value: Number to validate
        name: Name of the value (for error messages)

    Returns:
        Number (int or float): Validated positive number

    Raises:
        ValidationError: If value is not a positive number

    Example:
        >>> validate_positive_number(100, "Revenue")
        100
        >>> validate_positive_number(-50, "Revenue")
        ValidationError: Revenue must be positive, got: -50
    """
    if value is None:
        raise ValidationError(f"{name} cannot be None")

    try:
        if isinstance(value, str):
            value = float(value)

        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"{name} must be a number, got: {type(value)}"
            )

        if value <= 0:
            raise ValidationError(
                f"{name} must be positive, got: {value}"
            )

        return value

    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid {name} format: {value}") from e


def validate_year_list(years: List[int]) -> List[int]:
    """
    Validate a list of fiscal years

    Args:
        years: List of fiscal years

    Returns:
        List[int]: Validated list of fiscal years

    Raises:
        ValidationError: If any year is invalid

    Example:
        >>> validate_year_list([2020, 2021, 2022])
        [2020, 2021, 2022]
        >>> validate_year_list([2020, 'invalid'])
        ValidationError: Invalid fiscal year in list: invalid
    """
    if years is None:
        raise ValidationError("Year list cannot be None")

    if not isinstance(years, list):
        raise ValidationError(f"Years must be a list, got: {type(years)}")

    if len(years) == 0:
        raise ValidationError("Year list cannot be empty")

    validated_years = []
    for year in years:
        try:
            validated_years.append(validate_fiscal_year(year))
        except ValidationError as e:
            raise ValidationError(f"Invalid fiscal year in list: {year}") from e

    return validated_years


def safe_float(value, default: float = 0.0) -> float:
    """
    Safely convert value to float with default fallback

    This is a non-raising version of float() conversion.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        float: Converted value or default

    Example:
        >>> safe_float('123.45')
        123.45
        >>> safe_float('invalid', default=0.0)
        0.0
        >>> safe_float(None, default=-1.0)
        -1.0
    """
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        logger.debug(f"Could not convert {value} to float, using default {default}")
        return default


def safe_int(value, default: int = 0) -> int:
    """
    Safely convert value to int with default fallback

    This is a non-raising version of int() conversion.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        int: Converted value or default

    Example:
        >>> safe_int('123')
        123
        >>> safe_int('invalid', default=0)
        0
        >>> safe_int(123.7)
        123
    """
    try:
        if value is None:
            return default
        return int(float(value))  # Handle '123.0' strings
    except (ValueError, TypeError):
        logger.debug(f"Could not convert {value} to int, using default {default}")
        return default
