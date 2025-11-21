# Current Ratio Card Enhancement

## Overview
Enhanced the Current Ratio KPI card with:
1. **Definition tooltip** - Question mark icon (?) next to KPI name that shows description on hover
2. **Base calculation display** - Shows the actual numbers used in the calculation
3. **Compact number formatting** - Uses K/M/B suffixes to show at most 3 digits with 1 decimal

## Changes Made

### 1. Added Compact Number Formatting Function

**File**: `utils/formatting.py`

Added `format_number_compact()` function that formats numbers with K/M/B suffixes:

```python
def format_number_compact(value):
    """
    Format number with K/M/B suffix, showing at most 3 digits with 1 decimal.

    Examples:
        1_234 -> "1.2K"
        2_345_678 -> "2.3M"
        1_234_567_890 -> "1.2B"
    """
```

**Test Results**:
- All 10 test cases passed
- Handles positive, negative, zero, and decimal values correctly
- Example: $2,310,000 → "$2.3M"

### 2. Enhanced KPI Card Component

**File**: `components/kpi_cards.py`

Modified `create_enhanced_level1_kpi_card()` function:

#### Added Parameters:
- `data_manager` - HospitalDataManager instance for fetching base calculation data

#### New Features:

**A. Tooltip with Definition**
```python
# KPI Name with tooltip
html.H5([
    kpi_name,
    html.Span([
        html.I(className="fas fa-question-circle ms-2",
               id=f"tooltip-target-{kpi_key}",
               style={'fontSize': '0.8rem', 'color': '#6c757d', 'cursor': 'pointer'})
    ]),
], ...),
dbc.Tooltip(
    description,
    target=f"tooltip-target-{kpi_key}",
    placement="top"
)
```

**B. Base Calculation Display** (for Current_Ratio)
```python
# Fetch base calculation components
if kpi_key == 'Current_Ratio' and data_manager and ccn and fiscal_year:
    query = """
    SELECT Current_Assets, Current_Liabilities
    FROM kpi_data
    WHERE Provider_Number = '{ccn}'
    AND Fiscal_Year = {fiscal_year}
    """
    result = data_manager.query(query)

    # Format with compact notation
    assets_fmt = format_number_compact(current_assets)
    liabilities_fmt = format_number_compact(current_liabilities)
    calculation_display = f"Current assets (${assets_fmt}) ÷ Current liabilities (${liabilities_fmt})"
```

**C. Display Calculation Below KPI Value**
```python
# Calculation Display (if available)
html.Div([
    html.P(calculation_display, className="text-muted mb-3",
           style={'fontSize': '0.85rem', 'fontStyle': 'italic'})
]) if calculation_display else html.Div(),
```

### 3. Updated Dashboard Callback

**File**: `callbacks/dashboard_callbacks.py`

Updated the card creation call to pass `data_manager`:

```python
card = create_enhanced_level1_kpi_card(
    # ... existing parameters ...
    data_manager=data_manager  # NEW: Pass data_manager for base calculation data
)
```

## Visual Result

### Current Ratio Card Now Shows:

**Before:**
```
Current Ratio (?)                           [tooltip on hover]
1.87
↑ 5.2%

Short-term liquidity. Ability to meet current obligations with current assets.
```

**After:**
```
Current Ratio (?)                           [tooltip on hover: Short-term liquidity...]
1.87
↑ 5.2%
Current assets ($2.3M) ÷ Current liabilities ($12.3M)

[rest of card...]
```

## Example Values

For a hospital with:
- Current Assets: $2,310,000
- Current Liabilities: $12,320,000
- Current Ratio: 0.19

The display will show:
```
Current assets ($2.3M) ÷ Current liabilities ($12.3M)
```

## Benefits

1. **Better Understanding** - Users can see the definition without cluttering the interface
2. **Transparency** - Shows exactly what numbers are being used in the calculation
3. **Readability** - Compact format (2.3M vs 2,310,000) is easier to scan and compare
4. **Consistent Formatting** - Shows at most 3 digits with 1 decimal for easy reading

## Testing

### Unit Test for Formatting
Created `test_compact_formatting.py` with 10 test cases:
```
PASS            1234 ->       1.2K
PASS         2345678 ->       2.3M
PASS      1234567890 ->       1.2B
PASS             123 ->        123
PASS            12.5 ->         12
PASS             2.3 ->        2.3
PASS         2310000 ->       2.3M
PASS        12320000 ->      12.3M
PASS               0 ->          0
PASS           -1234 ->      -1.2K
```

### Manual Testing
1. Start dashboard: `python dashboard.py`
2. Open browser: http://127.0.0.1:8050
3. Select any hospital
4. Look for Current Ratio card:
   - Hover over (?) icon to see tooltip
   - See calculation with base numbers below value
   - Verify compact formatting (K/M/B)

## Future Enhancements

This pattern can be extended to other KPIs:

### Net Income Margin
```
Net Income ($1.5M) ÷ Total Revenue ($50.2M)
```

### Days in AR
```
Net Patient AR ($8.3M) ÷ (Net Patient Revenue ($100.5M) ÷ 365)
```

### Operating Expense per Adjusted Discharge
```
Total Operating Expenses ($45.2M) ÷ Adjusted Discharges (5,234)
```

To add calculation display for other KPIs:

1. Update the condition in `create_enhanced_level1_kpi_card()`:
```python
if kpi_key in ['Current_Ratio', 'Net_Income_Margin', 'AR_Days', ...]:
    # Fetch appropriate base columns for each KPI
    # Format and display calculation
```

2. Add mapping of KPI keys to their base columns:
```python
KPI_BASE_COLUMNS = {
    'Current_Ratio': ['Current_Assets', 'Current_Liabilities'],
    'Net_Income_Margin': ['Net_Income', 'Total_Revenue'],
    'AR_Days': ['Net_Patient_AR', 'Net_Patient_Revenue'],
    # ... etc
}
```

## Files Modified

1. `utils/formatting.py` - Added `format_number_compact()` function
2. `components/kpi_cards.py` - Enhanced `create_enhanced_level1_kpi_card()` with tooltip and calculation
3. `callbacks/dashboard_callbacks.py` - Pass `data_manager` to card creation

## Files Created

1. `test_compact_formatting.py` - Unit tests for compact number formatting
2. `CURRENT_RATIO_ENHANCEMENT.md` - This documentation file

---

**Date**: November 21, 2025
**Status**: ✅ Complete and tested
**Impact**: Improved user experience for Current Ratio KPI card with better context and readability
