# Hospital KPI Hierarchy Documentation

## Overview

This document describes the three-level KPI hierarchy implemented in the Hospital Dashboard, based on HCRIS (Hospital Cost Report Information System) data from CMS Form 2552-10.

## Hierarchy Structure

The KPI system is organized into three levels:

- **Level 1 (6 KPIs)**: Top-level strategic metrics focusing on financial health, efficiency, and sustainability
- **Level 2 (24 KPIs)**: Driver metrics - key components or influencers of Level 1 KPIs (4 per Level 1 KPI)
- **Level 3 (48 KPIs)**: Sub-driver metrics - granular breakdowns of Level 2 KPIs (2 per Level 2 KPI)

**Total KPIs: 78** across all three levels

## Level 1 KPIs (Strategic Metrics)

### 1. Net Income Margin
- **Formula**: (Net Income) ÷ (Total Revenue)
- **HCRIS Reference**: (G-3 Line 29) ÷ (G-3 Line 3)
- **Category**: Profitability
- **Target Range**: 2-4%
- **Why It Matters**: Reflects overall profitability and financial sustainability

### 2. Days in Net Patient Accounts Receivable (AR Days)
- **Formula**: (Net Patient AR) ÷ (Net Patient Revenue / 365)
- **HCRIS Reference**: (G Balance Sheet Current Assets Net Patient AR) ÷ (G-3 Line 3 ÷ 365)
- **Category**: Revenue Cycle
- **Target Range**: 40-50 days
- **Why It Matters**: Measures cash cycle efficiency and revenue collection speed

### 3. Operating Expense per Adjusted Discharge
- **Formula**: (Total Operating Expenses) ÷ (Adjusted Discharges)
- **HCRIS Reference**: (G-3 Line 25) ÷ [(S-3 Pt I Line 1 Col 1 × CMI) + (S-3 Pt I Line 15 Col 1 × 0.35)]
- **Category**: Cost Management
- **Target Range**: $8,000-$12,000
- **Why It Matters**: Gauges per-unit cost control efficiency

### 4. Medicare Cost-to-Charge Ratio (CCR)
- **Formula**: (Total Costs) ÷ (Total Charges)
- **HCRIS Reference**: (C Pt I Col 5 Sum) ÷ (C Pt I Col 8 Sum)
- **Category**: Efficiency
- **Target Range**: 0.2-0.4
- **Why It Matters**: Proxies reimbursement risk and cost efficiency

### 5. Bad Debt + Charity as % of Net Revenue
- **Formula**: (Bad Debt + Charity Care) ÷ (Net Revenue - Provisions)
- **HCRIS Reference**: (S-10 Line 29 Col 3 + Line 23 Col 3) ÷ (G-3 Line 3 - Provisions)
- **Category**: Revenue Cycle
- **Target Range**: 3-8%
- **Why It Matters**: Measures uncompensated care burden

### 6. Current Ratio (Unrestricted)
- **Formula**: (Current Assets Unrestricted) ÷ (Current Liabilities)
- **HCRIS Reference**: (G Balance Sheet Line 1-12 Col 3 Sum Unrestricted) ÷ (G Line 46-58 Col 3 Sum)
- **Category**: Liquidity
- **Target Range**: 1.5-2.5
- **Why It Matters**: Assesses short-term liquidity and ability to meet obligations

## Level 2 KPIs (Driver Metrics)

Each Level 1 KPI has 4 Level 2 driver KPIs that explain what influences the parent metric. For example:

### Net Income Margin → Level 2 Drivers:
1. **Operating Expense Ratio** - Higher expenses directly erode net income
2. **Non-Operating Income %** - Boosts net income beyond core operations
3. **Payer Mix - Medicare %** - Affects revenue stability and margins
4. **Capital Cost % of Expenses** - High capital costs eat into margins if not managed

### AR Days → Level 2 Drivers:
1. **Denial Rate** - Denials delay collections
2. **Payer Mix - Commercial %** - Slower payers increase AR days
3. **Billing Efficiency Ratio** - Inefficient billing prolongs AR
4. **Collection Rate** - Poor collections inflate AR days

*See kpi_hierarchy_config.py for complete Level 2 KPI specifications.*

## Level 3 KPIs (Sub-Driver Metrics)

Each Level 2 KPI has 2 Level 3 sub-drivers that provide granular breakdowns. For example:

### Operating Expense Ratio → Level 3 Sub-Drivers:
1. **FTE per Bed** - Staff intensity indicator
2. **Salary % of Total Expenses** - Labor cost intensity

### Denial Rate → Level 3 Sub-Drivers:
1. **Medicare Denial %** - Medicare-specific denial rate
2. **Non-Medicare Adjustment %** - Non-Medicare adjustments as % of revenue

*See kpi_hierarchy_config.py for complete Level 3 KPI specifications.*

## Implementation Status

### Currently Calculated (Available Data)
The following KPIs are actively calculated from available parquet data:

**Level 1:**
- Net Income Margin (approximated from Net_Margin_Pct)
- AR Days
- Current Ratio

**Level 2:**
- Operating Expense Ratio
- Cash Equivalents % of Assets
- Current Liabilities Ratio
- Fund Balance % Change
- Charge Inflation Rate (approximated from revenue growth)
- Utilization Mix (approximated from revenue mix)

**Level 3:**
- Retained Earnings %

### Placeholder KPIs (Pending HCRIS Data Integration)
The following KPIs require additional HCRIS worksheet data not yet integrated:

**Pending Data Sources:**
- Worksheet S-3: Patient days, FTEs, salaries, discharges, case mix
- Worksheet E: Claims and denials data
- Worksheet C: Cost-to-charge data
- Worksheet A: Detailed expense breakdowns
- Worksheet S-10: Charity care and bad debt
- Worksheet G-1: Cash flow statement
- Worksheet D: Revenue details by payer

These KPIs are defined in the hierarchy with `None` values and will be populated when the corresponding HCRIS data becomes available.

## Using the KPI Hierarchy

### Accessing KPIs Programmatically

```python
from kpi_hierarchy_config import (
    KPI_HIERARCHY,
    KPI_METADATA,
    get_level_1_kpis,
    get_level_2_kpis,
    get_level_3_kpis,
    get_kpi_lineage
)

# Get all Level 1 KPIs
level_1 = get_level_1_kpis()
print(f"Level 1 KPIs: {list(level_1.keys())}")

# Get Level 2 KPIs for a specific Level 1 KPI
level_2 = get_level_2_kpis('Net_Income_Margin')
print(f"Drivers of Net Income Margin: {list(level_2.keys())}")

# Get Level 3 KPIs for a specific Level 2 KPI
level_3 = get_level_3_kpis('Net_Income_Margin', 'Operating_Expense_Ratio')
print(f"Sub-drivers of Operating Expense Ratio: {list(level_3.keys())}")

# Get lineage of any KPI
lineage = get_kpi_lineage('FTE_per_Bed')
print(f"FTE_per_Bed is Level {lineage['level']}")
print(f"Parent L1: {lineage['parent_l1']}, Parent L2: {lineage['parent_l2']}")
```

### Accessing KPI Metadata

```python
# Get metadata for any KPI (flat dictionary)
from kpi_hierarchy_config import KPI_METADATA

kpi_meta = KPI_METADATA['Net_Income_Margin']
print(f"Name: {kpi_meta['name']}")
print(f"Unit: {kpi_meta['unit']}")
print(f"Format: {kpi_meta['format']}")
print(f"Target Range: {kpi_meta['target_range']}")
print(f"Description: {kpi_meta['description']}")
```

### Calculating KPIs

KPIs are calculated in the `HospitalDataManager.calculate_kpis()` method in `dashboard.py`:

```python
from dashboard import data_manager

# Calculate KPIs for a hospital
ccn = "050146"  # Example CCN
kpi_df = data_manager.calculate_kpis(ccn)

# Access specific KPIs
latest_year = kpi_df.iloc[0]
print(f"Net Income Margin: {latest_year['Net_Income_Margin']:.1f}%")
print(f"AR Days: {latest_year['AR_Days']:.0f}")
print(f"Current Ratio: {latest_year['Current_Ratio']:.2f}")
```

## Data Architecture

### File Structure
```
Hospital-Dashboard/
├── dashboard.py                    # Main dashboard application
├── kpi_hierarchy_config.py        # KPI hierarchy definitions
├── to_do.txt                       # Original requirements specification
└── KPI_HIERARCHY_DOCUMENTATION.md # This file
```

### KPI Configuration Structure

Each KPI in the hierarchy includes:
- `level`: 1, 2, or 3
- `name`: Display name
- `category`: Functional category (e.g., Profitability, Liquidity)
- `unit`: Unit of measurement (%, $, ratio, days, etc.)
- `format`: Python format string for display
- `higher_is_better`: Boolean indicating direction
- `target_range`: Tuple of (min, max) target values
- `impact_score`: Importance rating (1-10)
- `ease_of_change`: How easily influenced (1-10)
- `description`: What the KPI measures
- `formula_description`: Plain English formula
- `hcris_reference`: HCRIS worksheet reference
- `improvement_levers`: List of actionable improvements
- `why_affects_parent`: (Level 2/3 only) How it influences parent KPI

## Future Enhancements

### Phase 1: Data Integration
1. Integrate HCRIS Worksheet S-3 (utilization and staffing)
2. Integrate HCRIS Worksheet E (claims and denials)
3. Integrate HCRIS Worksheet C (cost-to-charge ratios)

### Phase 2: Advanced Analytics
1. Implement drill-down UI for hierarchical exploration
2. Add root-cause analysis highlighting underperforming sub-drivers
3. Create interactive dependency graphs showing KPI relationships

### Phase 3: Benchmarking
1. Calculate hierarchical benchmarks at all three levels
2. Add peer comparison for Level 2 and Level 3 metrics
3. Implement outlier detection and alerting

## References

- **CMS Form 2552-10**: Hospital Cost Report form
- **HCRIS**: Hospital Cost Report Information System
- **Worksheet References**: See individual KPI definitions in `kpi_hierarchy_config.py`
- **Original Requirements**: See `to_do.txt` for detailed hierarchy specifications

## Support

For questions or issues related to the KPI hierarchy:
1. Review this documentation
2. Check `kpi_hierarchy_config.py` for detailed KPI specifications
3. Review `to_do.txt` for original requirements and formulas
4. Check the `calculate_kpis()` method in `dashboard.py` for implementation details

---

**Last Updated**: 2025-11-15
**Version**: 1.0
**Total KPIs**: 78 (6 L1 + 24 L2 + 48 L3)
