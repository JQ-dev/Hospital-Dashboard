"""
Unit tests for utils/formatting.py
"""

import pytest
import pandas as pd
from utils.formatting import (
    format_currency,
    clean_re_line_name,
    clean_cost_line_name,
    is_subtotal_line,
    format_number_compact
)


class TestFormatCurrency:
    """Test currency formatting function"""

    def test_format_zero(self):
        """Test formatting zero value"""
        assert format_currency(0) == "0.00"

    def test_format_nan(self):
        """Test formatting NaN value"""
        assert format_currency(pd.NA) == "0.00"
        assert format_currency(float('nan')) == "0.00"

    def test_format_millions(self):
        """Test formatting values in millions"""
        assert format_currency(1000000) == "1.00"
        assert format_currency(1500000) == "1.50"
        assert format_currency(12345678) == "12.35"

    def test_format_negative(self):
        """Test formatting negative values"""
        assert format_currency(-1000000) == "-1.00"
        assert format_currency(-12345678) == "-12.35"

    def test_format_precision(self):
        """Test decimal precision"""
        assert format_currency(1234567) == "1.23"
        assert format_currency(1235567) == "1.24"  # Rounds up


class TestCleanReLineName:
    """Test revenue & expenses line name cleaning"""

    def test_clean_with_prefix(self):
        """Test removing Rev&Exp prefix"""
        assert clean_re_line_name("Rev&Exp Total Revenue") == "Total Revenue"
        assert clean_re_line_name("Rev&Exp Operating Expenses") == "Operating Expenses"

    def test_clean_without_prefix(self):
        """Test handling names without prefix"""
        assert clean_re_line_name("Total Revenue") == "Total Revenue"
        assert clean_re_line_name("Operating Expenses") == "Operating Expenses"

    def test_clean_nan(self):
        """Test handling NaN values"""
        assert clean_re_line_name(pd.NA) == ""
        assert clean_re_line_name(None) == ""

    def test_clean_empty_string(self):
        """Test handling empty strings"""
        assert clean_re_line_name("") == ""
        assert clean_re_line_name("   ") == ""


class TestCleanCostLineName:
    """Test cost line name cleaning"""

    def test_clean_with_prefix(self):
        """Test removing Cost prefix"""
        assert clean_cost_line_name("Cost Salaries") == "Salaries"
        assert clean_cost_line_name("Cost Benefits") == "Benefits"

    def test_clean_without_prefix(self):
        """Test handling names without prefix"""
        assert clean_cost_line_name("Salaries") == "Salaries"
        assert clean_cost_line_name("Benefits") == "Benefits"

    def test_clean_nan(self):
        """Test handling NaN values"""
        assert clean_cost_line_name(pd.NA) == ""
        assert clean_cost_line_name(None) == ""

    def test_clean_empty_string(self):
        """Test handling empty strings"""
        assert clean_cost_line_name("") == ""
        assert clean_cost_line_name("   ") == ""


class TestIsSubtotalLine:
    """Test subtotal line detection"""

    def test_detect_total(self):
        """Test detecting 'total' keywords"""
        assert is_subtotal_line("Total Revenue") == True
        assert is_subtotal_line("Grand Total") == True
        assert is_subtotal_line("TOTAL EXPENSES") == True

    def test_detect_subtotal(self):
        """Test detecting 'subtotal' keywords"""
        assert is_subtotal_line("Subtotal Operating") == True
        assert is_subtotal_line("SUBTOTAL") == True

    def test_detect_net(self):
        """Test detecting 'net' keywords"""
        assert is_subtotal_line("Net Income") == True
        assert is_subtotal_line("NET REVENUE") == True

    def test_detect_gross(self):
        """Test detecting 'gross' keywords"""
        assert is_subtotal_line("Gross Revenue") == True
        assert is_subtotal_line("GROSS PROFIT") == True

    def test_detect_sum_of(self):
        """Test detecting 'sum of' keywords"""
        assert is_subtotal_line("Sum of Expenses") == True
        assert is_subtotal_line("SUM OF REVENUE") == True

    def test_regular_line(self):
        """Test regular (non-subtotal) lines"""
        assert is_subtotal_line("Salaries") == False
        assert is_subtotal_line("Patient Revenue") == False
        assert is_subtotal_line("Operating Expenses") == False

    def test_nan_value(self):
        """Test handling NaN values"""
        assert is_subtotal_line(pd.NA) == False
        assert is_subtotal_line(None) == False

    def test_empty_string(self):
        """Test handling empty strings"""
        assert is_subtotal_line("") == False
        assert is_subtotal_line("   ") == False


class TestFormatNumberCompact:
    """Test compact number formatting with K/M/B suffixes"""

    def test_format_thousands(self):
        """Test formatting thousands with K suffix"""
        assert format_number_compact(1_234) == "1.2K"
        assert format_number_compact(9_876) == "9.9K"
        assert format_number_compact(1_000) == "1.0K"

    def test_format_millions(self):
        """Test formatting millions with M suffix"""
        assert format_number_compact(2_345_678) == "2.3M"
        assert format_number_compact(12_320_000) == "12.3M"
        assert format_number_compact(2_310_000) == "2.3M"

    def test_format_billions(self):
        """Test formatting billions with B suffix"""
        assert format_number_compact(1_234_567_890) == "1.2B"
        assert format_number_compact(9_876_543_210) == "9.9B"

    def test_format_small_numbers(self):
        """Test formatting small numbers without suffix"""
        assert format_number_compact(123) == "123"
        assert format_number_compact(12.5) == "12"
        assert format_number_compact(2.3) == "2.3"
        assert format_number_compact(9.99) == "10.0"

    def test_format_zero(self):
        """Test formatting zero"""
        assert format_number_compact(0) == "0"

    def test_format_negative(self):
        """Test formatting negative numbers"""
        assert format_number_compact(-1_234) == "-1.2K"
        assert format_number_compact(-2_345_678) == "-2.3M"
        assert format_number_compact(-1_234_567_890) == "-1.2B"

    def test_format_nan(self):
        """Test handling NaN values"""
        assert format_number_compact(pd.NA) == "0"
        assert format_number_compact(float('nan')) == "0"

    def test_boundary_values(self):
        """Test boundary values between K/M/B"""
        assert format_number_compact(999) == "999"
        assert format_number_compact(1_000) == "1.0K"
        assert format_number_compact(999_999) == "1000.0K"
        assert format_number_compact(1_000_000) == "1.0M"
        assert format_number_compact(999_999_999) == "1000.0M"
        assert format_number_compact(1_000_000_000) == "1.0B"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
