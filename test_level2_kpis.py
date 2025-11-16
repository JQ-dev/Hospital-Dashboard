"""
Test Level 2 KPI Calculations
Tests Phase 2 implementation - calculating Level 2 KPIs from worksheet data
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard import HospitalDataManager
import pandas as pd

def test_level2_kpis():
    """Test Level 2 KPI calculations"""

    print("="*80)
    print("PHASE 2 TEST: Level 2 KPI Calculations")
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

    if not manager.use_worksheets:
        print("[FAIL] Worksheet database not available")
        return False

    # Get a sample provider
    print("2. Selecting Sample Provider...")
    print("-" * 80)
    con = manager.get_worksheet_connection()
    sample_provider = con.execute("""
        SELECT DISTINCT Provider_Number, fiscal_year, state_code
        FROM worksheet_g000000
        WHERE Provider_Number = '310001'
        ORDER BY fiscal_year DESC
        LIMIT 1
    """).fetchone()

    if not sample_provider:
        print("[FAIL] No sample provider found")
        con.close()
        return False

    provider_num, fiscal_year, state_code = sample_provider
    print(f"   Provider: {provider_num}")
    print(f"   Fiscal Year: {fiscal_year}")
    print(f"   State: {state_code}")
    con.close()
    print()

    # Calculate Level 2 KPIs
    print("3. Calculating Level 2 KPIs...")
    print("-" * 80)
    l2_kpis = manager.calculate_level2_kpis(provider_num, fiscal_year)

    if not l2_kpis:
        print("[FAIL] Failed to calculate Level 2 KPIs")
        return False

    print(f"   [OK] Calculated {len(l2_kpis)} Level 2 KPIs")
    print()

    # Display results by Level 1 parent
    print("4. Level 2 KPI Results:")
    print("="*80)

    # L1.1 Drivers: Net Income Margin
    print("\nL1.1 DRIVERS: Net Income Margin")
    print("-" * 80)

    kpi_groups = {
        'L1.1 DRIVERS: Net Income Margin': [
            ('L2_1_2_Non_Operating_Income_Pct', 'L2.1.2: Non-Operating Income %', '%'),
            ('L2_1_3_Payer_Mix_Medicare_Pct', 'L2.1.3: Payer Mix - Medicare %', '%'),
            ('L2_1_4_Capital_Cost_Pct_of_Expenses', 'L2.1.4: Capital Cost % of Expenses', '%'),
        ],
        'L1.2 DRIVERS: Days in AR': [
            ('L2_2_2_Payer_Mix_Commercial_Pct', 'L2.2.2: Payer Mix - Commercial %', '%'),
        ],
        'L1.3 DRIVERS: Operating Expense per Discharge': [
            ('L2_3_4_Case_Mix_Index', 'L2.3.4: Case Mix Index', 'index'),
        ],
        'L1.5 DRIVERS: Bad Debt + Charity': [
            ('L2_5_1_Charity_Care_Charge_Ratio', 'L2.5.1: Charity Care Charge Ratio', '%'),
            ('L2_5_2_Bad_Debt_Recovery_Rate', 'L2.5.2: Bad Debt Recovery Rate', '%'),
            ('L2_5_3_Uninsured_Patient_Pct', 'L2.5.3: Uninsured Patient %', '%'),
            ('L2_5_4_Medicaid_Shortfall_Pct', 'L2.5.4: Medicaid Shortfall %', '%'),
        ],
        'L1.6 DRIVERS: Current Ratio': [
            ('L2_6_2_Current_Liabilities_Ratio', 'L2.6.2: Current Liabilities Ratio', '%'),
            ('L2_6_4_Fund_Balance_Pct_Change', 'L2.6.4: Fund Balance % Change', '%'),
        ]
    }

    total_kpis = 0
    calculated_kpis = 0
    null_kpis = 0

    for group_name, kpis in kpi_groups.items():
        print(f"\n{group_name}")
        print("-" * 80)

        for kpi_key, kpi_name, unit in kpis:
            total_kpis += 1
            value = l2_kpis.get(kpi_key)

            if value is not None:
                calculated_kpis += 1
                if unit == '%':
                    print(f"   [OK] {kpi_name}: {value:>10.2f}%")
                else:
                    print(f"   [OK] {kpi_name}: {value:>10.4f}")
            else:
                null_kpis += 1
                print(f"   [NULL] {kpi_name}: No data available")

    print()
    print("="*80)

    # Summary
    print("\n5. Calculation Summary:")
    print("-" * 80)
    print(f"   Total Level 2 KPIs implemented: {total_kpis}")
    print(f"   Successfully calculated: {calculated_kpis}")
    print(f"   Null/No data: {null_kpis}")
    print(f"   Success rate: {(calculated_kpis/total_kpis)*100:.1f}%")
    print()

    # Test multi-year capability
    print("6. Testing Multi-Year Calculation:")
    print("-" * 80)

    years_tested = 0
    years_success = 0

    for year in [2020, 2021, 2022, 2023, 2024]:
        l2_year = manager.calculate_level2_kpis(provider_num, year)
        if l2_year:
            years_tested += 1
            non_null = sum(1 for v in l2_year.values() if v is not None)
            if non_null > 0:
                years_success += 1
                print(f"   [OK] Year {year}: {non_null}/{len(l2_year)} KPIs calculated")
            else:
                print(f"   [WARN] Year {year}: No KPIs calculated (may not have data)")
        else:
            print(f"   [FAIL] Year {year}: Calculation failed")

    print()

    # Test multiple providers
    print("7. Testing Multiple Providers:")
    print("-" * 80)

    test_providers = con = manager.get_worksheet_connection()
    provider_list = con.execute("""
        SELECT DISTINCT Provider_Number
        FROM worksheet_g000000
        LIMIT 5
    """).fetchall()
    con.close()

    providers_tested = 0
    providers_success = 0

    for (provider,) in provider_list:
        l2_provider = manager.calculate_level2_kpis(provider, fiscal_year)
        if l2_provider:
            providers_tested += 1
            non_null = sum(1 for v in l2_provider.values() if v is not None)
            if non_null > 0:
                providers_success += 1
                print(f"   [OK] Provider {provider}: {non_null}/{len(l2_provider)} KPIs calculated")
            else:
                print(f"   [WARN] Provider {provider}: No KPIs calculated")
        else:
            print(f"   [FAIL] Provider {provider}: Calculation failed")

    print()

    # Final summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)

    tests_passed = 0
    total_tests = 4

    if l2_kpis:
        tests_passed += 1
        print(f"[PASS] Level 2 KPI calculation method works")
    else:
        print(f"[FAIL] Level 2 KPI calculation failed")

    if calculated_kpis >= 8:  # At least 8 of 11 KPIs should calculate
        tests_passed += 1
        print(f"[PASS] Majority of KPIs calculated ({calculated_kpis}/{total_kpis})")
    else:
        print(f"[FAIL] Too few KPIs calculated ({calculated_kpis}/{total_kpis})")

    if years_success >= 3:  # At least 3 years should work
        tests_passed += 1
        print(f"[PASS] Multi-year calculation works ({years_success} years)")
    else:
        print(f"[FAIL] Multi-year calculation issues ({years_success} years)")

    if providers_success >= 3:  # At least 3 providers should work
        tests_passed += 1
        print(f"[PASS] Multi-provider calculation works ({providers_success} providers)")
    else:
        print(f"[FAIL] Multi-provider calculation issues ({providers_success} providers)")

    print()
    print(f"Overall: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print()
        print("="*80)
        print("SUCCESS! PHASE 2 COMPLETE - Level 2 KPIs implemented!")
        print("="*80)
        print()
        print(f"Implemented KPIs:")
        print(f"  - L1.1 drivers: 3 KPIs (Non-Op Income, Medicare Mix, Capital Cost)")
        print(f"  - L1.2 drivers: 1 KPI (Commercial Mix)")
        print(f"  - L1.3 drivers: 1 KPI (Case Mix Index)")
        print(f"  - L1.5 drivers: 4 KPIs (Charity, Bad Debt, Uninsured, Medicaid)")
        print(f"  - L1.6 drivers: 2 KPIs (Current Liabilities, Fund Balance)")
        print(f"  Total: {total_kpis} Level 2 KPIs")
        print()
        print("Next Steps:")
        print("  - Phase 3: Build hierarchical drill-down UI")
        print("  - Phase 4: Implement Level 3 KPIs")
        return True
    else:
        print()
        print("="*80)
        print("WARNING: PHASE 2 INCOMPLETE - Some tests failed")
        print("="*80)
        print()
        print("Review errors above and fix before proceeding to Phase 3")
        return False


if __name__ == '__main__':
    success = test_level2_kpis()
    sys.exit(0 if success else 1)
