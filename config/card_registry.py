"""
Card Registry - Independent Card Definitions
=============================================

All KPI cards are defined here independently of any hierarchy.
Each card is self-contained with its metadata and display properties.

This allows cards to be:
- Easily added/modified
- Reused in multiple hierarchies
- Changed without affecting hierarchy structure
"""

# ============================================================================
# CARD DEFINITIONS
# ============================================================================

CARD_REGISTRY = {
    # ========================================================================
    # LEVEL 1 CARDS (Strategic KPIs)
    # ========================================================================
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
        'calculation_components': {
            'numerator': 'Net_Income',
            'denominator': 'Total_Revenue'
        }
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
        'improvement_levers': ['Improve billing processes', 'Reduce denials', 'Accelerate collections']
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
        'improvement_levers': ['Reduce labor costs', 'Optimize supply costs', 'Improve efficiency']
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
        'improvement_levers': ['Optimize charge master', 'Control costs', 'Improve efficiency']
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
        'improvement_levers': ['Improve financial screening', 'Reduce bad debt', 'Optimize charity policies']
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
        'calculation_components': {
            'numerator': 'Current_Assets',
            'denominator': 'Current_Liabilities'
        }
    },

    # ========================================================================
    # LEVEL 2 CARDS (Driver KPIs)
    # ========================================================================
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
        'improvement_levers': ['Reduce labor costs', 'Optimize supply chain', 'Improve efficiency']
    },

    'Non_Operating_Income_Pct': {
        'name': 'Non-Operating Income %',
        'category': 'Revenue',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (2, 5),
        'description': 'Non-operating revenue as % of total revenue. Boosts net income beyond core operations.',
        'formula_description': '(Non-Operating Income) ÷ (Total Revenue + Non-Operating Income)',
        'hcris_reference': '(G-3 Line 28) ÷ (G-3 Line 3 + Line 28)',
        'why_affects_parent': 'Boosts net income beyond core operations',
        'improvement_levers': ['Optimize investment returns', 'Seek grants', 'Manage donations']
    },

    'Payer_Mix_Medicare_Pct': {
        'name': 'Payer Mix - Medicare %',
        'category': 'Revenue Mix',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (30, 50),
        'description': 'Medicare patient days as % of total. Affects revenue stability and margins.',
        'formula_description': '(Medicare Days) ÷ (Total Patient Days)',
        'hcris_reference': '(S-3 Pt I Line 14 Col 2) ÷ (S-3 Pt I Line 14 Col 8)',
        'why_affects_parent': 'Affects revenue stability and margins',
        'improvement_levers': ['Diversify payer mix', 'Improve Medicare efficiency', 'Expand commercial volume']
    },

    'Capital_Cost_Pct_of_Expenses': {
        'name': 'Capital Cost % of Expenses',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (5, 10),
        'description': 'Capital-related costs as % of total expenses. High capital eats into margins if not managed.',
        'formula_description': '(Capital Costs) ÷ (Total Operating Expenses)',
        'hcris_reference': '(A Line 1-3 Col 7 Sum) ÷ (G-3 Line 25)',
        'why_affects_parent': 'High capital eats into margins if not managed',
        'improvement_levers': ['Optimize capital investments', 'Refinance debt', 'Extend asset life']
    },

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
        'improvement_levers': ['Improve documentation', 'Pre-authorization', 'Staff training']
    },

    'Payer_Mix_Commercial_Pct': {
        'name': 'Payer Mix - Commercial %',
        'category': 'Revenue Mix',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (30, 50),
        'description': 'Commercial payer share. Slower payers increase AR days.',
        'formula_description': '(Commercial Days) ÷ (Total Days)',
        'hcris_reference': '(S-3 Pt I Line 14 Col 7 - Cols 1-6 Sum) ÷ (S-3 Pt I Line 14 Col 8)',
        'why_affects_parent': 'Slower payers increase AR days',
        'improvement_levers': ['Negotiate payment terms', 'Expand commercial contracts', 'Improve collections']
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
        'improvement_levers': ['Improve coding accuracy', 'Optimize charge capture', 'Reduce errors']
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
        'hcris_reference': '(G Cash + Investments Increase) ÷ (G-3 Line 3)',
        'why_affects_parent': 'Poor collections inflate AR days',
        'improvement_levers': ['Accelerate cash collections', 'Reduce write-offs', 'Improve payment plans']
    },

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
        'improvement_levers': ['Optimize staffing', 'Reduce overtime', 'Improve productivity']
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
        'improvement_levers': ['Negotiate contracts', 'Reduce waste', 'Standardize supplies']
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
        'improvement_levers': ['Reduce administrative costs', 'Improve efficiency', 'Consolidate functions']
    },

    'Case_Mix_Index': {
        'name': 'Case Mix Index',
        'category': 'Patient Mix',
        'unit': 'index',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (1.2, 1.6),
        'description': 'Patient acuity measure. Higher acuity raises expenses per discharge.',
        'formula_description': 'Average DRG Weight',
        'hcris_reference': '(S-3 Pt I Line 1 Col 15)',
        'why_affects_parent': 'Higher acuity raises expenses per discharge',
        'improvement_levers': ['Improve coding accuracy', 'Document complexity', 'Focus on complex cases']
    },

    # Add more L2 and L3 cards here following the same pattern
    # ... (Continue with all other cards from the original hierarchy)
}


# ============================================================================
# CARD METADATA ENRICHMENT
# ============================================================================

def enrich_card_metadata(card_key, additional_metadata=None):
    """
    Get card definition with optional additional metadata

    Args:
        card_key: Card identifier
        additional_metadata: Dict of additional metadata to merge

    Returns:
        Enriched card definition
    """
    if card_key not in CARD_REGISTRY:
        return None

    card = CARD_REGISTRY[card_key].copy()

    if additional_metadata:
        card.update(additional_metadata)

    return card


def get_all_cards():
    """Get all card definitions"""
    return CARD_REGISTRY.copy()


def get_card_by_category(category):
    """Get all cards in a specific category"""
    return {k: v for k, v in CARD_REGISTRY.items() if v.get('category') == category}


def get_cards_by_tag(tag):
    """Get all cards with a specific tag (if tags are added to cards)"""
    return {k: v for k, v in CARD_REGISTRY.items() if tag in v.get('tags', [])}
