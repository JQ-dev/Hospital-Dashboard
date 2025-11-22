"""Test that peer counts follow correct hierarchy"""
from data.data_manager import HospitalDataManager

dm = HospitalDataManager()

# Test with a hospital from state 14 (has lots of data)
test_ccn = '140001'
fiscal_year = 2021

print(f"Testing peer count hierarchy for CCN {test_ccn}, Year {fiscal_year}")
print("=" * 80)

# Get all benchmark levels
benchmarks = {
    'National': dm.get_benchmarks(test_ccn, fiscal_year, 'National'),
    'Hospital_Type': dm.get_benchmarks(test_ccn, fiscal_year, 'Hospital_Type'),
    'State': dm.get_benchmarks(test_ccn, fiscal_year, 'State'),
    'State_Hospital_Type': dm.get_benchmarks(test_ccn, fiscal_year, 'State_Hospital_Type')
}

print("\nPeer counts by benchmark level:")
print("-" * 80)
for level, data in benchmarks.items():
    count = data.get('provider_count', 0)
    group = data.get('group_name', 'Unknown')
    print(f"{level:20s}: {count:4d} peers  ({group})")

print("\n" + "=" * 80)
print("HIERARCHY CHECK:")
print("=" * 80)

national_count = benchmarks['National']['provider_count']
hospital_type_count = benchmarks['Hospital_Type']['provider_count']
state_count = benchmarks['State']['provider_count']
state_hospital_type_count = benchmarks['State_Hospital_Type']['provider_count']

print(f"\nNational:           {national_count:4d} peers (ALL hospitals)")
print(f"Hospital_Type:      {hospital_type_count:4d} peers (subset by type)")
print(f"State:              {state_count:4d} peers (subset by state)")
print(f"State_Hospital_Type: {state_hospital_type_count:4d} peers (subset by both)")

print("\nExpected hierarchy: National >= State >= State_Hospital_Type")
print("Expected hierarchy: National >= Hospital_Type >= State_Hospital_Type")

# Check if hierarchy is correct
errors = []
if national_count < state_count:
    errors.append(f"❌ National ({national_count}) < State ({state_count})")
if national_count < hospital_type_count:
    errors.append(f"❌ National ({national_count}) < Hospital_Type ({hospital_type_count})")
if state_count < state_hospital_type_count:
    errors.append(f"❌ State ({state_count}) < State_Hospital_Type ({state_hospital_type_count})")
if hospital_type_count < state_hospital_type_count:
    errors.append(f"❌ Hospital_Type ({hospital_type_count}) < State_Hospital_Type ({state_hospital_type_count})")

if errors:
    print("\nERRORS FOUND:")
    for error in errors:
        print(f"  {error}")
else:
    print("\n✓ Hierarchy is CORRECT!")
    print("  National >= State >= State_Hospital_Type ✓")
    print("  National >= Hospital_Type >= State_Hospital_Type ✓")
