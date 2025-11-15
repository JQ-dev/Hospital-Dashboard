# Interactive Valuation Dashboard - User Guide

## Overview

This interactive dashboard allows you to analyze hospital financial performance and see how changes in key metrics affect hospital valuation in real-time. It provides detailed income statement breakdowns with expense categorization by administrative, clinical, and ancillary services.

---

## Features

### 1. **Real-Time Sensitivity Analysis**
   - Adjust revenue, expenses, margins, and valuation multiples using interactive sliders
   - See immediate impact on EBITDA and total valuation
   - Understand how operational changes affect enterprise value

### 2. **Detailed Income Statement Visualization**
   - Waterfall charts showing revenue flow to net income
   - Line-by-line income statement detail
   - Before/after comparison tables

### 3. **Expense Category Drill-Down**
   - **Administrative & General:** A&G costs, employee benefits
   - **Clinical Services:** Inpatient routine, ICU, nursing
   - **Ancillary Services:** Radiology, lab, pharmacy, OR, PT/OT
   - **Support Services:** Dietary, housekeeping, plant operations
   - **Medical Education:** Interns, residents, education programs

### 4. **Component Impact Analysis**
   - See exactly how each expense category contributes to costs
   - Identify areas for cost reduction or optimization
   - Compare expense distribution across categories

---

## Setup Instructions

### Step 1: Run ETL Scripts

First, extract the required data from HCRIS raw files:

```bash
# Navigate to project directory
cd "d:\HealthVista Analytics\hospital_dashboard"

# 1. Extract Income Statement (Worksheet G-3)
python etl\create_income_statement.py

# 2. Extract Detailed Expense Breakdown (Worksheet A)
python etl\create_expense_detail.py
```

**Expected Output:**
- `data/output/income_statement_long/` - Income statement data partitioned by year and state
- `data/output/income_statement_wide/` - Pivoted income statement for easy analysis
- `data/output/expense_detail/` - Detailed expense breakdown by category

### Step 2: Load Data into DuckDB

Load the parquet files into DuckDB for fast querying:

```bash
python scripts\load_valuation_data.py
```

**Expected Output:**
- Creates/updates `hospital_analytics.duckdb`
- Three tables created:
  - `income_statement_long` - Detailed income statement lines
  - `income_statement_wide` - Pivoted income statement
  - `expense_detail` - Expense breakdown by category

**Verify Data Load:**
```bash
# Should see confirmation messages like:
# Loaded income_statement_long: X records, Y providers, Z years
# Loaded expense_detail: X records, Y providers, Z expense categories
```

### Step 3: Launch Dashboard

Start the interactive Dash application:

```bash
python valuation_dashboard.py
```

**Access Dashboard:**
- Open browser to: `http://127.0.0.1:8051`
- Dashboard should load with hospital selector

---

## How to Use the Dashboard

### Selecting a Hospital

1. **Choose Hospital:**
   - Use the dropdown to select a provider by Provider Number
   - Hospitals are listed with their provider ID (e.g., "Provider 010001")

2. **Select Fiscal Year:**
   - Choose the fiscal year to analyze
   - Dropdown automatically populates with available years for selected hospital

3. **Load Data:**
   - Click "Load Data" button to populate dashboard with hospital's financials

### Understanding the Metrics Cards

Four key metric cards display at the top:

| Metric | Description |
|--------|-------------|
| **Net Patient Revenue** | Total patient revenue minus deductions (contractual adjustments, bad debts, charity care) |
| **Operating Income** | Net Patient Revenue minus Operating Expenses (core profitability) |
| **EBITDA (Est.)** | Earnings before interest, taxes, depreciation, and amortization (valuation metric) |
| **Valuation** | Estimated enterprise value using EBITDA multiple (default: 8x) |

### Using Sensitivity Analysis Sliders

#### 1. Revenue Change (%)
- **Range:** -20% to +20%
- **Impact:** Changes Net Patient Revenue
- **Use Case:** Model revenue growth scenarios, new service lines, volume changes

**Example:**
- +10% revenue = Model impact of 10% patient volume increase
- -5% revenue = Model impact of payer mix deterioration

#### 2. Operating Margin Change (percentage points)
- **Range:** -10pp to +10pp
- **Impact:** Changes Operating Income relative to revenue
- **Use Case:** Model operational efficiency improvements or cost pressures

**Example:**
- +3pp margin = Model impact of cost reduction initiatives
- -2pp margin = Model impact of increased labor costs

#### 3. Operating Expense Change (%)
- **Range:** -20% to +20%
- **Impact:** Directly changes Total Operating Expenses
- **Use Case:** Model specific cost reduction or inflation scenarios

**Example:**
- -8% expenses = Model impact of supply chain optimization
- +12% expenses = Model impact of wage inflation and labor shortages

#### 4. EBITDA Valuation Multiple
- **Range:** 4x to 14x
- **Impact:** Changes valuation calculation (Valuation = EBITDA × Multiple)
- **Use Case:** Adjust for market conditions, hospital type, or strategic value

**Typical Multiples:**
- **4-6x:** Small rural hospitals, distressed assets
- **6-8x:** Community hospitals, average performance
- **8-10x:** Strong regional hospitals, growth markets
- **10-14x:** Academic medical centers, strategic acquisitions

### Interpreting the Adjusted Metrics Table

The comparison table shows:
- **Original:** Baseline metrics from actual HCRIS data
- **Adjusted:** Metrics after applying sensitivity analysis sliders
- **Change:** Dollar amount difference
- **% Change:** Percentage difference

**Color Coding:**
- **Green:** Positive change (increased revenue/income, decreased expenses)
- **Red:** Negative change (decreased revenue/income, increased expenses)
- **Orange:** Final valuation (highlighted row)

### Visualizations

#### Income Statement Waterfall Chart
Shows the flow from Net Revenue to Net Income:
1. **Net Revenue:** Starting point (green bar)
2. **Operating Expenses:** Reduction (red bar)
3. **Operating Income:** Intermediate total (blue bar)
4. **Other Income (Net):** Adjustment (green/red bar)
5. **Net Income:** Final total (blue bar)

**Use Case:** Understand exactly where revenue goes and where margins are compressed

#### Valuation Sensitivity Chart
Bar chart comparing:
- **Base Case:** Original valuation (8x EBITDA)
- **Current Scenario:** Adjusted valuation based on slider inputs

**Color Coding:**
- Blue = Base case
- Orange = Positive change
- Red = Negative change

#### Expense Breakdown by Category (Top 10)
Horizontal bar chart showing largest expense categories.

**Common Top Categories:**
1. **Inpatient_Routine:** General acute care nursing and room costs
2. **Administrative_General:** Corporate overhead, management, HR, finance
3. **Radiology:** Imaging services (X-ray, CT, MRI)
4. **Operating_Room:** Surgical suite operations
5. **Laboratory:** Clinical lab and pathology
6. **Pharmacy:** Medication costs
7. **Emergency:** ER services

**Use Case:** Identify cost concentration areas and prioritize cost reduction efforts

#### Expense Distribution by Type (Pie Chart)
Shows expense allocation across high-level types:
- **General_Service:** Support services (A&G, housekeeping, dietary, plant)
- **Revenue_Producing:** Direct patient care (inpatient routine)
- **Ancillary:** Clinical support services (lab, radiology, pharmacy)
- **Outpatient:** Ambulatory services (clinics, ER)
- **Capital:** Building and equipment costs
- **Medical_Education:** Teaching program costs

**Use Case:** Understand expense structure and compare to industry benchmarks

---

## Practical Use Cases

### Use Case 1: M&A Target Valuation

**Scenario:** Evaluating a hospital acquisition

**Steps:**
1. Load target hospital data
2. Note baseline EBITDA and current valuation
3. Model operational improvements:
   - Set Operating Margin Change to +3pp (improvement from acquiring company's best practices)
   - Set Revenue Change to +5% (volume growth from expanded network)
4. Adjust multiple to 10x (strategic value)
5. Review adjusted valuation vs. asking price

**Key Questions:**
- What's the delta between adjusted valuation and asking price?
- What margin improvement is required to justify the purchase price?
- Which expense categories offer the most opportunity?

### Use Case 2: Operational Turnaround Planning

**Scenario:** Hospital is underperforming; CFO needs to model cost reduction

**Steps:**
1. Load hospital data
2. Review Expense Breakdown chart to identify largest cost centers
3. Model aggressive cost reduction:
   - Set Operating Expense Change to -10% (target cost reduction)
   - Keep Revenue constant (conservative assumption)
4. Review Operating Margin improvement
5. Drill into expense categories to prioritize cuts

**Key Questions:**
- What operating margin is achievable with aggressive cost management?
- Which expense categories are disproportionately high?
- What's the impact on EBITDA and enterprise value?

### Use Case 3: Debt Capacity Analysis

**Scenario:** Hospital seeking debt financing; lender evaluating debt service coverage

**Steps:**
1. Load hospital data
2. Note baseline EBITDA
3. Model stress scenarios:
   - Set Revenue Change to -10% (volume decline)
   - Set Operating Margin Change to -2pp (cost pressure)
4. Review stressed EBITDA
5. Calculate debt service coverage: EBITDA / Annual Debt Service

**Key Questions:**
- What's the minimum EBITDA under stress scenarios?
- Can the hospital service its debt under adverse conditions?
- What's the appropriate debt level given volatility?

### Use Case 4: Benchmarking and Target Setting

**Scenario:** Board wants to understand performance vs. peers

**Steps:**
1. Load hospital data
2. Note Operating Margin and EBITDA Margin
3. Compare to industry benchmarks:
   - Strong: Operating Margin >5%, EBITDA Margin >12%
   - Average: Operating Margin 2-5%, EBITDA Margin 7-12%
   - Weak: Operating Margin <2%, EBITDA Margin <7%
4. Model improvement needed to reach target tier
5. Identify expense categories to optimize

**Key Questions:**
- Where does the hospital rank relative to benchmarks?
- What margin improvement is needed to reach top quartile?
- Which cost categories offer the most leverage?

### Use Case 5: Service Line Expansion Analysis

**Scenario:** CFO evaluating impact of new cardiac service line

**Steps:**
1. Load current hospital data
2. Model incremental impact:
   - Set Revenue Change to +15% (new service line contribution)
   - Set Operating Expense Change to +10% (incremental costs - assume better margin)
3. Review Operating Margin and EBITDA improvement
4. Calculate incremental valuation creation
5. Review Expense by Category to see if capacity exists

**Key Questions:**
- What's the incremental EBITDA from the new service line?
- What's the ROI in terms of enterprise value creation?
- Does the hospital have capacity or need capital investment?

---

## Data Quality and Limitations

### Data Quality Considerations

1. **EBITDA Calculation:**
   - Current version uses Operating Income as EBITDA proxy
   - True EBITDA requires adding back depreciation and interest from Worksheets A and A-7
   - Consider implementing full EBITDA calculation for more accurate valuations

2. **COVID-19 Impact:**
   - 2020-2021 data may include:
     - COVID relief funds (non-recurring)
     - Extraordinary PPE and staffing costs
     - Volume disruptions
   - Consider adjusting for non-recurring items when analyzing these years

3. **Reporting Variations:**
   - Hospitals may file amended reports
   - Script keeps most recent report by Process_Date and Report_Status
   - Verify data quality for critical analyses

4. **Missing Data:**
   - Not all hospitals report all expense categories
   - Some expense categories may show as "Other" or "Unknown"
   - Expense detail is based on Worksheet A which may have reporting variations

### Known Limitations

1. **Simplified EBITDA:**
   - Does not include depreciation add-back (requires Worksheet A-7 integration)
   - Does not include interest add-back (requires Worksheet A, Line 11300)
   - May understate true EBITDA by 2-5 percentage points

2. **Expense Categories:**
   - Categorization is based on standard line numbers
   - Hospitals may classify costs differently
   - "Other" category may be significant for some hospitals

3. **Valuation Multiples:**
   - Multiples shown are illustrative ranges
   - Actual transaction multiples depend on many factors:
     - Hospital size and market position
     - Payer mix and managed care contracts
     - Capital requirements and deferred maintenance
     - Regulatory and compliance status
     - Strategic value to acquirer

4. **Tax Status:**
   - Dashboard doesn't distinguish tax-exempt vs. taxable entities
   - Tax implications affect valuation for investor-owned hospitals
   - Debt/equity structure impacts after-tax returns

---

## Troubleshooting

### Dashboard Won't Load

**Issue:** Browser shows "This site can't be reached"

**Solutions:**
1. Verify dashboard is running: `python valuation_dashboard.py`
2. Check port 8051 is not in use
3. Try alternative port: Edit `app.run_server(debug=True, port=8052)` in script

### No Hospitals in Dropdown

**Issue:** Hospital dropdown is empty

**Solutions:**
1. Verify ETL scripts ran successfully
2. Check DuckDB database exists: `ls hospital_analytics.duckdb`
3. Re-run data loader: `python scripts\load_valuation_data.py`
4. Check logs in `logs/` directory for errors

### "No data found" Message

**Issue:** Dashboard loads but shows "No data found"

**Solutions:**
1. Verify selected hospital and year have data in database
2. Check state filter in `config/paths.py` - may be filtering out hospital
3. Query database directly to verify data exists:
   ```python
   import duckdb
   conn = duckdb.connect('hospital_analytics.duckdb')
   conn.execute("SELECT COUNT(*) FROM income_statement_long").fetchall()
   conn.close()
   ```

### Expense Charts Empty

**Issue:** Expense breakdown charts show no data

**Solutions:**
1. Verify expense_detail ETL ran: Check for `data/output/expense_detail/` directory
2. Re-run ETL: `python etl\create_expense_detail.py`
3. Reload into DuckDB: `python scripts\load_valuation_data.py`

### Sliders Not Working

**Issue:** Moving sliders doesn't update metrics

**Solutions:**
1. Check browser console for JavaScript errors (F12 → Console tab)
2. Refresh page (Ctrl+R)
3. Restart dashboard application
4. Clear browser cache

---

## Advanced Configuration

### Customizing Expense Categories

To modify expense categorization, edit `etl/create_expense_detail.py`:

```python
EXPENSE_CATEGORIES = {
    'Your_Custom_Category': {
        'lines': ['00500', '00600'],  # Worksheet A line numbers
        'description': 'Your description',
        'category_type': 'General_Service'  # or Revenue_Producing, Ancillary, etc.
    },
    # ... add more categories
}
```

Then re-run:
```bash
python etl\create_expense_detail.py
python scripts\load_valuation_data.py
```

### Adjusting Default Valuation Multiple

Edit `valuation_dashboard.py`:

```python
# Find this line in the layout:
dcc.Slider(
    id='multiple-slider',
    min=4, max=14, step=0.5, value=8,  # Change value=8 to your default
    ...
)
```

### Adding More Income Statement Lines

Edit `etl/create_income_statement.py` to add more line mappings:

```python
INCOME_STATEMENT_LINES = {
    '03000': {'name': 'Your_Custom_Line', 'section': 'Revenue', 'subsection': 'Other'},
    # ... add more lines
}
```

### State Filtering

To change which states are included, edit `config/paths.py`:

```python
# Filter to specific states (empty list = all states)
FILTER_STATES = ['06', '36', '48']  # CA, NY, TX
```

Then re-run all ETL scripts.

---

## Performance Optimization

### For Large Datasets

1. **Partition Data:**
   - Data is already partitioned by Fiscal_Year and State_Code
   - Queries automatically filter on these partitions

2. **Limit Hospital List:**
   - Edit `load_hospital_list()` in dashboard to add `WHERE` clause:
   ```python
   query = """
   SELECT DISTINCT provider_number, MAX(fiscal_year) as latest_year
   FROM income_statement_long
   WHERE State_Code = '06'  -- California only
   GROUP BY provider_number
   ORDER BY provider_number
   LIMIT 500
   """
   ```

3. **Index Additional Columns:**
   - Edit `load_valuation_data.py` to add indexes:
   ```python
   conn.execute("CREATE INDEX idx_custom ON income_statement_long(your_column)")
   ```

### Dashboard Performance

- **Slow Loading:** Reduce dataset size or add more specific filters
- **Slow Sliders:** Simplify visualizations or reduce data points
- **Memory Issues:** Restart dashboard or reduce query result size

---

## Next Steps

### Enhancements to Consider

1. **Full EBITDA Calculation:**
   - Integrate Worksheet A-7 for depreciation
   - Add interest expense from Worksheet A
   - See `HCRIS_VALUATION_METHODOLOGY.md` for formulas

2. **Multi-Year Trends:**
   - Add time-series charts showing 3-5 year trends
   - Calculate growth rates (CAGR)
   - Show trajectory with projections

3. **Peer Benchmarking:**
   - Load multiple hospitals for comparison
   - Show percentile rankings
   - Calculate Z-scores vs. peers

4. **DCF Valuation:**
   - Add discounted cash flow calculator
   - Model terminal value
   - Include WACC calculator

5. **Scenario Planning:**
   - Save/load scenarios
   - Compare multiple scenarios side-by-side
   - Export to Excel/PDF

---

## Support and Documentation

- **Methodology:** See `HCRIS_VALUATION_METHODOLOGY.md` for detailed calculation methodology
- **Quick Reference:** See `HCRIS_QUICK_REFERENCE.md` for formulas and line numbers
- **Logs:** Check `logs/` directory for ETL and dashboard errors
- **HCRIS Documentation:** See `Provider Reimbursement Manual.txt` for official CMS guidance

---

**Last Updated:** 2025-11-13
**Version:** 1.0
