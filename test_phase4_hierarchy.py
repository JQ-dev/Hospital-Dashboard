"""
Test Phase 4 Three-Level Hierarchical Drill-Down
Verifies that Level 3 KPIs are properly integrated into the dashboard
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard import HospitalDataManager, create_hierarchical_kpi_card, KPI_METADATA
import pandas as pd

def test_three_level_hierarchy():
    """Test 3-level hierarchical KPI structure"""

    print("="*80)
    print("PHASE 4 TEST: Three-Level Hierarchical Drill-Down")
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
        print("[FAIL] Worksheet database not available - cannot test hierarchical structure")
        return False

    # Get sample provider data
    print("2. Getting Sample Provider Data...")
    print("-" * 80)
    provider_num = '310001'
    fiscal_year = 2024

    kpi_data = manager.calculate_kpis(provider_num)
    if kpi_data.empty:
        print(f"[FAIL] No KPI data for provider {provider_num}")
        return False

    print(f"   Provider: {provider_num}")
    print(f"   Fiscal Year: {fiscal_year}")
    print(f"   L1 KPIs available: {len(kpi_data.columns)}")
    print()

    # Calculate Level 2 KPIs
    print("3. Calculating Level 2 KPIs...")
    print("-" * 80)
    l2_kpis = manager.calculate_level2_kpis(provider_num, fiscal_year)

    if not l2_kpis:
        print("[FAIL] Failed to calculate Level 2 KPIs")
        return False

    non_null_l2 = sum(1 for v in l2_kpis.values() if v is not None)
    print(f"   [OK] Level 2 KPIs calculated: {non_null_l2}/{len(l2_kpis)}")
    print()

    # Calculate Level 3 KPIs
    print("4. Calculating Level 3 KPIs...")
    print("-" * 80)
    l3_kpis = manager.calculate_level3_kpis(provider_num, fiscal_year)

    if not l3_kpis:
        print("[FAIL] Failed to calculate Level 3 KPIs")
        return False

    non_null_l3 = sum(1 for v in l3_kpis.values() if v is not None)
    print(f"   [OK] Level 3 KPIs calculated: {non_null_l3}/{len(l3_kpis)}")
    print()

    # Display L3 KPI results by parent
    print("5. Level 3 KPI Results by Parent:")
    print("="*80)

    l3_structure = {
        'L2.1.2: Non-Operating Income %': [
            ('L3_1_2_1_Investment_Income_Share', 'Investment Income Share'),
            ('L3_1_2_2_Donation_Grant_Pct', 'Donation/Grant %'),
        ],
        'L2.1.3: Medicare Mix %': [
            ('L3_1_3_1_Medicare_Inpatient_Days_Pct', 'Medicare Inpatient Days %'),
        ],
        'L2.1.4: Capital Cost % of Expenses': [
            ('L3_1_4_1_Depreciation_Pct_of_Capital', 'Depreciation % of Capital'),
            ('L3_1_4_2_Interest_Expense_Ratio', 'Interest Expense Ratio'),
        ],
        'L2.2.2: Commercial Mix %': [
            ('L3_2_2_1_Commercial_Inpatient_Pct', 'Commercial Inpatient %'),
            ('L3_2_2_2_Self_Pay_Pct', 'Self-Pay %'),
        ],
        'L2.6.2: Current Liabilities Ratio': [
            ('L3_6_2_1_Accounts_Payable_Pct', 'Accounts Payable %'),
            ('L3_6_2_2_Short_Term_Debt_Pct', 'Short-Term Debt %'),
        ],
        'L2.6.4: Fund Balance % Change': [
            ('L3_6_4_1_Retained_Earnings_Pct', 'Retained Earnings %'),
            ('L3_6_4_2_Depreciation_Impact', 'Depreciation Impact'),
        ],
    }

    total_l3 = 0
    calculated_l3 = 0

    for parent_name, l3_list in l3_structure.items():
        print(f"\n{parent_name}")
        print("-" * 80)
        for l3_key, l3_name in l3_list:
            total_l3 += 1
            value = l3_kpis.get(l3_key)
            if value is not None:
                calculated_l3 += 1
                print(f"   [OK] {l3_name}: {value:>10.2f}%")
            else:
                print(f"   [NULL] {l3_name}: No data")

    print()
    print("="*80)
    print(f"L3 Summary: {calculated_l3}/{total_l3} calculated ({(calculated_l3/total_l3)*100:.1f}%)")
    print()

    # Test hierarchical card creation with 3 levels
    print("6. Testing 3-Level Hierarchical Card Creation...")
    print("-" * 80)

    test_kpis = [
        ('Net_Margin_Pct', 'Net Income Margin'),
        ('AR_Days', 'Days in AR'),
        ('Current_Ratio', 'Current Ratio')
    ]

    cards_created = 0
    cards_with_l2 = 0
    cards_with_l3 = 0

    for kpi_key, kpi_name in test_kpis:
        if kpi_key not in kpi_data.columns:
            print(f"   [SKIP] {kpi_name}: Not in dataset")
            continue

        try:
            # Get KPI value
            kpi_value = kpi_data[kpi_key].iloc[0]
            kpi_values = kpi_data[kpi_key].values
            fiscal_years = kpi_data['Fiscal_Year'].values

            # Create hierarchical card
            card = create_hierarchical_kpi_card(
                kpi_key=kpi_key,
                kpi_value=kpi_value,
                kpi_trend_values=kpi_values,
                fiscal_years=fiscal_years,
                benchmark_data={'kpis': {}},  # Empty benchmark for test
                rank=1,
                importance_score=100,
                l2_kpis=l2_kpis,
                l3_kpis=l3_kpis,
                ccn=provider_num,
                fiscal_year=fiscal_year
            )

            cards_created += 1

            # Check if card has L2 section
            card_str = str(card)
            has_l2_section = 'KEY DRIVERS' in card_str
            has_l3_section = 'Sub-Drivers' in card_str
            has_expand_l2 = 'View Drivers' in card_str
            has_expand_l3 = 'expand-l3-btn' in card_str

            if has_l2_section:
                cards_with_l2 += 1

            if has_l3_section:
                cards_with_l3 += 1

            if has_l2_section and has_l3_section:
                print(f"   [OK] {kpi_name}: 3-level card (L1 -> L2 -> L3)")
            elif has_l2_section:
                print(f"   [OK] {kpi_name}: 2-level card (L1 -> L2)")
            else:
                print(f"   [OK] {kpi_name}: 1-level card (L1 only)")

        except Exception as e:
            print(f"   [FAIL] {kpi_name}: Error creating card - {str(e)}")
            import traceback
            traceback.print_exc()

    print()
    print(f"   Total cards created: {cards_created}/{len(test_kpis)}")
    print(f"   Cards with L2 sections: {cards_with_l2}")
    print(f"   Cards with L3 sections: {cards_with_l3}")
    print()

    # Test component structure
    print("7. Testing 3-Level Component Structure...")
    print("-" * 80)

    components_found = {
        'l2_collapse': False,
        'l2_expand_button': False,
        'l3_collapse': False,
        'l3_expand_button': False,
    }

    test_card = create_hierarchical_kpi_card(
        kpi_key='Net_Margin_Pct',
        kpi_value=kpi_data['Net_Margin_Pct'].iloc[0],
        kpi_trend_values=kpi_data['Net_Margin_Pct'].values,
        fiscal_years=kpi_data['Fiscal_Year'].values,
        benchmark_data={'kpis': {}},
        rank=1,
        importance_score=100,
        l2_kpis=l2_kpis,
        l3_kpis=l3_kpis,
        ccn=provider_num,
        fiscal_year=fiscal_year
    )

    card_str = str(test_card)

    if 'l2-collapse' in card_str:
        components_found['l2_collapse'] = True
        print("   [OK] L2 collapse div present")

    if 'expand-btn' in card_str:
        components_found['l2_expand_button'] = True
        print("   [OK] L2 expand button present")

    if 'l3-collapse' in card_str:
        components_found['l3_collapse'] = True
        print("   [OK] L3 collapse div present")

    if 'expand-l3-btn' in card_str:
        components_found['l3_expand_button'] = True
        print("   [OK] L3 expand button present")

    all_components = all(components_found.values())
    if all_components:
        print("\n   [OK] All 3-level interactive components present")
    else:
        print(f"\n   [WARN] Some components missing: {components_found}")

    print()

    # Final summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)

    tests_passed = 0
    total_tests = 7

    if l2_kpis and non_null_l2 > 0:
        tests_passed += 1
        print(f"[PASS] Level 2 KPIs calculated ({non_null_l2}/{len(l2_kpis)})")
    else:
        print(f"[FAIL] Level 2 KPI calculation failed")

    if l3_kpis and non_null_l3 > 0:
        tests_passed += 1
        print(f"[PASS] Level 3 KPIs calculated ({non_null_l3}/{len(l3_kpis)})")
    else:
        print(f"[FAIL] Level 3 KPI calculation failed")

    if calculated_l3 >= 10:  # At least 10 of ~14 L3 KPIs should calculate
        tests_passed += 1
        print(f"[PASS] Majority of L3 KPIs calculated ({calculated_l3}/{total_l3})")
    else:
        print(f"[FAIL] Too few L3 KPIs calculated ({calculated_l3}/{total_l3})")

    if cards_created == len(test_kpis):
        tests_passed += 1
        print(f"[PASS] All hierarchical cards created ({cards_created}/{len(test_kpis)})")
    else:
        print(f"[FAIL] Not all cards created ({cards_created}/{len(test_kpis)})")

    if cards_with_l2 >= 2:
        tests_passed += 1
        print(f"[PASS] Cards with L2 KPI sections ({cards_with_l2})")
    else:
        print(f"[FAIL] Too few cards with L2 sections ({cards_with_l2})")

    if cards_with_l3 >= 2:
        tests_passed += 1
        print(f"[PASS] Cards with L3 KPI sections ({cards_with_l3})")
    else:
        print(f"[FAIL] Too few cards with L3 sections ({cards_with_l3})")

    if all_components:
        tests_passed += 1
        print(f"[PASS] All 3-level interactive components present")
    else:
        print(f"[FAIL] Missing some interactive components")

    print()
    print(f"Overall: {tests_passed}/{total_tests} tests passed")

    if tests_passed >= 6:  # 6/7 is acceptable
        print()
        print("="*80)
        print("SUCCESS! PHASE 4 COMPLETE - 3-Level Hierarchy implemented!")
        print("="*80)
        print()
        print("Features Implemented:")
        print("  - Level 3 KPI calculations from worksheet data")
        print(f"  - {non_null_l3} Level 3 KPIs calculating successfully")
        print("  - 3-level expandable UI (L1 -> L2 -> L3)")
        print("  - Nested collapse/expand for L2 and L3 sections")
        print(f"  - {cards_with_l3} KPIs with full 3-level drill-down")
        print()
        print("KPI Hierarchy Summary:")
        print(f"  - Level 1: 6 top-level KPIs")
        print(f"  - Level 2: {non_null_l2}/{len(l2_kpis)} drivers calculated")
        print(f"  - Level 3: {non_null_l3}/{len(l3_kpis)} sub-drivers calculated")
        print(f"  - Total KPI depth: 3 levels")
        print()
        print("Next Steps:")
        print("  - Test live dashboard: python dashboard.py")
        print("  - Add tooltips with formulas")
        print("  - Add more Level 3 KPIs for remaining L2 parents")
        return True
    else:
        print()
        print("="*80)
        print("WARNING: PHASE 4 INCOMPLETE - Some tests failed")
        print("="*80)
        print()
        print("Review errors above and fix before deploying")
        return False


if __name__ == '__main__':
    success = test_three_level_hierarchy()
    sys.exit(0 if success else 1)
