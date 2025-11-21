"""
Unit tests for utils/financial_tables.py
"""

import pytest
import pandas as pd
from dash import html
from utils.financial_tables import create_multiyear_financial_table


class TestCreateMultiyearFinancialTable:
    """Test multi-year financial table generation"""

    def test_empty_dataframe(self):
        """Test handling empty dataframe"""
        df = pd.DataFrame()
        result = create_multiyear_financial_table(df, "Test Title", "balance_sheet")

        # Should return an alert div
        assert isinstance(result, html.Div)
        assert "No data available" in str(result)

    def test_none_dataframe(self):
        """Test handling None dataframe"""
        result = create_multiyear_financial_table(None, "Test Title", "balance_sheet")

        # Should return an alert div
        assert isinstance(result, html.Div)
        assert "No data available" in str(result)

    def test_balance_sheet_structure(self):
        """Test balance sheet table structure"""
        # Create sample balance sheet data
        df = pd.DataFrame({
            'Fiscal_Year': [2023, 2023, 2022, 2022],
            'Line': ['1000', '1100', '1000', '1100'],
            'Acc_level2': ['Assets', 'Assets', 'Assets', 'Assets'],
            'Acc_level3': ['Current Assets', 'Current Assets', 'Current Assets', 'Current Assets'],
            'Acc_name': ['Cash', 'Accounts Receivable', 'Cash', 'Accounts Receivable'],
            'Value': [1000000, 2000000, 900000, 1800000]
        })

        result = create_multiyear_financial_table(df, "Balance Sheet", "balance_sheet")

        # Should return a Div containing table
        assert isinstance(result, html.Div)
        # Should contain the title
        assert any("Balance Sheet" in str(child) for child in result.children)

    def test_revenue_expenses_structure(self):
        """Test revenue & expenses table structure"""
        df = pd.DataFrame({
            'Fiscal_Year': [2023, 2023, 2022, 2022],
            'Line': ['1000', '2000', '1000', '2000'],
            'RE_Line_Name': ['Rev&Exp Total Revenue', 'Rev&Exp Operating Expenses', 'Rev&Exp Total Revenue', 'Rev&Exp Operating Expenses'],
            'RE_Level': [1, 2, 1, 2],
            'Value': [5000000, 4000000, 4800000, 3900000]
        })

        result = create_multiyear_financial_table(df, "Revenue & Expenses", "revenue_expenses")

        # Should return a Div
        assert isinstance(result, html.Div)

    def test_unknown_statement_type(self):
        """Test handling unknown statement type"""
        df = pd.DataFrame({
            'Fiscal_Year': [2023],
            'Line': ['1000'],
            'Value': [1000000]
        })

        result = create_multiyear_financial_table(df, "Test", "invalid_type")

        # Should return a warning div
        assert isinstance(result, html.Div)
        assert "Unknown statement type" in str(result)

    def test_multi_year_columns(self):
        """Test that multiple years create separate columns"""
        df = pd.DataFrame({
            'Fiscal_Year': [2023, 2022, 2021],
            'Line': ['1000', '1000', '1000'],
            'Acc_level2': ['Assets', 'Assets', 'Assets'],
            'Acc_level3': ['Current Assets', 'Current Assets', 'Current Assets'],
            'Acc_name': ['Cash', 'Cash', 'Cash'],
            'Value': [1000000, 900000, 850000]
        })

        result = create_multiyear_financial_table(df, "Balance Sheet", "balance_sheet")

        # Check that note mentions all years
        result_str = str(result)
        assert "2021" in result_str
        assert "2022" in result_str
        assert "2023" in result_str


class TestTableHelpers:
    """Test helper functions within financial tables"""

    def test_table_contains_professional_styling(self):
        """Test that generated tables have professional styling"""
        df = pd.DataFrame({
            'Fiscal_Year': [2023],
            'Line': ['1000'],
            'Acc_level2': ['Assets'],
            'Acc_level3': ['Current Assets'],
            'Acc_name': ['Cash'],
            'Value': [1000000]
        })

        result = create_multiyear_financial_table(df, "Test", "balance_sheet")
        result_str = str(result)

        # Check for styling indicators
        assert "table" in result_str.lower()
        assert "style" in result_str.lower() or "className" in result_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
