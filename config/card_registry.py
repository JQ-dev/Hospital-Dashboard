"""
KPI Card Registry
==================

Complete registry of all KPI cards with their metadata.
This file contains ONLY card definitions - no hierarchy information.

Each card is self-contained and can be reused in multiple hierarchies.

Card Structure:
- name: Display name for the KPI
- category: Grouping category (Profitability, Cost Management, Revenue Cycle, etc.)
- unit: Display unit (%, $, days, ratio, index)
- format: Python format string (.1f, .2f, ,.0f, .3f)
- higher_is_better: Boolean - determines color coding direction
- target_range: Tuple of (min, max) target values
- description: Brief explanation of what the KPI measures
- formula_description: Human-readable formula
- hcris_reference: CMS Form 2552-10 worksheet/line references
- improvement_levers: List of actions to improve the KPI
- calculation_components: Optional dict with numerator/denominator for display
- tags: List of tags for filtering (e.g., ['strategic', 'level1', 'driver'])

Usage:
    from config.card_registry import CARD_REGISTRY, get_card, get_cards_by_category

    card = get_card('Net_Income_Margin')
    profitability_cards = get_cards_by_category('Profitability')
"""

# =============================================================================
# COMPLETE KPI CARD REGISTRY - 78 KPIs
# =============================================================================

CARD_REGISTRY = {
    # =========================================================================
    # LEVEL 1 CARDS - Strategic KPIs (6 total)
    # =========================================================================

    'Net_Income_Margin': {
        'name': 'Net Income Margin',
        'category': 'Profitability',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (2, 4),
        'description': 'Overall profitability. Reflects financial health and sustainability.',
        'formula_description': '(Net Income) ÷ (Total Revenue)',
        'hcris_reference': '(G-3 Line 29) ÷ (G-3 Line 3)',
        'improvement_levers': ['Improve operating margin', 'Manage non-operating income', 'Control expenses'],
        'calculation_components': {'numerator': 'Net Income', 'denominator': 'Total Revenue'},
        'tags': ['strategic', 'level1', 'profitability'],
        'impact_score': 10,
        'ease_of_change': 4
    },

    'AR_Days': {
        'name': 'Days in Net Patient AR',
        'category': 'Revenue Cycle',
        'unit': 'days',
        'format': '.0f',
        'higher_is_better': False,
        'target_range': (40, 50),
        'description': 'Cash cycle efficiency. Measures how quickly hospital collects revenue.',
        'formula_description': '(Net Patient AR) ÷ (Net Patient Revenue / 365)',
        'hcris_reference': '(G Balance Sheet Current Assets Net Patient AR) ÷ (G-3 Line 3 ÷ 365)',
        'improvement_levers': ['Improve billing processes', 'Reduce denials', 'Accelerate collections'],
        'calculation_components': {'numerator': 'Net Patient AR', 'denominator': 'Daily Net Patient Revenue'},
        'tags': ['strategic', 'level1', 'revenue'],
        'impact_score': 9,
        'ease_of_change': 7
    },

    'Operating_Expense_per_Adjusted_Discharge': {
        'name': 'Operating Expense per Adjusted Discharge',
        'category': 'Cost Management',
        'unit': '$',
        'format': ',.0f',
        'higher_is_better': False,
        'target_range': (8000, 12000),
        'description': 'Cost control efficiency. Gauges per-unit cost management.',
        'formula_description': '(Total Operating Expenses) ÷ (Adjusted Discharges)',
        'hcris_reference': '(G-3 Line 25) ÷ [(S-3 Pt I Line 1 Col 1 × CMI) + (S-3 Pt I Line 15 Col 1 × 0.35)]',
        'improvement_levers': ['Reduce labor costs', 'Optimize supply costs', 'Improve efficiency'],
        'calculation_components': {'numerator': 'Total Operating Expenses', 'denominator': 'Adjusted Discharges'},
        'tags': ['strategic', 'level1', 'cost'],
        'impact_score': 9,
        'ease_of_change': 6
    },

    'Medicare_CCR': {
        'name': 'Medicare Cost-to-Charge Ratio',
        'category': 'Efficiency',
        'unit': 'ratio',
        'format': '.3f',
        'higher_is_better': False,
        'target_range': (0.2, 0.4),
        'description': 'Cost efficiency proxy. Lower CCR indicates better charge optimization.',
        'formula_description': '(Total Costs) ÷ (Total Charges)',
        'hcris_reference': '(C Pt I Col 5 Sum) ÷ (C Pt I Col 8 Sum)',
        'improvement_levers': ['Optimize charge master', 'Control costs', 'Improve efficiency'],
        'calculation_components': {'numerator': 'Total Costs', 'denominator': 'Total Charges'},
        'tags': ['strategic', 'level1', 'efficiency'],
        'impact_score': 7,
        'ease_of_change': 5
    },

    'Bad_Debt_Charity_Pct': {
        'name': 'Bad Debt + Charity %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (3, 8),
        'description': 'Uncompensated care burden. Measures charity care and bad debt as % of revenue.',
        'formula_description': '(Bad Debt + Charity Care) ÷ (Net Revenue - Provisions)',
        'hcris_reference': '(S-10 Line 29 Col 3 + Line 23 Col 3) ÷ (G-3 Line 3 - Provisions)',
        'improvement_levers': ['Improve financial screening', 'Reduce bad debt', 'Optimize charity policies'],
        'calculation_components': {'numerator': 'Bad Debt + Charity Care', 'denominator': 'Net Revenue'},
        'tags': ['strategic', 'level1', 'revenue'],
        'impact_score': 8,
        'ease_of_change': 5
    },

    'Current_Ratio': {
        'name': 'Current Ratio',
        'category': 'Liquidity',
        'unit': 'ratio',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (1.5, 2.5),
        'description': 'Short-term liquidity. Ability to meet current obligations with current assets.',
        'formula_description': '(Current Assets Unrestricted) ÷ (Current Liabilities)',
        'hcris_reference': '(G Line 1-12 Col 3 Unrestricted) ÷ (G Line 46-58 Col 3 Sum)',
        'improvement_levers': ['Build cash reserves', 'Improve collections', 'Manage payables'],
        'calculation_components': {'numerator': 'Current Assets', 'denominator': 'Current Liabilities'},
        'tags': ['strategic', 'level1', 'liquidity'],
        'impact_score': 9,
        'ease_of_change': 5
    },

    # =========================================================================
    # LEVEL 2 CARDS - Driver KPIs for Net Income Margin
    # =========================================================================

    'Operating_Expense_Ratio': {
        'name': 'Operating Expense Ratio',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (85, 95),
        'description': 'Operating expenses as % of revenue. Higher expenses erode net income.',
        'formula_description': '(Total Operating Expenses) ÷ (Total Revenue)',
        'hcris_reference': '(G-3 Line 25) ÷ (G-3 Line 3)',
        'why_affects_parent': 'Higher expenses directly erode net income',
        'improvement_levers': ['Reduce labor costs', 'Optimize supply chain', 'Improve efficiency'],
        'tags': ['driver', 'level2', 'cost'],
        'impact_score': 9,
        'ease_of_change': 5
    },

    'Non_Operating_Income_Pct': {
        'name': 'Non-Operating Income %',
        'category': 'Profitability',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (2, 5),
        'description': 'Non-operating revenue as % of total. Boosts net income beyond core operations.',
        'formula_description': '(Non-Operating Income) ÷ (Total Revenue + Non-Operating Income)',
        'hcris_reference': '(G-3 Line 28) ÷ (G-3 Line 3 + Line 28)',
        'why_affects_parent': 'Boosts net income beyond core operations',
        'improvement_levers': ['Optimize investment returns', 'Seek grants', 'Manage donations'],
        'tags': ['driver', 'level2', 'profitability'],
        'impact_score': 7,
        'ease_of_change': 3
    },

    'Payer_Mix_Medicare_Pct': {
        'name': 'Payer Mix - Medicare %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (30, 50),
        'description': 'Medicare patient days as % of total. Affects revenue stability and margins.',
        'formula_description': '(Medicare Days) ÷ (Total Patient Days)',
        'hcris_reference': '(S-3 Pt I Line 14 Col 2) ÷ (S-3 Pt I Line 14 Col 8)',
        'why_affects_parent': 'Affects revenue stability and margins',
        'improvement_levers': ['Diversify payer mix', 'Improve Medicare efficiency', 'Expand commercial volume'],
        'tags': ['driver', 'level2', 'revenue'],
        'impact_score': 8,
        'ease_of_change': 3
    },

    'Capital_Cost_Pct_of_Expenses': {
        'name': 'Capital Cost % of Expenses',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (5, 10),
        'description': 'Capital-related costs as % of total expenses. High capital eats into margins.',
        'formula_description': '(Capital Costs) ÷ (Total Operating Expenses)',
        'hcris_reference': '(A Line 1-3 Col 7 Sum) ÷ (G-3 Line 25)',
        'why_affects_parent': 'High capital eats into margins if not managed',
        'improvement_levers': ['Optimize capital investments', 'Refinance debt', 'Extend asset life'],
        'tags': ['driver', 'level2', 'cost'],
        'impact_score': 6,
        'ease_of_change': 2
    },

    # =========================================================================
    # LEVEL 2 CARDS - Driver KPIs for AR Days
    # =========================================================================

    'Denial_Rate': {
        'name': 'Denial Rate',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (5, 10),
        'description': 'Claim denials as % of total claims. Denials delay collections.',
        'formula_description': '(Total Denials) ÷ (Total Claims)',
        'hcris_reference': '(E Pt A Line 25) ÷ (E Pt A Line 1)',
        'why_affects_parent': 'Denials delay collections',
        'improvement_levers': ['Improve documentation', 'Pre-authorization', 'Staff training'],
        'tags': ['driver', 'level2', 'revenue'],
        'impact_score': 8,
        'ease_of_change': 6
    },

    'Payer_Mix_Commercial_Pct': {
        'name': 'Payer Mix - Commercial %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (30, 50),
        'description': 'Commercial payer share. Slower payers increase AR days.',
        'formula_description': '(Commercial Days) ÷ (Total Days)',
        'hcris_reference': '(S-3 Pt I Line 14 Col 7 - Cols 1-6 Sum) ÷ (S-3 Pt I Line 14 Col 8)',
        'why_affects_parent': 'Slower payers increase AR days',
        'improvement_levers': ['Negotiate payment terms', 'Expand commercial contracts', 'Improve collections'],
        'tags': ['driver', 'level2', 'revenue'],
        'impact_score': 7,
        'ease_of_change': 4
    },

    'Billing_Efficiency_Ratio': {
        'name': 'Billing Efficiency Ratio',
        'category': 'Revenue Cycle',
        'unit': 'ratio',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (0.8, 1.2),
        'description': 'Revenue per adjusted discharge. Inefficient billing prolongs AR.',
        'formula_description': '(Total Revenue) ÷ (Adjusted Discharges)',
        'hcris_reference': '(G-3 Line 3) ÷ (S-3 Pt I Line 14 Col 15 Adjusted Discharges)',
        'why_affects_parent': 'Inefficient billing prolongs AR',
        'improvement_levers': ['Improve coding accuracy', 'Optimize charge capture', 'Reduce errors'],
        'tags': ['driver', 'level2', 'revenue'],
        'impact_score': 7,
        'ease_of_change': 6
    },

    'Collection_Rate': {
        'name': 'Collection Rate',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (90, 98),
        'description': 'Cash collections efficiency. Poor collections inflate AR days.',
        'formula_description': '(Cash Increase) ÷ (Net Revenue)',
        'hcris_reference': '(G Cash + Investments Increase from G-1) ÷ (G-3 Line 3)',
        'why_affects_parent': 'Poor collections inflate AR days',
        'improvement_levers': ['Accelerate cash collections', 'Reduce write-offs', 'Improve payment plans'],
        'tags': ['driver', 'level2', 'revenue'],
        'impact_score': 9,
        'ease_of_change': 6
    },

    # =========================================================================
    # LEVEL 2 CARDS - Driver KPIs for Operating Expense per Adjusted Discharge
    # =========================================================================

    'Labor_Cost_per_Discharge': {
        'name': 'Labor Cost per Discharge',
        'category': 'Cost Management',
        'unit': '$',
        'format': ',.0f',
        'higher_is_better': False,
        'target_range': (4000, 7000),
        'description': 'Labor cost per discharge. Labor is 50-60% of expenses.',
        'formula_description': '(Total Labor Costs) ÷ (Adjusted Discharges)',
        'hcris_reference': '(S-3 Pt II Line 1 Col 1) ÷ (S-3 Pt I Line 1 Col 1 Adjusted)',
        'why_affects_parent': 'Labor is 50-60% of expenses',
        'improvement_levers': ['Optimize staffing', 'Reduce overtime', 'Improve productivity'],
        'tags': ['driver', 'level2', 'cost'],
        'impact_score': 9,
        'ease_of_change': 5
    },

    'Supply_Cost_per_Discharge': {
        'name': 'Supply Cost per Discharge',
        'category': 'Cost Management',
        'unit': '$',
        'format': ',.0f',
        'higher_is_better': False,
        'target_range': (1500, 3000),
        'description': 'Supply costs per discharge. Supplies drive variable costs.',
        'formula_description': '(Total Supply Costs) ÷ (Adjusted Discharges)',
        'hcris_reference': '(A Line 71 Col 7) ÷ (S-3 Pt I Line 1 Col 1 Adjusted)',
        'why_affects_parent': 'Supplies drive variable costs',
        'improvement_levers': ['Negotiate contracts', 'Reduce waste', 'Standardize supplies'],
        'tags': ['driver', 'level2', 'cost'],
        'impact_score': 8,
        'ease_of_change': 6
    },

    'Overhead_Allocation_Ratio': {
        'name': 'Overhead Allocation Ratio',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (15, 25),
        'description': 'Overhead as % of total expenses. Overhead inflates per-unit costs.',
        'formula_description': '(Overhead Costs) ÷ (Total Operating Expenses)',
        'hcris_reference': '(B Pt I Col 26 Sum General Svcs) ÷ (G-3 Line 25)',
        'why_affects_parent': 'Overhead inflates per-unit costs',
        'improvement_levers': ['Reduce administrative costs', 'Improve efficiency', 'Consolidate functions'],
        'tags': ['driver', 'level2', 'cost'],
        'impact_score': 7,
        'ease_of_change': 4
    },

    'Case_Mix_Index': {
        'name': 'Case Mix Index',
        'category': 'Operations',
        'unit': 'index',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (1.2, 1.6),
        'description': 'Patient acuity measure. Higher acuity raises expenses per discharge.',
        'formula_description': 'Average DRG Weight',
        'hcris_reference': '(S-3 Pt I Line 1 Col 15)',
        'why_affects_parent': 'Higher acuity raises expenses per discharge',
        'improvement_levers': ['Improve coding accuracy', 'Document complexity', 'Focus on complex cases'],
        'tags': ['driver', 'level2', 'operations'],
        'impact_score': 8,
        'ease_of_change': 3
    },

    # =========================================================================
    # LEVEL 2 CARDS - Driver KPIs for Medicare CCR
    # =========================================================================

    'Ancillary_Cost_Ratio': {
        'name': 'Ancillary Cost Ratio',
        'category': 'Efficiency',
        'unit': 'ratio',
        'format': '.3f',
        'higher_is_better': False,
        'target_range': (0.15, 0.35),
        'description': 'Ancillary costs as % of total costs. Ancillary drives CCR variability.',
        'formula_description': '(Ancillary Costs) ÷ (Total Costs)',
        'hcris_reference': '(C Pt I Lines 50-76 Col 5 Sum) ÷ (C Pt I Col 5 Total)',
        'why_affects_parent': 'Ancillary drives CCR variability',
        'improvement_levers': ['Optimize lab/radiology', 'Reduce unnecessary tests', 'Negotiate pricing'],
        'tags': ['driver', 'level2', 'efficiency'],
        'impact_score': 7,
        'ease_of_change': 5
    },

    'Charge_Inflation_Rate': {
        'name': 'Charge Inflation Rate',
        'category': 'Efficiency',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (2, 5),
        'description': 'Year-over-year charge growth. Rising charges lower CCR if costs lag.',
        'formula_description': 'YoY Change in Total Charges',
        'hcris_reference': 'YoY Change in (C Pt I Col 8 Sum)',
        'why_affects_parent': 'Rising charges lower CCR if costs lag',
        'improvement_levers': ['Annual charge updates', 'Market-based pricing', 'Service line review'],
        'tags': ['driver', 'level2', 'efficiency'],
        'impact_score': 6,
        'ease_of_change': 6
    },

    'Adjustment_Impact_on_Costs': {
        'name': 'Adjustment Impact on Costs',
        'category': 'Efficiency',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (1, 5),
        'description': 'Cost adjustments as % of total costs. Adjustments reduce allowable costs.',
        'formula_description': '(Total Adjustments) ÷ (Total Costs)',
        'hcris_reference': '(A-8 Col 2 Sum) ÷ (C Pt I Col 5 Sum)',
        'why_affects_parent': 'Adjustments reduce allowable costs, raising CCR',
        'improvement_levers': ['Minimize non-allowable costs', 'Improve documentation', 'Review cost reports'],
        'tags': ['driver', 'level2', 'efficiency'],
        'impact_score': 6,
        'ease_of_change': 4
    },

    'Utilization_Mix': {
        'name': 'Utilization Mix',
        'category': 'Operations',
        'unit': 'ratio',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (0.4, 0.6),
        'description': 'Outpatient visits as ratio to total. OP shift affects aggregate CCR.',
        'formula_description': '(OP Visits) ÷ (Total Adjusted Encounters)',
        'hcris_reference': '(S-3 Pt I Line 15 Col 1 OP Visits) ÷ (S-3 Pt I Line 1 Col 1 + Line 15 Col 1 Adjusted)',
        'why_affects_parent': 'OP shift affects aggregate CCR',
        'improvement_levers': ['Expand outpatient services', 'Shift procedures to outpatient', 'Build ambulatory capacity'],
        'tags': ['driver', 'level2', 'operations'],
        'impact_score': 7,
        'ease_of_change': 4
    },

    # =========================================================================
    # LEVEL 2 CARDS - Driver KPIs for Bad Debt + Charity
    # =========================================================================

    'Charity_Care_Charge_Ratio': {
        'name': 'Charity Care Charge Ratio',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (2, 6),
        'description': 'Charity care charges as % of total charges. High charity increases uncompensated %.',
        'formula_description': '(Charity Care Charges) ÷ (Total Charges)',
        'hcris_reference': '(S-10 Line 20 Col 3) ÷ (C Pt I Col 8 Sum)',
        'why_affects_parent': 'High charity increases uncompensated %',
        'improvement_levers': ['Improve financial screening', 'Expand Medicaid enrollment', 'Optimize charity policies'],
        'tags': ['driver', 'level2', 'revenue'],
        'impact_score': 7,
        'ease_of_change': 5
    },

    'Bad_Debt_Recovery_Rate': {
        'name': 'Bad Debt Recovery Rate',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (10, 30),
        'description': 'Bad debt recovered as % of total bad debt. Low recoveries inflate bad debt %.',
        'formula_description': '(Bad Debt Recovered) ÷ (Total Bad Debt)',
        'hcris_reference': '(S-10 Line 26) ÷ (S-10 Line 25)',
        'why_affects_parent': 'Low recoveries inflate bad debt %',
        'improvement_levers': ['Improve collections', 'Use collection agencies', 'Better credit screening'],
        'tags': ['driver', 'level2', 'revenue'],
        'impact_score': 7,
        'ease_of_change': 6
    },

    'Uninsured_Patient_Pct': {
        'name': 'Uninsured Patient %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (5, 15),
        'description': 'Uninsured patients as % of total. Uninsured drive charity/bad debt.',
        'formula_description': '(Uninsured Encounters) ÷ (Total Encounters)',
        'hcris_reference': '(S-10 Line 20 Col 1 + Line 31) ÷ (S-3 Pt I Line 14 Col 8)',
        'why_affects_parent': 'Uninsured drive charity/bad debt',
        'improvement_levers': ['Expand Medicaid', 'Financial counseling', 'Community outreach'],
        'tags': ['driver', 'level2', 'revenue'],
        'impact_score': 8,
        'ease_of_change': 4
    },

    'Medicaid_Shortfall_Pct': {
        'name': 'Medicaid Shortfall %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (0, 5),
        'description': 'Medicaid payment shortfall as % of revenue. Shortfalls add to uncompensated load.',
        'formula_description': '(Medicaid Cost - Medicaid Payment) ÷ (Total Revenue)',
        'hcris_reference': '(S-10 Line 18 - Line 19) ÷ (G-3 Line 3)',
        'why_affects_parent': 'Shortfalls add to uncompensated load',
        'improvement_levers': ['Advocate for rate increases', 'Improve Medicaid efficiency', 'Optimize coding'],
        'tags': ['driver', 'level2', 'revenue'],
        'impact_score': 7,
        'ease_of_change': 3
    },

    # =========================================================================
    # LEVEL 2 CARDS - Driver KPIs for Current Ratio
    # =========================================================================

    'Cash_Equivalents_Pct_of_Assets': {
        'name': 'Cash + Equivalents % of Assets',
        'category': 'Liquidity',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (10, 30),
        'description': 'Cash and equivalents as % of total assets. Boosts current assets for liquidity.',
        'formula_description': '(Cash + Marketable Securities) ÷ (Total Assets)',
        'hcris_reference': '(G Line 1+2 Col 3) ÷ (G Line 59 Col 3)',
        'why_affects_parent': 'Boosts current assets for liquidity',
        'improvement_levers': ['Build reserves', 'Retain earnings', 'Optimize cash management'],
        'tags': ['driver', 'level2', 'liquidity'],
        'impact_score': 8,
        'ease_of_change': 5
    },

    'Current_Liabilities_Ratio': {
        'name': 'Current Liabilities Ratio',
        'category': 'Liquidity',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (20, 40),
        'description': 'Current liabilities as % of total liabilities. High liabilities strain ratio.',
        'formula_description': '(Current Liabilities) ÷ (Total Liabilities)',
        'hcris_reference': '(G Line 46-58 Col 3 Sum) ÷ (G Line 75 Col 3)',
        'why_affects_parent': 'High liabilities strain ratio',
        'improvement_levers': ['Extend payment terms', 'Refinance short-term debt', 'Manage payables'],
        'tags': ['driver', 'level2', 'liquidity'],
        'impact_score': 7,
        'ease_of_change': 5
    },

    'Inventory_Turnover': {
        'name': 'Inventory Turnover',
        'category': 'Liquidity',
        'unit': 'ratio',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (20, 40),
        'description': 'Inventory efficiency. Low turnover ties up current assets.',
        'formula_description': '(Supply Expense) ÷ (Average Inventory)',
        'hcris_reference': '(A Line 71 Col 2 Supplies) ÷ (G Inventory Avg from Beg/End)',
        'why_affects_parent': 'Ties up current assets if low',
        'improvement_levers': ['Reduce inventory levels', 'Implement JIT', 'Improve supply chain'],
        'tags': ['driver', 'level2', 'liquidity'],
        'impact_score': 6,
        'ease_of_change': 6
    },

    'Fund_Balance_Pct_Change': {
        'name': 'Fund Balance % Change',
        'category': 'Liquidity',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (2, 8),
        'description': 'Change in fund balance as %. Positive changes build reserves.',
        'formula_description': '(Change in Fund Balance) ÷ (Beginning Fund Balance)',
        'hcris_reference': '(G-1 Line 21 Col 3) ÷ (G Line 70 Col 3 Beg)',
        'why_affects_parent': 'Positive changes build reserves',
        'improvement_levers': ['Improve profitability', 'Retain earnings', 'Build reserves'],
        'tags': ['driver', 'level2', 'liquidity'],
        'impact_score': 7,
        'ease_of_change': 4
    },

    # =========================================================================
    # LEVEL 3 CARDS - Sub-driver KPIs (48 total)
    # =========================================================================

    # Net Income Margin -> Operating Expense Ratio drivers
    'FTE_per_Bed': {
        'name': 'FTE per Bed',
        'category': 'Workforce',
        'unit': 'ratio',
        'format': '.2f',
        'higher_is_better': False,
        'target_range': (4, 6),
        'description': 'Staff intensity indicator. Higher ratios indicate more staffing per bed.',
        'formula_description': '(Total FTEs) ÷ (Total Beds)',
        'hcris_reference': '(S-3 Pt I Line 14 Col 6) ÷ (S-3 Pt I Line 7 Col 1)',
        'improvement_levers': ['Optimize staffing levels', 'Improve productivity', 'Cross-train staff'],
        'tags': ['sub-driver', 'level3', 'workforce']
    },

    'Salary_Pct_of_Expenses': {
        'name': 'Salary % of Total Expenses',
        'category': 'Workforce',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (45, 55),
        'description': 'Labor cost intensity. Salaries typically represent largest expense category.',
        'formula_description': '(Total Salaries) ÷ (Total Operating Expenses)',
        'hcris_reference': '(S-3 Pt II Line 1 Col 1) ÷ (G-3 Line 25)',
        'improvement_levers': ['Manage labor costs', 'Improve productivity', 'Optimize staffing mix'],
        'tags': ['sub-driver', 'level3', 'workforce']
    },

    # Net Income Margin -> Non-Operating Income drivers
    'Investment_Income_Share': {
        'name': 'Investment Income Share',
        'category': 'Profitability',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (40, 70),
        'description': 'Investment returns as % of non-operating income.',
        'formula_description': '(Investment Income) ÷ (Non-Operating Income)',
        'hcris_reference': '(G-1 Line 5 Col 3) ÷ (G-3 Line 28)',
        'improvement_levers': ['Optimize investment portfolio', 'Increase investment allocation'],
        'tags': ['sub-driver', 'level3', 'profitability']
    },

    'Donation_Grant_Pct': {
        'name': 'Donation/Grant %',
        'category': 'Profitability',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (10, 30),
        'description': 'Donations and grants as % of non-operating income.',
        'formula_description': '(Donations + Grants) ÷ (Non-Operating Income)',
        'hcris_reference': '(G-1 Line 6 Col 3) ÷ (G-3 Line 28)',
        'improvement_levers': ['Expand fundraising', 'Seek grant opportunities', 'Community partnerships'],
        'tags': ['sub-driver', 'level3', 'profitability']
    },

    # Net Income Margin -> Payer Mix Medicare drivers
    'Medicare_Inpatient_Days_Pct': {
        'name': 'Medicare Inpatient Days %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (30, 50),
        'description': 'Medicare inpatient utilization.',
        'formula_description': '(Medicare Inpatient Days) ÷ (Total Inpatient Days)',
        'hcris_reference': '(S-3 Pt I Line 8 Col 2) ÷ (S-3 Pt I Line 8 Col 8)',
        'improvement_levers': ['Diversify patient base', 'Expand commercial services'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    'Medicare_Outpatient_Revenue_Pct': {
        'name': 'Medicare Outpatient Revenue %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (15, 30),
        'description': 'Medicare outpatient revenue share.',
        'formula_description': '(Medicare Outpatient Revenue) ÷ (Total Revenue)',
        'hcris_reference': '(D Pt V Col 2 Sum) ÷ (G-3 Line 2)',
        'improvement_levers': ['Expand outpatient services', 'Grow commercial volume'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    # Net Income Margin -> Capital Cost drivers
    'Depreciation_Pct_of_Capital': {
        'name': 'Depreciation % of Capital',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (60, 80),
        'description': 'Depreciation intensity.',
        'formula_description': '(Depreciation) ÷ (Total Capital Costs)',
        'hcris_reference': '(A-7 Pt I Col 9) ÷ (A-7 Pt I Col 1)',
        'improvement_levers': ['Extend asset life', 'Optimize capital spending'],
        'tags': ['sub-driver', 'level3', 'cost']
    },

    'Interest_Expense_Ratio': {
        'name': 'Interest Expense Ratio',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (10, 25),
        'description': 'Interest burden on capital.',
        'formula_description': '(Interest Expense) ÷ (Total Capital Costs)',
        'hcris_reference': '(A Line 116 Col 2) ÷ (A Line 1-3 Col 7 Sum)',
        'improvement_levers': ['Refinance debt', 'Reduce borrowing', 'Improve credit rating'],
        'tags': ['sub-driver', 'level3', 'cost']
    },

    # AR Days -> Denial Rate drivers
    'Medicare_Denial_Pct': {
        'name': 'Medicare Denial %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (3, 8),
        'description': 'Medicare-specific denial rate.',
        'formula_description': '(Medicare Denials) ÷ (Medicare Claims)',
        'hcris_reference': '(E Pt A Line 25) ÷ (E Pt A Line 4)',
        'improvement_levers': ['Improve Medicare documentation', 'Train on Medicare rules'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    'Non_Medicare_Adjustment_Pct': {
        'name': 'Non-Medicare Adjustment %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (5, 15),
        'description': 'Non-Medicare adjustments as % of revenue.',
        'formula_description': '(Non-Medicare Adjustments) ÷ (Total Revenue)',
        'hcris_reference': '(A-8 Col 2 Sum Non-Allowable) ÷ (G-3 Line 3)',
        'improvement_levers': ['Reduce contractual adjustments', 'Improve payer contracts'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    # AR Days -> Commercial Payer Mix drivers
    'Commercial_Inpatient_Pct': {
        'name': 'Commercial Inpatient %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (25, 45),
        'description': 'Commercial inpatient utilization.',
        'formula_description': '(Commercial Inpatient Days) ÷ (Total Inpatient Days)',
        'hcris_reference': '(S-3 Pt I Line 8 Col 7 - Cols 1-6) ÷ (S-3 Pt I Line 8 Col 8)',
        'improvement_levers': ['Expand commercial programs', 'Market to employers'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    'Self_Pay_Pct': {
        'name': 'Self-Pay %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (3, 10),
        'description': 'Self-pay revenue share.',
        'formula_description': '(Self-Pay Revenue) ÷ (Total Revenue)',
        'hcris_reference': '(S-10 Line 20 Col 1) ÷ (G-3 Line 3)',
        'improvement_levers': ['Financial counseling', 'Enrollment assistance', 'Payment plans'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    # AR Days -> Billing Efficiency drivers
    'Charges_per_Discharge': {
        'name': 'Charges per Discharge',
        'category': 'Revenue Cycle',
        'unit': '$',
        'format': ',.0f',
        'higher_is_better': True,
        'target_range': (40000, 80000),
        'description': 'Average charges per discharge.',
        'formula_description': '(Total Charges) ÷ (Total Discharges)',
        'hcris_reference': '(C Pt I Col 8 Sum) ÷ (S-3 Pt I Line 1 Col 1)',
        'improvement_levers': ['Optimize charge master', 'Capture all charges', 'Review pricing'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    'Adjustment_Pct_of_Gross_Rev': {
        'name': 'Adjustment % of Gross Rev',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (50, 70),
        'description': 'Revenue adjustments.',
        'formula_description': '(Adjustments) ÷ (Gross Revenue)',
        'hcris_reference': '(G-3 Line 3 - Net Rev Derived) ÷ (G-2 Pt I Col 3 Sum)',
        'improvement_levers': ['Negotiate better contracts', 'Reduce write-offs'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    # AR Days -> Collection Rate drivers
    'Cash_from_Operations_Pct': {
        'name': 'Cash from Operations %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (80, 95),
        'description': 'Operating cash flow efficiency.',
        'formula_description': '(Cash from Operations) ÷ (Total Cash)',
        'hcris_reference': '(G-1 Line 1 Col 3) ÷ (G Cash Total)',
        'improvement_levers': ['Improve collections', 'Manage payables timing'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    'AR_Aging_Over_90_Days_Pct': {
        'name': 'AR Aging >90 Days %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (10, 20),
        'description': 'Aged receivables share.',
        'formula_description': '(AR Allowances) ÷ (Gross AR)',
        'hcris_reference': '(G Balance Sheet AR Allowances) ÷ (G AR Gross)',
        'improvement_levers': ['Accelerate collections', 'Address aged accounts', 'Reduce denials'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    # Operating Expense -> Labor Cost drivers
    'Contract_Labor_Pct': {
        'name': 'Contract Labor %',
        'category': 'Workforce',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (3, 10),
        'description': 'Contract labor as % of total labor.',
        'formula_description': '(Contract Labor) ÷ (Total Labor Costs)',
        'hcris_reference': '(S-3 Pt V Line 11 Col 1) ÷ (S-3 Pt II Line 1 Col 1)',
        'improvement_levers': ['Reduce agency usage', 'Hire permanent staff', 'Improve retention'],
        'tags': ['sub-driver', 'level3', 'workforce']
    },

    'Overtime_Hours_Pct': {
        'name': 'Overtime Hours %',
        'category': 'Workforce',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (3, 8),
        'description': 'Overtime as % of total hours.',
        'formula_description': '(Overtime Hours) ÷ (Total Hours)',
        'hcris_reference': '(S-3 Pt II Line 10 Col 2) ÷ (S-3 Pt II Line 1 Col 2)',
        'improvement_levers': ['Optimize scheduling', 'Improve staffing levels', 'Cross-train staff'],
        'tags': ['sub-driver', 'level3', 'workforce']
    },

    # Operating Expense -> Supply Cost drivers
    'Drug_Cost_Pct': {
        'name': 'Drug Cost %',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (15, 30),
        'description': 'Drug costs as % of total supply costs.',
        'formula_description': '(Drug Costs) ÷ (Total Supply Costs)',
        'hcris_reference': '(A Line 15 Col 7) ÷ (A Line 71 Col 7)',
        'improvement_levers': ['Negotiate drug contracts', 'Use formulary', 'Biosimilar adoption'],
        'tags': ['sub-driver', 'level3', 'cost']
    },

    'Implant_Device_Pct': {
        'name': 'Implant/Device %',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (10, 25),
        'description': 'Implants/devices as % of supply costs.',
        'formula_description': '(Implant/Device Costs) ÷ (Total Supply Costs)',
        'hcris_reference': '(A Line 72 Col 7) ÷ (A Line 71 Col 7)',
        'improvement_levers': ['Negotiate implant contracts', 'Standardize devices', 'Value analysis'],
        'tags': ['sub-driver', 'level3', 'cost']
    },

    # Operating Expense -> Overhead drivers
    'Admin_General_Pct': {
        'name': 'A&G % of Total',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (8, 15),
        'description': 'Administrative & general costs.',
        'formula_description': '(A&G Costs) ÷ (Total Operating Expenses)',
        'hcris_reference': '(A Line 5 Col 7) ÷ (G-3 Line 25)',
        'improvement_levers': ['Reduce admin overhead', 'Automate processes', 'Consolidate functions'],
        'tags': ['sub-driver', 'level3', 'cost']
    },

    'Maintenance_Pct': {
        'name': 'Maintenance %',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (2, 5),
        'description': 'Maintenance costs as % of expenses.',
        'formula_description': '(Maintenance Costs) ÷ (Total Operating Expenses)',
        'hcris_reference': '(A Line 6 Col 7) ÷ (G-3 Line 25)',
        'improvement_levers': ['Preventive maintenance', 'Optimize contracts', 'Energy efficiency'],
        'tags': ['sub-driver', 'level3', 'cost']
    },

    # Operating Expense -> Case Mix drivers
    'DRG_Weight_Average': {
        'name': 'DRG Weight Average',
        'category': 'Operations',
        'unit': 'index',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (1.2, 1.6),
        'description': 'Average DRG weight.',
        'formula_description': 'Average DRG Weight',
        'hcris_reference': '(S-3 Pt I Line 1 Col 15)',
        'improvement_levers': ['Improve documentation', 'Clinical documentation improvement'],
        'tags': ['sub-driver', 'level3', 'operations']
    },

    'Transfer_Adjusted_CMI': {
        'name': 'Transfer-Adjusted CMI',
        'category': 'Operations',
        'unit': 'index',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (1.2, 1.6),
        'description': 'CMI adjusted for transfers.',
        'formula_description': 'CMI Adjusted for Transfers',
        'hcris_reference': '(S-3 Pt I Line 1 Col 15 Adjusted for Transfers)',
        'improvement_levers': ['Manage transfers appropriately', 'Document transfer reasons'],
        'tags': ['sub-driver', 'level3', 'operations']
    },

    # Medicare CCR -> Ancillary Cost drivers
    'Lab_CCR': {
        'name': 'Lab CCR',
        'category': 'Efficiency',
        'unit': 'ratio',
        'format': '.3f',
        'higher_is_better': False,
        'target_range': (0.1, 0.25),
        'description': 'Laboratory cost-to-charge ratio.',
        'formula_description': '(Lab Costs) ÷ (Lab Charges)',
        'hcris_reference': '(C Pt I Line 60 Col 5) ÷ (C Pt I Line 60 Col 8)',
        'improvement_levers': ['Optimize lab operations', 'Review test pricing'],
        'tags': ['sub-driver', 'level3', 'efficiency']
    },

    'Radiology_CCR': {
        'name': 'Radiology CCR',
        'category': 'Efficiency',
        'unit': 'ratio',
        'format': '.3f',
        'higher_is_better': False,
        'target_range': (0.1, 0.25),
        'description': 'Radiology cost-to-charge ratio.',
        'formula_description': '(Radiology Costs) ÷ (Radiology Charges)',
        'hcris_reference': '(C Pt I Line 54 Col 5) ÷ (C Pt I Line 54 Col 8)',
        'improvement_levers': ['Optimize radiology operations', 'Review imaging pricing'],
        'tags': ['sub-driver', 'level3', 'efficiency']
    },

    # Medicare CCR -> Charge Inflation drivers
    'Inpatient_Charge_Pct': {
        'name': 'Inpatient Charge %',
        'category': 'Efficiency',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (40, 60),
        'description': 'Inpatient charges as % of total.',
        'formula_description': '(Inpatient Charges) ÷ (Total Charges)',
        'hcris_reference': '(C Pt I Col 6 Sum) ÷ (C Pt I Col 8 Sum)',
        'improvement_levers': ['Balance IP/OP mix', 'Review inpatient pricing'],
        'tags': ['sub-driver', 'level3', 'efficiency']
    },

    'Outpatient_Charge_Pct': {
        'name': 'Outpatient Charge %',
        'category': 'Efficiency',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (40, 60),
        'description': 'Outpatient charges as % of total.',
        'formula_description': '(Outpatient Charges) ÷ (Total Charges)',
        'hcris_reference': '(C Pt I Col 7 Sum) ÷ (C Pt I Col 8 Sum)',
        'improvement_levers': ['Grow outpatient volume', 'Review outpatient pricing'],
        'tags': ['sub-driver', 'level3', 'efficiency']
    },

    # Medicare CCR -> Adjustment Impact drivers
    'Non_Allowable_Pct': {
        'name': 'Non-Allowable %',
        'category': 'Efficiency',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (1, 5),
        'description': 'Non-allowable costs %.',
        'formula_description': '(Non-Allowable Costs) ÷ (Total Costs)',
        'hcris_reference': '(A-8 Col 2 Negative Sum) ÷ (A Col 3 Sum)',
        'improvement_levers': ['Minimize non-allowable costs', 'Review cost allocation'],
        'tags': ['sub-driver', 'level3', 'efficiency']
    },

    'RCE_Disallowance_Pct': {
        'name': 'RCE Disallowance %',
        'category': 'Efficiency',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (0, 3),
        'description': 'Related cost entity disallowances.',
        'formula_description': '(RCE Disallowances) ÷ (Total Costs)',
        'hcris_reference': '(A-8-2 Col 18 Sum) ÷ (C Pt I Col 5 Sum)',
        'improvement_levers': ['Review RCE agreements', 'Improve documentation'],
        'tags': ['sub-driver', 'level3', 'efficiency']
    },

    # Medicare CCR -> Utilization Mix drivers
    'ER_Visit_Pct': {
        'name': 'ER Visit %',
        'category': 'Operations',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (20, 40),
        'description': 'ER visits as % of outpatient.',
        'formula_description': '(ER Visits) ÷ (Total OP Visits)',
        'hcris_reference': '(S-3 Pt I Line 15 Col 1 ER Portion) ÷ (S-3 Pt I Line 15 Col 1)',
        'improvement_levers': ['Divert non-emergent visits', 'Expand urgent care'],
        'tags': ['sub-driver', 'level3', 'operations']
    },

    'Clinic_Visit_Pct': {
        'name': 'Clinic Visit %',
        'category': 'Operations',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (30, 50),
        'description': 'Clinic visits as % of outpatient.',
        'formula_description': '(Clinic Visits) ÷ (Total OP Costs)',
        'hcris_reference': '(A Line 91 Col 7 Clinic) ÷ (C Pt I Col 5 OP Sum)',
        'improvement_levers': ['Expand clinic services', 'Improve clinic access'],
        'tags': ['sub-driver', 'level3', 'operations']
    },

    # Bad Debt -> Charity Care drivers
    'Insured_Charity_Pct': {
        'name': 'Insured Charity %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (10, 30),
        'description': 'Insured patients receiving charity care.',
        'formula_description': '(Insured Charity) ÷ (Total Charity)',
        'hcris_reference': '(S-10 Line 20 Col 2) ÷ (S-10 Line 20 Col 3)',
        'improvement_levers': ['Address underinsurance', 'Improve coverage verification'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    'Non_Covered_Charity_Pct': {
        'name': 'Non-Covered Charity %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (5, 20),
        'description': 'Non-covered services charity care.',
        'formula_description': '(Non-Covered Charity) ÷ (Total Charity)',
        'hcris_reference': '(S-10 Line 20 Col 1) ÷ (S-10 Line 20 Col 3)',
        'improvement_levers': ['Review non-covered services', 'Improve coverage communication'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    # Bad Debt -> Recovery Rate drivers
    'Medicare_Bad_Debt_Pct': {
        'name': 'Medicare Bad Debt %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (10, 30),
        'description': 'Medicare bad debt share.',
        'formula_description': '(Medicare Bad Debt) ÷ (Total Bad Debt)',
        'hcris_reference': '(E Pt A Line 64) ÷ (S-10 Line 25)',
        'improvement_levers': ['Improve Medicare collections', 'Address copay issues'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    'Non_Medicare_Bad_Debt_Pct': {
        'name': 'Non-Medicare Bad Debt %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (50, 80),
        'description': 'Non-Medicare bad debt share.',
        'formula_description': '(Non-Medicare Bad Debt) ÷ (Total Bad Debt)',
        'hcris_reference': '(S-10 Line 25 - E Pt A Line 64) ÷ (S-10 Line 25)',
        'improvement_levers': ['Improve non-Medicare collections', 'Payment plans'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    # Bad Debt -> Uninsured drivers
    'Uninsured_Inpatient_Pct': {
        'name': 'Uninsured Inpatient %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (3, 10),
        'description': 'Uninsured inpatient share.',
        'formula_description': '(Uninsured Inpatient Days) ÷ (Total Inpatient Days)',
        'hcris_reference': '(S-10 Inpatient Portion Derived) ÷ (S-3 Pt I Line 8 Col 8)',
        'improvement_levers': ['Financial screening at admission', 'Enrollment assistance'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    'Uninsured_OP_Pct': {
        'name': 'Uninsured OP %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (5, 15),
        'description': 'Uninsured outpatient share.',
        'formula_description': '(Uninsured OP Visits) ÷ (Total OP Visits)',
        'hcris_reference': '(S-10 OP Portion) ÷ (S-3 Pt I Line 15 Col 1)',
        'improvement_levers': ['Point-of-service screening', 'Community enrollment drives'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    # Bad Debt -> Medicaid Shortfall drivers
    'Medicaid_Days_Pct': {
        'name': 'Medicaid Days %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (10, 25),
        'description': 'Medicaid patient days share.',
        'formula_description': '(Medicaid Days) ÷ (Total Patient Days)',
        'hcris_reference': '(S-3 Pt I Line 14 Col 5+6) ÷ (S-3 Pt I Line 14 Col 8)',
        'improvement_levers': ['Manage Medicaid volume', 'Improve efficiency'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    'Medicaid_Payment_to_Cost': {
        'name': 'Medicaid Payment-to-Cost',
        'category': 'Revenue Cycle',
        'unit': 'ratio',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (0.7, 0.95),
        'description': 'Medicaid payment adequacy.',
        'formula_description': '(Medicaid Payment) ÷ (Medicaid Cost)',
        'hcris_reference': '(S-10 Line 18) ÷ (S-10 Line 19)',
        'improvement_levers': ['Optimize Medicaid reimbursement', 'Reduce costs'],
        'tags': ['sub-driver', 'level3', 'revenue']
    },

    # Current Ratio -> Cash Equivalents drivers
    'Operating_Cash_Flow': {
        'name': 'Operating Cash Flow',
        'category': 'Liquidity',
        'unit': '$M',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (5, 50),
        'description': 'Cash flow from operations.',
        'formula_description': '(Cash from Operations) ÷ (Cash + Equivalents)',
        'hcris_reference': '(G-1 Line 1 Col 3) ÷ (G Line 1+2 Col 3)',
        'improvement_levers': ['Improve collections', 'Manage payables', 'Control costs'],
        'tags': ['sub-driver', 'level3', 'liquidity']
    },

    'Investment_Returns': {
        'name': 'Investment Returns',
        'category': 'Liquidity',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (3, 8),
        'description': 'Investment income returns.',
        'formula_description': '(Investment Income) ÷ (Investments)',
        'hcris_reference': '(G-1 Line 5 Col 3) ÷ (G Line 39 Col 3)',
        'improvement_levers': ['Optimize portfolio', 'Review investment strategy'],
        'tags': ['sub-driver', 'level3', 'liquidity']
    },

    # Current Ratio -> Current Liabilities drivers
    'Accounts_Payable_Pct': {
        'name': 'Accounts Payable %',
        'category': 'Liquidity',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (30, 50),
        'description': 'AP as % of current liabilities.',
        'formula_description': '(Accounts Payable) ÷ (Current Liabilities)',
        'hcris_reference': '(G Line 47 Col 3) ÷ (G Line 46-58 Sum)',
        'improvement_levers': ['Manage payment timing', 'Negotiate terms'],
        'tags': ['sub-driver', 'level3', 'liquidity']
    },

    'Short_Term_Debt_Pct': {
        'name': 'Short-Term Debt %',
        'category': 'Liquidity',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (5, 20),
        'description': 'Short-term debt as % of current liabilities.',
        'formula_description': '(Short-Term Debt) ÷ (Current Liabilities)',
        'hcris_reference': '(G Line 46 Col 3) ÷ (G Line 46-58 Sum)',
        'improvement_levers': ['Refinance to long-term', 'Reduce borrowing'],
        'tags': ['sub-driver', 'level3', 'liquidity']
    },

    # Current Ratio -> Inventory Turnover drivers
    'Supply_Expense_Pct': {
        'name': 'Supply Expense %',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (10, 20),
        'description': 'Supply expenses as % of total.',
        'formula_description': '(Supply Expenses) ÷ (Total Operating Expenses)',
        'hcris_reference': '(A Line 71 Col 7) ÷ (G-3 Line 25)',
        'improvement_levers': ['Negotiate contracts', 'Reduce waste', 'Standardize supplies'],
        'tags': ['sub-driver', 'level3', 'cost']
    },

    'Days_in_Inventory': {
        'name': 'Days in Inventory',
        'category': 'Liquidity',
        'unit': 'days',
        'format': '.0f',
        'higher_is_better': False,
        'target_range': (10, 20),
        'description': 'Average days inventory on hand.',
        'formula_description': '(Inventory) ÷ (Supply Expense / 365)',
        'hcris_reference': '(G Line 4 Col 3) ÷ ((A Line 71 Col 2) ÷ 365)',
        'improvement_levers': ['Reduce inventory levels', 'Improve turnover', 'JIT delivery'],
        'tags': ['sub-driver', 'level3', 'liquidity']
    },

    # Current Ratio -> Fund Balance drivers
    'Retained_Earnings_Pct': {
        'name': 'Retained Earnings %',
        'category': 'Liquidity',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (30, 60),
        'description': 'Retained earnings as % of total liabilities.',
        'formula_description': '(Retained Earnings) ÷ (Total Liabilities)',
        'hcris_reference': '(G Line 73 Col 3) ÷ (G Line 75 Col 3)',
        'improvement_levers': ['Improve profitability', 'Retain earnings'],
        'tags': ['sub-driver', 'level3', 'liquidity']
    },

    'Depreciation_Impact': {
        'name': 'Depreciation Impact',
        'category': 'Liquidity',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (50, 100),
        'description': 'Depreciation as % of fund balance change.',
        'formula_description': '(Depreciation) ÷ (Fund Balance Change)',
        'hcris_reference': '(G-1 Line 3 Col 3) ÷ (G-1 Line 21 Col 3)',
        'improvement_levers': ['Manage capital spending', 'Optimize asset life'],
        'tags': ['sub-driver', 'level3', 'liquidity']
    },
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_card(card_id: str) -> dict:
    """Get a card definition by ID."""
    return CARD_REGISTRY.get(card_id, {})


def get_all_cards() -> dict:
    """Get all card definitions."""
    return CARD_REGISTRY.copy()


def get_cards_by_category(category: str) -> dict:
    """Get all cards in a specific category."""
    return {k: v for k, v in CARD_REGISTRY.items() if v.get('category') == category}


def get_cards_by_tag(tag: str) -> dict:
    """Get all cards with a specific tag."""
    return {k: v for k, v in CARD_REGISTRY.items() if tag in v.get('tags', [])}


def get_level1_cards() -> dict:
    """Get all Level 1 (strategic) cards."""
    return get_cards_by_tag('level1')


def get_level2_cards() -> dict:
    """Get all Level 2 (driver) cards."""
    return get_cards_by_tag('level2')


def get_level3_cards() -> dict:
    """Get all Level 3 (sub-driver) cards."""
    return get_cards_by_tag('level3')


def get_categories() -> list:
    """Get list of all unique categories."""
    categories = set(card.get('category', 'Other') for card in CARD_REGISTRY.values())
    return sorted(categories)


def validate_card_ids(card_ids: list) -> tuple:
    """Validate a list of card IDs. Returns (valid_ids, invalid_ids)."""
    valid_ids = [cid for cid in card_ids if cid in CARD_REGISTRY]
    invalid_ids = [cid for cid in card_ids if cid not in CARD_REGISTRY]
    return valid_ids, invalid_ids


def enrich_card_metadata(card_id: str, additional_metadata: dict) -> dict:
    """Merge additional metadata with a card definition."""
    card = get_card(card_id)
    if card:
        return {**card, **additional_metadata}
    return additional_metadata


# =============================================================================
# BACKWARD COMPATIBILITY - Flat metadata dictionary
# =============================================================================

KPI_METADATA = CARD_REGISTRY.copy()
