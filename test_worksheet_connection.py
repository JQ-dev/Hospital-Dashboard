"""
Test Worksheet Database Connection
Tests Phase 1 implementation - connecting to hospital_worksheets.duckdb
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard import HospitalDataManager
import pandas as pd

def test_worksheet_connection():
    """Test worksheet database connection and access"""

    print("="*80)
    print("PHASE 1 TEST: Worksheet Database Connection")
    print("="*80)
    print()

    # Initialize data manager
    print("1. Initializing HospitalDataManager...")
    print("-" * 80)
    manager = HospitalDataManager(
        db_path='data/hospital_analytics.duckdb',
        worksheet_db_path='data/hospital_worksheets.duckdb'
    )
    print()

    # Check connection status
    print("2. Connection Status:")
    print("-" * 80)
    print(f"   Main database connected: {'[YES]' if manager.use_database else '[NO]'}")
    print(f"   Worksheet database connected: {'[YES]' if manager.use_worksheets else '[NO]'}")
    print(f"   Worksheet tables found: {manager.worksheet_count}")
    print()

    if not manager.use_worksheets:
        print("[FAIL] Worksheet database not available")
        return False

    # Verify worksheet access
    print("3. Verifying Worksheet Table Access:")
    print("-" * 80)
    verification = manager.verify_worksheet_access()

    print(f"   Status: {verification['status'].upper()}")
    print(f"   Message: {verification['message']}")
    print(f"   Tables accessible: {verification['tables_accessible']}/{verification['tables_total']}")

    if verification['errors']:
        print(f"\n   Errors ({len(verification['errors'])}):")
        for error in verification['errors']:
            print(f"      - {error}")
    print()

    # Get available worksheets
    print("4. Available Worksheets:")
    print("-" * 80)
    worksheets_df = manager.get_available_worksheets()

    if not worksheets_df.empty:
        # Sort by worksheet code
        worksheets_df = worksheets_df.sort_values('worksheet')

        print(f"\n   Total worksheets: {len(worksheets_df)}")
        print(f"   Total records: {worksheets_df['record_count'].sum():,}")
        print()
        print("   Worksheet Details:")
        print("   " + "-" * 76)

        # Group by series
        series_groups = {
            'A': [],
            'B': [],
            'C': [],
            'G': [],
            'S': []
        }

        for _, row in worksheets_df.iterrows():
            worksheet = row['worksheet']
            series = worksheet[0]
            if series in series_groups:
                series_groups[series].append(row)

        for series, rows in series_groups.items():
            if rows:
                print(f"\n   {series}-Series ({len(rows)} worksheets):")
                for row in rows:
                    print(f"      {row['worksheet']}: {row['record_count']:>12,} records")
    else:
        print("   ✗ No worksheets found")
    print()

    # Test specific worksheet queries
    print("5. Testing Specific Worksheet Queries:")
    print("-" * 80)

    test_queries = [
        {
            'name': 'Balance Sheet (G000000)',
            'query': """
                SELECT COUNT(*) as cnt,
                       COUNT(DISTINCT Provider_Number) as providers,
                       COUNT(DISTINCT fiscal_year) as years
                FROM worksheet_g000000
            """,
            'expected': 'Balance sheet data for all providers'
        },
        {
            'name': 'Income Statement (G300000)',
            'query': """
                SELECT COUNT(*) as cnt,
                       COUNT(DISTINCT Provider_Number) as providers,
                       COUNT(DISTINCT fiscal_year) as years
                FROM worksheet_g300000
            """,
            'expected': 'Income statement data'
        },
        {
            'name': 'Statistical Data (S300001)',
            'query': """
                SELECT COUNT(*) as cnt,
                       COUNT(DISTINCT Provider_Number) as providers,
                       COUNT(DISTINCT fiscal_year) as years
                FROM worksheet_s300001
            """,
            'expected': 'Utilization statistics'
        },
        {
            'name': 'Cost Centers (A000000)',
            'query': """
                SELECT COUNT(*) as cnt,
                       COUNT(DISTINCT Provider_Number) as providers,
                       COUNT(DISTINCT fiscal_year) as years
                FROM worksheet_a000000
            """,
            'expected': 'Cost center data'
        }
    ]

    con = manager.get_worksheet_connection()
    success_count = 0

    for test in test_queries:
        try:
            result = con.execute(test['query']).fetchone()
            records, providers, years = result
            print(f"\n   [OK] {test['name']}")
            print(f"        Records: {records:,}")
            print(f"        Providers: {providers}")
            print(f"        Fiscal Years: {years}")
            success_count += 1
        except Exception as e:
            print(f"\n   [FAIL] {test['name']}")
            print(f"          Error: {str(e)}")

    con.close()
    print()

    # Test sample data retrieval
    print("6. Sample Data Retrieval Test:")
    print("-" * 80)

    try:
        con = manager.get_worksheet_connection()

        # Get a sample provider
        sample_provider = con.execute("""
            SELECT Provider_Number, fiscal_year, state_code
            FROM worksheet_g000000
            LIMIT 1
        """).fetchone()

        if sample_provider:
            provider_num, fiscal_year, state_code = sample_provider
            print(f"\n   Testing with Provider: {provider_num}")
            print(f"   Fiscal Year: {fiscal_year}")
            print(f"   State: {state_code}")
            print()

            # Get balance sheet data
            balance_data = con.execute("""
                SELECT
                    line_level1,
                    COUNT(*) as line_items,
                    SUM(CASE WHEN Value IS NOT NULL THEN 1 ELSE 0 END) as values_present
                FROM worksheet_g000000
                WHERE Provider_Number = ?
                  AND fiscal_year = ?
                GROUP BY line_level1
                ORDER BY line_items DESC
                LIMIT 5
            """, [provider_num, fiscal_year]).df()

            print("   Top 5 Balance Sheet Categories:")
            for _, row in balance_data.iterrows():
                category = row['line_level1'] or '(Uncategorized)'
                print(f"      {category}: {row['line_items']} items, {row['values_present']} with values")

            print("\n   [OK] Sample data retrieval successful")
        else:
            print("   [FAIL] No sample data found")

        con.close()
    except Exception as e:
        print(f"   [FAIL] Error retrieving sample data: {str(e)}")

    print()

    # Final summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)

    total_tests = 4
    passed_tests = 0

    if manager.use_worksheets:
        passed_tests += 1
        print(f"[PASS] Database connection established")
    else:
        print(f"[FAIL] Database connection failed")

    if verification['status'] in ['success', 'partial']:
        passed_tests += 1
        print(f"[PASS] Worksheet tables accessible ({verification['tables_accessible']}/{verification['tables_total']})")
    else:
        print(f"[FAIL] Worksheet access verification failed")

    if not worksheets_df.empty:
        passed_tests += 1
        print(f"[PASS] Worksheet metadata retrieved ({len(worksheets_df)} worksheets)")
    else:
        print(f"[FAIL] Failed to retrieve worksheet metadata")

    if success_count == len(test_queries):
        passed_tests += 1
        print(f"[PASS] All {len(test_queries)} test queries executed successfully")
    else:
        print(f"[FAIL] Only {success_count}/{len(test_queries)} test queries succeeded")

    # Overall result
    print()
    print(f"Overall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print()
        print("="*80)
        print("SUCCESS! PHASE 1 COMPLETE - Worksheet database fully connected!")
        print("="*80)
        print()
        print("Next Steps:")
        print("  - Phase 2: Implement Level 2 KPI calculations")
        print("  - Phase 3: Build hierarchical drill-down UI")
        return True
    else:
        print()
        print("="*80)
        print("WARNING: PHASE 1 INCOMPLETE - Some tests failed")
        print("="*80)
        print()
        print("Review errors above and fix before proceeding to Phase 2")
        return False


if __name__ == '__main__':
    success = test_worksheet_connection()
    sys.exit(0 if success else 1)
