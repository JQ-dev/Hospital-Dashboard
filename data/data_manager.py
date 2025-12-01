"""
Hospital Data Manager

Central data access layer for hospital analytics.
Provides unified access to KPI calculations, benchmarks, and financial data
from either DuckDB database (optimized) or parquet files (fallback).
"""

import logging
from pathlib import Path
import pandas as pd
import duckdb
from typing import Optional, Dict, List, Union

from config.paths import (
    BALANCE_SHEET_OUTPUT,
    REVENUE_OUTPUT,
    REVENUE_EXPENSES_OUTPUT,
    COSTS_A000_OUTPUT,
    COSTS_B100_OUTPUT,
    PROJECT_ROOT
)

# Configure logging
logger = logging.getLogger(__name__)


class HospitalDataManager:
    """
    Central data access layer for hospital analytics.

    Provides unified access to KPI calculations, benchmarks, and financial data
    from either DuckDB database (optimized) or parquet files (fallback).

    Attributes:
        use_database (bool): True if using DuckDB, False if using parquet files
        db_path (str): Path to DuckDB database file
        read_only (bool): Whether to open database in read-only mode

    Example:
        >>> dm = HospitalDataManager(db_path="hospital_analytics.duckdb")
        >>> kpis = dm.calculate_kpis('010001')
        >>> print(kpis['net_income_margin'])
    """

    def __init__(self, db_path: Optional[str] = None, read_only: bool = True):
        """
        Initialize HospitalDataManager

        Args:
            db_path: Path to DuckDB database file (optional)
            read_only: Whether to open database in read-only mode
        """
        self.read_only = read_only
        self.connection = None

        # Determine data source
        if db_path is None:
            # Try default locations
            default_paths = [
                PROJECT_ROOT / 'hospital_analytics.duckdb',
                PROJECT_ROOT / 'data' / 'hospital_analytics.duckdb'
            ]
            for path in default_paths:
                if path.exists():
                    db_path = str(path)
                    break

        if db_path and Path(db_path).exists():
            self.use_database = True
            self.db_path = db_path
            logger.info(f"Using DuckDB database: {db_path}")
        else:
            self.use_database = False
            self.db_path = None
            logger.warning("DuckDB database not found. Falling back to parquet files.")
            logger.warning("Performance will be slower. Consider building database with scripts/build_database.py")

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """
        Get database connection (creates if doesn't exist)

        Returns:
            DuckDB connection object

        Raises:
            RuntimeError: If not using database mode
        """
        if not self.use_database:
            raise RuntimeError("Not using database mode. Cannot get connection.")

        if self.connection is None or self.connection.is_closed():
            self.connection = duckdb.connect(self.db_path, read_only=self.read_only)
            logger.debug(f"Opened database connection: {self.db_path}")

        return self.connection

    def close(self):
        """Close database connection if open"""
        if self.connection and not self.connection.is_closed():
            self.connection.close()
            logger.debug("Closed database connection")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection"""
        self.close()

    def get_available_hospitals(self) -> pd.DataFrame:
        """
        Get list of available hospitals from data source

        Returns:
            DataFrame with columns: Provider_Number, State_Code, Year_Count

        Example:
            >>> dm = HospitalDataManager()
            >>> hospitals = dm.get_available_hospitals()
            >>> print(f"Found {len(hospitals)} hospitals")
        """
        try:
            if self.use_database:
                return self._get_hospitals_from_database()
            else:
                return self._get_hospitals_from_parquet()
        except Exception as e:
            logger.error(f"Error loading hospitals: {e}", exc_info=True)
            return pd.DataFrame()

    def _get_hospitals_from_database(self) -> pd.DataFrame:
        """Get hospitals from DuckDB database"""
        con = self.get_connection()

        query = """
            SELECT DISTINCT
                Provider_Number,
                State_Code,
                COUNT(DISTINCT Fiscal_Year) as Year_Count
            FROM hospital_metadata
            GROUP BY Provider_Number, State_Code
            ORDER BY Provider_Number
        """

        try:
            return con.execute(query).fetchdf()
        except Exception as e:
            logger.error(f"Error querying hospital_metadata table: {e}")
            # Fallback: try hospital_kpis table
            try:
                query = """
                    SELECT DISTINCT
                        Provider_Number,
                        CAST(SUBSTR(CAST(Provider_Number AS VARCHAR), 1, 2) AS INTEGER) as State_Code,
                        COUNT(DISTINCT Fiscal_Year) as Year_Count
                    FROM hospital_kpis
                    GROUP BY Provider_Number
                    ORDER BY Provider_Number
                """
                return con.execute(query).fetchdf()
            except Exception as e2:
                logger.error(f"Error querying hospital_kpis table: {e2}")
                return pd.DataFrame()

    def _get_hospitals_from_parquet(self) -> pd.DataFrame:
        """Get hospitals from parquet files"""
        try:
            # Try to read from balance sheet parquet
            if BALANCE_SHEET_OUTPUT.exists():
                con = duckdb.connect()
                query = f"""
                    SELECT DISTINCT
                        Provider_Number,
                        CAST(SUBSTR(CAST(Provider_Number AS VARCHAR), 1, 2) AS INTEGER) as State_Code,
                        COUNT(DISTINCT Fiscal_Year) as Year_Count
                    FROM read_parquet('{BALANCE_SHEET_OUTPUT}/*.parquet')
                    GROUP BY Provider_Number
                    ORDER BY Provider_Number
                """
                return con.execute(query).fetchdf()
            else:
                logger.error(f"Balance sheet parquet directory not found: {BALANCE_SHEET_OUTPUT}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error reading parquet files: {e}", exc_info=True)
            return pd.DataFrame()

    def classify_hospital_type(self, ccn: str) -> str:
        """
        Classify hospital type based on CCN (Provider Number)

        Hospital types are determined by the first 2 digits of the CCN:
        - 00-02: Short Term Acute Care
        - 03-04: Rehabilitation
        - 05-06: Psychiatric
        - 13: Swing Bed
        - 20-22: Long Term Care
        - 33: Critical Access Hospital

        Args:
            ccn: Provider number (6-digit string)

        Returns:
            Hospital type string (e.g., "Short Term Acute Care", "Critical Access Hospital")

        Example:
            >>> dm = HospitalDataManager()
            >>> print(dm.classify_hospital_type('010001'))
            'Short Term Acute Care'
            >>> print(dm.classify_hospital_type('330001'))
            'Critical Access Hospital'
        """
        try:
            ccn_str = str(int(ccn)).zfill(6)
            prefix = int(ccn_str[:2])

            if prefix <= 2:
                return "Short Term Acute Care"
            elif prefix <= 4:
                return "Rehabilitation"
            elif prefix <= 6:
                return "Psychiatric"
            elif prefix == 13:
                return "Swing Bed"
            elif prefix <= 22:
                return "Long Term Care"
            elif prefix == 33:
                return "Critical Access Hospital"
            else:
                return "Other"
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid CCN format: {ccn} - {e}")
            return "Unknown"

    def calculate_kpis(self, ccn: str, year: Optional[int] = None) -> pd.DataFrame:
        """
        Calculate all Level 1 KPIs for a hospital

        Args:
            ccn: Provider number (6-digit string)
            year: Fiscal year (optional, defaults to latest available)

        Returns:
            DataFrame with KPI data indexed by Fiscal_Year

        Example:
            >>> dm = HospitalDataManager()
            >>> kpis = dm.calculate_kpis('010001')
            >>> print(kpis[['net_income_margin', 'operating_margin']])
        """
        try:
            if self.use_database:
                return self._calculate_kpis_from_database(ccn, year)
            else:
                return self._calculate_kpis_from_parquet(ccn, year)
        except Exception as e:
            logger.error(f"Error calculating KPIs for {ccn}: {e}", exc_info=True)
            return pd.DataFrame()

    def _calculate_kpis_from_database(self, ccn: str, year: Optional[int] = None) -> pd.DataFrame:
        """Calculate KPIs from DuckDB database"""
        con = self.get_connection()
        ccn_str = str(int(ccn)).zfill(6)

        if year:
            query = f"""
                SELECT *
                FROM hospital_kpis
                WHERE Provider_Number = '{ccn_str}'
                AND Fiscal_Year = {year}
            """
        else:
            query = f"""
                SELECT *
                FROM hospital_kpis
                WHERE Provider_Number = '{ccn_str}'
                ORDER BY Fiscal_Year
            """

        try:
            df = con.execute(query).fetchdf()
            if not df.empty:
                df = df.set_index('Fiscal_Year')
            return df
        except Exception as e:
            logger.error(f"Error querying hospital_kpis for {ccn_str}: {e}")
            return pd.DataFrame()

    def _calculate_kpis_from_parquet(self, ccn: str, year: Optional[int] = None) -> pd.DataFrame:
        """
        Calculate KPIs from parquet files (slower fallback)

        This is a simplified implementation. For production use, implement full KPI calculations
        from raw financial data in parquet files.
        """
        logger.warning("KPI calculation from parquet files not fully implemented")
        logger.warning("Please build the database using scripts/build_database.py for full functionality")

        # Return empty DataFrame with expected structure
        return pd.DataFrame(columns=['Provider_Number', 'Fiscal_Year'])

    def get_benchmarks(
        self,
        ccn: str,
        year: int,
        level: str
    ) -> Dict[str, float]:
        """
        Get benchmark data for a hospital at specified level

        Benchmark levels:
        - 'National': Compare against all US hospitals
        - 'State': Compare against hospitals in same state
        - 'Hospital_Type': Compare against same hospital type
        - 'State_Hospital_Type': Compare against same state AND type (most specific)

        Args:
            ccn: Provider number (6-digit string)
            year: Fiscal year
            level: Benchmark level (National, State, Hospital_Type, State_Hospital_Type)

        Returns:
            Dict with benchmark statistics: {
                'p25': float,     # 25th percentile
                'median': float,  # 50th percentile (median)
                'p75': float,     # 75th percentile
                'mean': float,    # Mean value
                'count': int      # Number of peers
            }

        Example:
            >>> dm = HospitalDataManager()
            >>> benchmarks = dm.get_benchmarks('010001', 2024, 'State')
            >>> print(f"Median: {benchmarks['median']}, Peers: {benchmarks['count']}")
        """
        try:
            if self.use_database:
                return self._get_benchmarks_from_database(ccn, year, level)
            else:
                return self._get_benchmarks_from_parquet(ccn, year, level)
        except Exception as e:
            logger.error(f"Error getting benchmarks for {ccn}: {e}", exc_info=True)
            return {}

    def _get_benchmarks_from_database(
        self,
        ccn: str,
        year: int,
        level: str
    ) -> Dict[str, float]:
        """Get benchmarks from DuckDB database"""
        con = self.get_connection()
        ccn_str = str(int(ccn)).zfill(6)

        query = f"""
            SELECT *
            FROM hospital_benchmarks
            WHERE Provider_Number = '{ccn_str}'
            AND Fiscal_Year = {year}
            AND Benchmark_Level = '{level}'
        """

        try:
            df = con.execute(query).fetchdf()
            if df.empty:
                logger.warning(f"No benchmarks found for {ccn_str}, {year}, {level}")
                return {}

            # Convert DataFrame row to dict
            return df.iloc[0].to_dict()
        except Exception as e:
            logger.error(f"Error querying hospital_benchmarks: {e}")
            return {}

    def _get_benchmarks_from_parquet(
        self,
        ccn: str,
        year: int,
        level: str
    ) -> Dict[str, float]:
        """
        Calculate benchmarks from parquet files (slower fallback)

        This is a simplified implementation. For production use, implement full benchmark
        calculations from raw data in parquet files.
        """
        logger.warning("Benchmark calculation from parquet files not fully implemented")
        logger.warning("Please build the database using scripts/build_database.py for full functionality")
        return {}

    def calculate_level2_kpis(self, ccn: str, year: int) -> pd.DataFrame:
        """
        Calculate Level 2 KPIs (drivers of Level 1 KPIs)

        Args:
            ccn: Provider number (6-digit string)
            year: Fiscal year

        Returns:
            DataFrame with Level 2 KPI data

        Example:
            >>> dm = HospitalDataManager()
            >>> l2_kpis = dm.calculate_level2_kpis('010001', 2024)
        """
        try:
            if self.use_database:
                return self._calculate_level2_kpis_from_database(ccn, year)
            else:
                return self._calculate_level2_kpis_from_parquet(ccn, year)
        except Exception as e:
            logger.error(f"Error calculating Level 2 KPIs for {ccn}: {e}", exc_info=True)
            return pd.DataFrame()

    def _calculate_level2_kpis_from_database(self, ccn: str, year: int) -> pd.DataFrame:
        """Calculate Level 2 KPIs from database"""
        con = self.get_connection()
        ccn_str = str(int(ccn)).zfill(6)

        # Try to query Level 2 KPIs table if it exists
        try:
            query = f"""
                SELECT *
                FROM hospital_level2_kpis
                WHERE Provider_Number = '{ccn_str}'
                AND Fiscal_Year = {year}
            """
            return con.execute(query).fetchdf()
        except Exception:
            # Table doesn't exist, return empty DataFrame
            logger.debug("hospital_level2_kpis table not found")
            return pd.DataFrame()

    def _calculate_level2_kpis_from_parquet(self, ccn: str, year: int) -> pd.DataFrame:
        """Calculate Level 2 KPIs from parquet files"""
        logger.warning("Level 2 KPI calculation from parquet files not implemented")
        return pd.DataFrame()

    def calculate_level3_kpis(self, ccn: str, year: int) -> pd.DataFrame:
        """
        Calculate Level 3 KPIs (drivers of Level 2 KPIs)

        Args:
            ccn: Provider number (6-digit string)
            year: Fiscal year

        Returns:
            DataFrame with Level 3 KPI data

        Example:
            >>> dm = HospitalDataManager()
            >>> l3_kpis = dm.calculate_level3_kpis('010001', 2024)
        """
        try:
            if self.use_database:
                return self._calculate_level3_kpis_from_database(ccn, year)
            else:
                return self._calculate_level3_kpis_from_parquet(ccn, year)
        except Exception as e:
            logger.error(f"Error calculating Level 3 KPIs for {ccn}: {e}", exc_info=True)
            return pd.DataFrame()

    def _calculate_level3_kpis_from_database(self, ccn: str, year: int) -> pd.DataFrame:
        """Calculate Level 3 KPIs from database"""
        con = self.get_connection()
        ccn_str = str(int(ccn)).zfill(6)

        # Try to query Level 3 KPIs table if it exists
        try:
            query = f"""
                SELECT *
                FROM hospital_level3_kpis
                WHERE Provider_Number = '{ccn_str}'
                AND Fiscal_Year = {year}
            """
            return con.execute(query).fetchdf()
        except Exception:
            # Table doesn't exist, return empty DataFrame
            logger.debug("hospital_level3_kpis table not found")
            return pd.DataFrame()

    def _calculate_level3_kpis_from_parquet(self, ccn: str, year: int) -> pd.DataFrame:
        """Calculate Level 3 KPIs from parquet files"""
        logger.warning("Level 3 KPI calculation from parquet files not implemented")
        return pd.DataFrame()

    def get_financial_statement(
        self,
        ccn: str,
        statement_type: str,
        years: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Get financial statement data (Balance Sheet, Revenue, Expenses, Costs)

        Args:
            ccn: Provider number (6-digit string)
            statement_type: Type of statement ('balance_sheet', 'revenue', 'revenue_expenses', 'costs_a000', 'costs_b100')
            years: List of fiscal years (optional, defaults to all available)

        Returns:
            DataFrame with financial statement data

        Example:
            >>> dm = HospitalDataManager()
            >>> balance_sheet = dm.get_financial_statement('010001', 'balance_sheet', [2023, 2024])
        """
        try:
            if self.use_database:
                return self._get_financial_statement_from_database(ccn, statement_type, years)
            else:
                return self._get_financial_statement_from_parquet(ccn, statement_type, years)
        except Exception as e:
            logger.error(f"Error getting financial statement for {ccn}: {e}", exc_info=True)
            return pd.DataFrame()

    def _get_financial_statement_from_database(
        self,
        ccn: str,
        statement_type: str,
        years: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """Get financial statement from database"""
        con = self.get_connection()
        ccn_str = str(int(ccn)).zfill(6)

        table_name = statement_type  # Assuming table names match statement types

        where_clauses = [f"Provider_Number = '{ccn_str}'"]
        if years:
            year_list = ','.join(map(str, years))
            where_clauses.append(f"Fiscal_Year IN ({year_list})")

        where_clause = ' AND '.join(where_clauses)

        query = f"""
            SELECT *
            FROM {table_name}
            WHERE {where_clause}
            ORDER BY Fiscal_Year, Line_Number
        """

        try:
            return con.execute(query).fetchdf()
        except Exception as e:
            logger.error(f"Error querying {table_name} table: {e}")
            return pd.DataFrame()

    def _get_financial_statement_from_parquet(
        self,
        ccn: str,
        statement_type: str,
        years: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """Get financial statement from parquet files"""
        # Map statement types to parquet directories
        parquet_paths = {
            'balance_sheet': BALANCE_SHEET_OUTPUT,
            'revenue': REVENUE_OUTPUT,
            'revenue_expenses': REVENUE_EXPENSES_OUTPUT,
            'costs_a000': COSTS_A000_OUTPUT,
            'costs_b100': COSTS_B100_OUTPUT
        }

        if statement_type not in parquet_paths:
            logger.error(f"Unknown statement type: {statement_type}")
            return pd.DataFrame()

        parquet_dir = parquet_paths[statement_type]
        if not parquet_dir.exists():
            logger.error(f"Parquet directory not found: {parquet_dir}")
            return pd.DataFrame()

        try:
            con = duckdb.connect()
            ccn_str = str(int(ccn)).zfill(6)

            where_clauses = [f"Provider_Number = '{ccn_str}'"]
            if years:
                year_list = ','.join(map(str, years))
                where_clauses.append(f"Fiscal_Year IN ({year_list})")

            where_clause = ' AND '.join(where_clauses)

            query = f"""
                SELECT *
                FROM read_parquet('{parquet_dir}/*.parquet')
                WHERE {where_clause}
                ORDER BY Fiscal_Year
            """

            return con.execute(query).fetchdf()
        except Exception as e:
            logger.error(f"Error reading parquet files from {parquet_dir}: {e}")
            return pd.DataFrame()
