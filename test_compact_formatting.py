"""
Test script for format_number_compact function
"""

from utils.formatting import format_number_compact

# Test cases
test_values = [
    (1_234, "1.2K"),
    (2_345_678, "2.3M"),
    (1_234_567_890, "1.2B"),
    (123, "123"),
    (12.5, "12"),
    (2.3, "2.3"),
    (2_310_000, "2.3M"),
    (12_320_000, "12.3M"),
    (0, "0"),
    (-1_234, "-1.2K"),
]

print("Testing format_number_compact function:")
print("=" * 60)

all_passed = True
for value, expected in test_values:
    result = format_number_compact(value)
    status = "PASS" if result == expected else "FAIL"
    if result != expected:
        all_passed = False
    print(f"{status} {value:>15} -> {result:>10} (expected: {expected})")

print("=" * 60)
if all_passed:
    print("All tests passed!")
else:
    print("Some tests failed!")

# Test with real Current Ratio data format
print("\nExample for Current Ratio calculation:")
print("=" * 60)
current_assets = 2_310_000  # $2.31M
current_liabilities = 12_320_000  # $12.32M

assets_fmt = format_number_compact(current_assets)
liabilities_fmt = format_number_compact(current_liabilities)

calculation = f"Current assets (${assets_fmt}) ÷ Current liabilities (${liabilities_fmt})"
print(calculation)
print(f"Result: {current_assets / current_liabilities:.2f}")
