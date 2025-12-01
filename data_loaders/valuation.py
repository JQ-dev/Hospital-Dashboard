"""
Valuation Data Loaders - Functions to load data for valuation analysis
"""

import pandas as pd

from utils.logging_config import get_logger

logger = get_logger(__name__)


def load_valuation_income_statement(data_manager, ccn, fiscal_year):
    """Load income statement data for valuation analysis"""
    con = data_manager.get_connection()
    try:
        query = """
        SELECT
            Line_Name,
            Section,
            Subsection,
            Value
        FROM income_statement_long
        WHERE Provider_Number = ?
            AND Fiscal_Year = ?
        ORDER BY Line
        """
        df = con.execute(query, [int(ccn), int(fiscal_year)]).df()
        con.close()
        return df
    except Exception as e:
        logger.error(f"Error loading income statement for valuation: {e}")
        con.close()
        return pd.DataFrame()


def load_valuation_expense_detail(data_manager, ccn, fiscal_year):
    """Load detailed expense breakdown for valuation analysis"""
    con = data_manager.get_connection()
    try:
        query = """
        SELECT
            Expense_Category,
            Category_Description,
            Category_Type,
            Column_Description,
            SUM(Value) as Total_Expense
        FROM expense_detail
        WHERE Provider_Number = ?
            AND Fiscal_Year = ?
            AND Column_Description = 'Final_Adjusted'
        GROUP BY Expense_Category, Category_Description, Category_Type, Column_Description
        ORDER BY Total_Expense DESC
        """
        df = con.execute(query, [int(ccn), int(fiscal_year)]).df()
        con.close()
        return df
    except Exception as e:
        logger.error(f"Error loading expense detail for valuation: {e}")
        con.close()
        return pd.DataFrame()
