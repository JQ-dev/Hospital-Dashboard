"""
Three-Level KPI Hierarchy Configuration
Based on Hospital HCRIS Data (CMS Form 2552-10)

Hierarchical structure:
- Level 1: 6 top-level strategic KPIs
- Level 2: 4 driver KPIs per Level 1 (24 total)
- Level 3: 2 sub-driver KPIs per Level 2 (48 total)

Total: 78 KPIs across 3 levels
"""

KPI_HIERARCHY = {
    # ========================================================================
    # LEVEL 1 KPI 1: Net Income Margin
    # ========================================================================
    'Net_Income_Margin': {
        'level': 1,
        'name': 'Net Income Margin',
        'category': 'Profitability',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (2, 4),
        'impact_score': 10,
        'ease_of_change': 4,
        'description': 'Overall profitability. Reflects financial health and sustainability.',
        'formula_description': '(Net Income) ÷ (Total Revenue)',
        'hcris_reference': '(G-3 Line 29) ÷ (G-3 Line 3)',
        'improvement_levers': ['Improve operating margin', 'Manage non-operating income', 'Control expenses'],
        'level_2_kpis': {
            'Operating_Expense_Ratio': {
                'level': 2,
                'name': 'Operating Expense Ratio',
                'category': 'Cost Management',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': False,
                'target_range': (85, 95),
                'impact_score': 9,
                'ease_of_change': 5,
                'description': 'Operating expenses as % of revenue. Higher expenses erode net income.',
                'formula_description': '(Total Operating Expenses) ÷ (Total Revenue)',
                'hcris_reference': '(G-3 Line 25) ÷ (G-3 Line 3)',
                'why_affects_parent': 'Higher expenses directly erode net income',
                'improvement_levers': ['Reduce labor costs', 'Optimize supply chain', 'Improve efficiency'],
                'level_3_kpis': {
                    'FTE_per_Bed': {
                        'level': 3,
                        'name': 'FTE per Bed',
                        'unit': 'ratio',
                        'format': '.2f',
                        'higher_is_better': False,
                        'description': 'Staff intensity indicator',
                        'formula_description': '(Total FTEs) ÷ (Total Beds)',
                        'hcris_reference': '(S-3 Pt I Line 14 Col 6) ÷ (S-3 Pt I Line 7 Col 1)'
                    },
                    'Salary_Pct_of_Expenses': {
                        'level': 3,
                        'name': 'Salary % of Total Expenses',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Labor cost intensity',
                        'formula_description': '(Total Salaries) ÷ (Total Operating Expenses)',
                        'hcris_reference': '(S-3 Pt II Line 1 Col 1) ÷ (G-3 Line 25)'
                    }
                }
            },
            'Non_Operating_Income_Pct': {
                'level': 2,
                'name': 'Non-Operating Income %',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': True,
                'target_range': (2, 5),
                'impact_score': 7,
                'ease_of_change': 3,
                'description': 'Non-operating revenue as % of total revenue. Boosts net income beyond core operations.',
                'formula_description': '(Non-Operating Income) ÷ (Total Revenue + Non-Operating Income)',
                'hcris_reference': '(G-3 Line 28) ÷ (G-3 Line 3 + Line 28)',
                'why_affects_parent': 'Boosts net income beyond core operations',
                'improvement_levers': ['Optimize investment returns', 'Seek grants', 'Manage donations'],
                'level_3_kpis': {
                    'Investment_Income_Share': {
                        'level': 3,
                        'name': 'Investment Income Share',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': True,
                        'description': 'Investment returns as % of non-operating income',
                        'formula_description': '(Investment Income) ÷ (Non-Operating Income)',
                        'hcris_reference': '(G-1 Line 5 Col 3) ÷ (G-3 Line 28)'
                    },
                    'Donation_Grant_Pct': {
                        'level': 3,
                        'name': 'Donation/Grant %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': True,
                        'description': 'Donations and grants as % of non-operating income',
                        'formula_description': '(Donations + Grants) ÷ (Non-Operating Income)',
                        'hcris_reference': '(G-1 Line 6 Col 3) ÷ (G-3 Line 28)'
                    }
                }
            },
            'Payer_Mix_Medicare_Pct': {
                'level': 2,
                'name': 'Payer Mix - Medicare %',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': False,
                'target_range': (30, 50),
                'impact_score': 8,
                'ease_of_change': 3,
                'description': 'Medicare patient days as % of total. Affects revenue stability and margins.',
                'formula_description': '(Medicare Days) ÷ (Total Patient Days)',
                'hcris_reference': '(S-3 Pt I Line 14 Col 2) ÷ (S-3 Pt I Line 14 Col 8)',
                'why_affects_parent': 'Affects revenue stability and margins',
                'improvement_levers': ['Diversify payer mix', 'Improve Medicare efficiency', 'Expand commercial volume'],
                'level_3_kpis': {
                    'Medicare_Inpatient_Days_Pct': {
                        'level': 3,
                        'name': 'Medicare Inpatient Days %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Medicare inpatient utilization',
                        'formula_description': '(Medicare Inpatient Days) ÷ (Total Inpatient Days)',
                        'hcris_reference': '(S-3 Pt I Line 8 Col 2) ÷ (S-3 Pt I Line 8 Col 8)'
                    },
                    'Medicare_Outpatient_Revenue_Pct': {
                        'level': 3,
                        'name': 'Medicare Outpatient Revenue %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Medicare outpatient revenue share',
                        'formula_description': '(Medicare Outpatient Revenue) ÷ (Total Revenue)',
                        'hcris_reference': '(D Pt V Col 2 Sum) ÷ (G-3 Line 2)'
                    }
                }
            },
            'Capital_Cost_Pct_of_Expenses': {
                'level': 2,
                'name': 'Capital Cost % of Expenses',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': False,
                'target_range': (5, 10),
                'impact_score': 6,
                'ease_of_change': 2,
                'description': 'Capital-related costs as % of total expenses. High capital eats into margins if not managed.',
                'formula_description': '(Capital Costs) ÷ (Total Operating Expenses)',
                'hcris_reference': '(A Line 1-3 Col 7 Sum) ÷ (G-3 Line 25)',
                'why_affects_parent': 'High capital eats into margins if not managed',
                'improvement_levers': ['Optimize capital investments', 'Refinance debt', 'Extend asset life'],
                'level_3_kpis': {
                    'Depreciation_Pct_of_Capital': {
                        'level': 3,
                        'name': 'Depreciation % of Capital',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Depreciation intensity',
                        'formula_description': '(Depreciation) ÷ (Total Capital Costs)',
                        'hcris_reference': '(A-7 Pt I Col 9) ÷ (A-7 Pt I Col 1)'
                    },
                    'Interest_Expense_Ratio': {
                        'level': 3,
                        'name': 'Interest Expense Ratio',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Interest burden on capital',
                        'formula_description': '(Interest Expense) ÷ (Total Capital Costs)',
                        'hcris_reference': '(A Line 116 Col 2) ÷ (A Line 1-3 Col 7 Sum)'
                    }
                }
            }
        }
    },

    # ========================================================================
    # LEVEL 1 KPI 2: Days in Net Patient Accounts Receivable
    # ========================================================================
    'AR_Days': {
        'level': 1,
        'name': 'Days in Net Patient AR',
        'category': 'Revenue Cycle',
        'unit': 'days',
        'format': '.0f',
        'higher_is_better': False,
        'target_range': (40, 50),
        'impact_score': 9,
        'ease_of_change': 7,
        'description': 'Cash cycle efficiency. Measures how quickly hospital collects revenue.',
        'formula_description': '(Net Patient AR) ÷ (Net Patient Revenue / 365)',
        'hcris_reference': '(G Balance Sheet Current Assets Net Patient AR) ÷ (G-3 Line 3 ÷ 365)',
        'improvement_levers': ['Improve billing processes', 'Reduce denials', 'Accelerate collections'],
        'level_2_kpis': {
            'Denial_Rate': {
                'level': 2,
                'name': 'Denial Rate',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': False,
                'target_range': (5, 10),
                'impact_score': 8,
                'ease_of_change': 6,
                'description': 'Claim denials as % of total claims. Denials delay collections.',
                'formula_description': '(Total Denials) ÷ (Total Claims)',
                'hcris_reference': '(E Pt A Line 25) ÷ (E Pt A Line 1)',
                'why_affects_parent': 'Denials delay collections',
                'improvement_levers': ['Improve documentation', 'Pre-authorization', 'Staff training'],
                'level_3_kpis': {
                    'Medicare_Denial_Pct': {
                        'level': 3,
                        'name': 'Medicare Denial %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Medicare-specific denial rate',
                        'formula_description': '(Medicare Denials) ÷ (Medicare Claims)',
                        'hcris_reference': '(E Pt A Line 25) ÷ (E Pt A Line 4)'
                    },
                    'Non_Medicare_Adjustment_Pct': {
                        'level': 3,
                        'name': 'Non-Medicare Adjustment %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Non-Medicare adjustments as % of revenue',
                        'formula_description': '(Non-Medicare Adjustments) ÷ (Total Revenue)',
                        'hcris_reference': '(A-8 Col 2 Sum Non-Allowable) ÷ (G-3 Line 3)'
                    }
                }
            },
            'Payer_Mix_Commercial_Pct': {
                'level': 2,
                'name': 'Payer Mix - Commercial %',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': True,
                'target_range': (30, 50),
                'impact_score': 7,
                'ease_of_change': 4,
                'description': 'Commercial payer share. Slower payers increase AR days.',
                'formula_description': '(Commercial Days) ÷ (Total Days)',
                'hcris_reference': '(S-3 Pt I Line 14 Col 7 - Cols 1-6 Sum) ÷ (S-3 Pt I Line 14 Col 8)',
                'why_affects_parent': 'Slower payers increase AR days',
                'improvement_levers': ['Negotiate payment terms', 'Expand commercial contracts', 'Improve collections'],
                'level_3_kpis': {
                    'Commercial_Inpatient_Pct': {
                        'level': 3,
                        'name': 'Commercial Inpatient %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': True,
                        'description': 'Commercial inpatient utilization',
                        'formula_description': '(Commercial Inpatient Days) ÷ (Total Inpatient Days)',
                        'hcris_reference': '(S-3 Pt I Line 8 Col 7 - Cols 1-6) ÷ (S-3 Pt I Line 8 Col 8)'
                    },
                    'Self_Pay_Pct': {
                        'level': 3,
                        'name': 'Self-Pay %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Self-pay revenue share',
                        'formula_description': '(Self-Pay Revenue) ÷ (Total Revenue)',
                        'hcris_reference': '(S-10 Line 20 Col 1) ÷ (G-3 Line 3)'
                    }
                }
            },
            'Billing_Efficiency_Ratio': {
                'level': 2,
                'name': 'Billing Efficiency Ratio',
                'unit': 'ratio',
                'format': '.2f',
                'higher_is_better': True,
                'target_range': (0.8, 1.2),
                'impact_score': 7,
                'ease_of_change': 6,
                'description': 'Revenue per adjusted discharge. Inefficient billing prolongs AR.',
                'formula_description': '(Total Revenue) ÷ (Adjusted Discharges)',
                'hcris_reference': '(G-3 Line 3) ÷ (S-3 Pt I Line 14 Col 15 Adjusted Discharges)',
                'why_affects_parent': 'Inefficient billing prolongs AR',
                'improvement_levers': ['Improve coding accuracy', 'Optimize charge capture', 'Reduce errors'],
                'level_3_kpis': {
                    'Charges_per_Discharge': {
                        'level': 3,
                        'name': 'Charges per Discharge',
                        'unit': '$',
                        'format': ',.0f',
                        'higher_is_better': True,
                        'description': 'Average charges per discharge',
                        'formula_description': '(Total Charges) ÷ (Total Discharges)',
                        'hcris_reference': '(C Pt I Col 8 Sum) ÷ (S-3 Pt I Line 1 Col 1)'
                    },
                    'Adjustment_Pct_of_Gross_Rev': {
                        'level': 3,
                        'name': 'Adjustment % of Gross Rev',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Revenue adjustments',
                        'formula_description': '(Adjustments) ÷ (Gross Revenue)',
                        'hcris_reference': '(G-3 Line 3 - Net Rev Derived) ÷ (G-2 Pt I Col 3 Sum)'
                    }
                }
            },
            'Collection_Rate': {
                'level': 2,
                'name': 'Collection Rate',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': True,
                'target_range': (90, 98),
                'impact_score': 9,
                'ease_of_change': 6,
                'description': 'Cash collections efficiency. Poor collections inflate AR days.',
                'formula_description': '(Cash Increase) ÷ (Net Revenue)',
                'hcris_reference': '(G Cash + Investments Increase from G-1) ÷ (G-3 Line 3)',
                'why_affects_parent': 'Poor collections inflate AR days',
                'improvement_levers': ['Accelerate cash collections', 'Reduce write-offs', 'Improve payment plans'],
                'level_3_kpis': {
                    'Cash_from_Operations_Pct': {
                        'level': 3,
                        'name': 'Cash from Operations %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': True,
                        'description': 'Operating cash flow efficiency',
                        'formula_description': '(Cash from Operations) ÷ (Total Cash)',
                        'hcris_reference': '(G-1 Line 1 Col 3) ÷ (G Cash Total)'
                    },
                    'AR_Aging_Over_90_Days_Pct': {
                        'level': 3,
                        'name': 'AR Aging >90 Days %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Aged receivables share',
                        'formula_description': '(AR Allowances) ÷ (Gross AR)',
                        'hcris_reference': '(G Balance Sheet AR Allowances) ÷ (G AR Gross)'
                    }
                }
            }
        }
    },

    # ========================================================================
    # LEVEL 1 KPI 3: Operating Expense per Adjusted Discharge
    # ========================================================================
    'Operating_Expense_per_Adjusted_Discharge': {
        'level': 1,
        'name': 'Operating Expense per Adjusted Discharge',
        'category': 'Cost Management',
        'unit': '$',
        'format': ',.0f',
        'higher_is_better': False,
        'target_range': (8000, 12000),
        'impact_score': 9,
        'ease_of_change': 6,
        'description': 'Cost control efficiency. Gauges per-unit cost management.',
        'formula_description': '(Total Operating Expenses) ÷ (Adjusted Discharges)',
        'hcris_reference': '(G-3 Line 25) ÷ [(S-3 Pt I Line 1 Col 1 × S-3 Pt I Line 1 Col 15 CMI) + (S-3 Pt I Line 15 Col 1 × 0.35)]',
        'improvement_levers': ['Reduce labor costs', 'Optimize supply costs', 'Improve efficiency'],
        'level_2_kpis': {
            'Labor_Cost_per_Discharge': {
                'level': 2,
                'name': 'Labor Cost per Discharge',
                'unit': '$',
                'format': ',.0f',
                'higher_is_better': False,
                'target_range': (4000, 7000),
                'impact_score': 9,
                'ease_of_change': 5,
                'description': 'Labor cost per discharge. Labor is 50-60% of expenses.',
                'formula_description': '(Total Labor Costs) ÷ (Adjusted Discharges)',
                'hcris_reference': '(S-3 Pt II Line 1 Col 1) ÷ (S-3 Pt I Line 1 Col 1 Adjusted)',
                'why_affects_parent': 'Labor is 50-60% of expenses',
                'improvement_levers': ['Optimize staffing', 'Reduce overtime', 'Improve productivity'],
                'level_3_kpis': {
                    'Contract_Labor_Pct': {
                        'level': 3,
                        'name': 'Contract Labor %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Contract labor as % of total labor',
                        'formula_description': '(Contract Labor) ÷ (Total Labor Costs)',
                        'hcris_reference': '(S-3 Pt V Line 11 Col 1) ÷ (S-3 Pt II Line 1 Col 1)'
                    },
                    'Overtime_Hours_Pct': {
                        'level': 3,
                        'name': 'Overtime Hours %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Overtime as % of total hours',
                        'formula_description': '(Overtime Hours) ÷ (Total Hours)',
                        'hcris_reference': '(S-3 Pt II Line 10 Col 2) ÷ (S-3 Pt II Line 1 Col 2)'
                    }
                }
            },
            'Supply_Cost_per_Discharge': {
                'level': 2,
                'name': 'Supply Cost per Discharge',
                'unit': '$',
                'format': ',.0f',
                'higher_is_better': False,
                'target_range': (1500, 3000),
                'impact_score': 8,
                'ease_of_change': 6,
                'description': 'Supply costs per discharge. Supplies drive variable costs.',
                'formula_description': '(Total Supply Costs) ÷ (Adjusted Discharges)',
                'hcris_reference': '(A Line 71 Col 7) ÷ (S-3 Pt I Line 1 Col 1 Adjusted)',
                'why_affects_parent': 'Supplies drive variable costs',
                'improvement_levers': ['Negotiate contracts', 'Reduce waste', 'Standardize supplies'],
                'level_3_kpis': {
                    'Drug_Cost_Pct': {
                        'level': 3,
                        'name': 'Drug Cost %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Drug costs as % of total supply costs',
                        'formula_description': '(Drug Costs) ÷ (Total Supply Costs)',
                        'hcris_reference': '(A Line 15 Col 7) ÷ (A Line 71 Col 7)'
                    },
                    'Implant_Device_Pct': {
                        'level': 3,
                        'name': 'Implant/Device %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Implants/devices as % of supply costs',
                        'formula_description': '(Implant/Device Costs) ÷ (Total Supply Costs)',
                        'hcris_reference': '(A Line 72 Col 7) ÷ (A Line 71 Col 7)'
                    }
                }
            },
            'Overhead_Allocation_Ratio': {
                'level': 2,
                'name': 'Overhead Allocation Ratio',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': False,
                'target_range': (15, 25),
                'impact_score': 7,
                'ease_of_change': 4,
                'description': 'Overhead as % of total expenses. Overhead inflates per-unit costs.',
                'formula_description': '(Overhead Costs) ÷ (Total Operating Expenses)',
                'hcris_reference': '(B Pt I Col 26 Sum General Svcs) ÷ (G-3 Line 25)',
                'why_affects_parent': 'Overhead inflates per-unit costs',
                'improvement_levers': ['Reduce administrative costs', 'Improve efficiency', 'Consolidate functions'],
                'level_3_kpis': {
                    'Admin_General_Pct': {
                        'level': 3,
                        'name': 'A&G % of Total',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Administrative & general costs',
                        'formula_description': '(A&G Costs) ÷ (Total Operating Expenses)',
                        'hcris_reference': '(A Line 5 Col 7) ÷ (G-3 Line 25)'
                    },
                    'Maintenance_Pct': {
                        'level': 3,
                        'name': 'Maintenance %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Maintenance costs as % of expenses',
                        'formula_description': '(Maintenance Costs) ÷ (Total Operating Expenses)',
                        'hcris_reference': '(A Line 6 Col 7) ÷ (G-3 Line 25)'
                    }
                }
            },
            'Case_Mix_Index': {
                'level': 2,
                'name': 'Case Mix Index',
                'unit': 'index',
                'format': '.2f',
                'higher_is_better': True,
                'target_range': (1.2, 1.6),
                'impact_score': 8,
                'ease_of_change': 3,
                'description': 'Patient acuity measure. Higher acuity raises expenses per discharge.',
                'formula_description': 'Average DRG Weight',
                'hcris_reference': '(S-3 Pt I Line 1 Col 15)',
                'why_affects_parent': 'Higher acuity raises expenses per discharge',
                'improvement_levers': ['Improve coding accuracy', 'Document complexity', 'Focus on complex cases'],
                'level_3_kpis': {
                    'DRG_Weight_Average': {
                        'level': 3,
                        'name': 'DRG Weight Average',
                        'unit': 'index',
                        'format': '.2f',
                        'higher_is_better': True,
                        'description': 'Average DRG weight',
                        'formula_description': 'Average DRG Weight',
                        'hcris_reference': '(S-3 Pt I Line 1 Col 15)'
                    },
                    'Transfer_Adjusted_CMI': {
                        'level': 3,
                        'name': 'Transfer-Adjusted CMI',
                        'unit': 'index',
                        'format': '.2f',
                        'higher_is_better': True,
                        'description': 'CMI adjusted for transfers',
                        'formula_description': 'CMI Adjusted for Transfers',
                        'hcris_reference': '(S-3 Pt I Line 1 Col 15 Adjusted for Transfers)'
                    }
                }
            }
        }
    },

    # ========================================================================
    # LEVEL 1 KPI 4: Medicare Cost-to-Charge Ratio (CCR)
    # ========================================================================
    'Medicare_CCR': {
        'level': 1,
        'name': 'Medicare Cost-to-Charge Ratio',
        'category': 'Efficiency',
        'unit': 'ratio',
        'format': '.3f',
        'higher_is_better': False,
        'target_range': (0.2, 0.4),
        'impact_score': 7,
        'ease_of_change': 5,
        'description': 'Cost efficiency proxy. Lower CCR indicates better charge optimization.',
        'formula_description': '(Total Costs) ÷ (Total Charges)',
        'hcris_reference': '(C Pt I Col 5 Sum) ÷ (C Pt I Col 8 Sum)',
        'improvement_levers': ['Optimize charge master', 'Control costs', 'Improve efficiency'],
        'level_2_kpis': {
            'Ancillary_Cost_Ratio': {
                'level': 2,
                'name': 'Ancillary Cost Ratio',
                'unit': 'ratio',
                'format': '.3f',
                'higher_is_better': False,
                'target_range': (0.15, 0.35),
                'impact_score': 7,
                'ease_of_change': 5,
                'description': 'Ancillary costs as % of total costs. Ancillary drives CCR variability.',
                'formula_description': '(Ancillary Costs) ÷ (Total Costs)',
                'hcris_reference': '(C Pt I Lines 50-76 Col 5 Sum) ÷ (C Pt I Col 5 Total)',
                'why_affects_parent': 'Ancillary drives CCR variability',
                'improvement_levers': ['Optimize lab/radiology', 'Reduce unnecessary tests', 'Negotiate pricing'],
                'level_3_kpis': {
                    'Lab_CCR': {
                        'level': 3,
                        'name': 'Lab CCR',
                        'unit': 'ratio',
                        'format': '.3f',
                        'higher_is_better': False,
                        'description': 'Laboratory cost-to-charge ratio',
                        'formula_description': '(Lab Costs) ÷ (Lab Charges)',
                        'hcris_reference': '(C Pt I Line 60 Col 5) ÷ (C Pt I Line 60 Col 8)'
                    },
                    'Radiology_CCR': {
                        'level': 3,
                        'name': 'Radiology CCR',
                        'unit': 'ratio',
                        'format': '.3f',
                        'higher_is_better': False,
                        'description': 'Radiology cost-to-charge ratio',
                        'formula_description': '(Radiology Costs) ÷ (Radiology Charges)',
                        'hcris_reference': '(C Pt I Line 54 Col 5) ÷ (C Pt I Line 54 Col 8)'
                    }
                }
            },
            'Charge_Inflation_Rate': {
                'level': 2,
                'name': 'Charge Inflation Rate',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': True,
                'target_range': (2, 5),
                'impact_score': 6,
                'ease_of_change': 6,
                'description': 'Year-over-year charge growth. Rising charges lower CCR if costs lag.',
                'formula_description': 'YoY Change in Total Charges',
                'hcris_reference': 'YoY Change in (C Pt I Col 8 Sum)',
                'why_affects_parent': 'Rising charges lower CCR if costs lag',
                'improvement_levers': ['Annual charge updates', 'Market-based pricing', 'Service line review'],
                'level_3_kpis': {
                    'Inpatient_Charge_Pct': {
                        'level': 3,
                        'name': 'Inpatient Charge %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Inpatient charges as % of total',
                        'formula_description': '(Inpatient Charges) ÷ (Total Charges)',
                        'hcris_reference': '(C Pt I Col 6 Sum) ÷ (C Pt I Col 8 Sum)'
                    },
                    'Outpatient_Charge_Pct': {
                        'level': 3,
                        'name': 'Outpatient Charge %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': True,
                        'description': 'Outpatient charges as % of total',
                        'formula_description': '(Outpatient Charges) ÷ (Total Charges)',
                        'hcris_reference': '(C Pt I Col 7 Sum) ÷ (C Pt I Col 8 Sum)'
                    }
                }
            },
            'Adjustment_Impact_on_Costs': {
                'level': 2,
                'name': 'Adjustment Impact on Costs',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': False,
                'target_range': (1, 5),
                'impact_score': 6,
                'ease_of_change': 4,
                'description': 'Cost adjustments as % of total costs. Adjustments reduce allowable costs, raising CCR.',
                'formula_description': '(Total Adjustments) ÷ (Total Costs)',
                'hcris_reference': '(A-8 Col 2 Sum) ÷ (C Pt I Col 5 Sum)',
                'why_affects_parent': 'Adjustments reduce allowable costs, raising CCR',
                'improvement_levers': ['Minimize non-allowable costs', 'Improve documentation', 'Review cost reports'],
                'level_3_kpis': {
                    'Non_Allowable_Pct': {
                        'level': 3,
                        'name': 'Non-Allowable %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Non-allowable costs %',
                        'formula_description': '(Non-Allowable Costs) ÷ (Total Costs)',
                        'hcris_reference': '(A-8 Col 2 Negative Sum) ÷ (A Col 3 Sum)'
                    },
                    'RCE_Disallowance_Pct': {
                        'level': 3,
                        'name': 'RCE Disallowance %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Related cost entity disallowances',
                        'formula_description': '(RCE Disallowances) ÷ (Total Costs)',
                        'hcris_reference': '(A-8-2 Col 18 Sum) ÷ (C Pt I Col 5 Sum)'
                    }
                }
            },
            'Utilization_Mix': {
                'level': 2,
                'name': 'Utilization Mix',
                'unit': 'ratio',
                'format': '.2f',
                'higher_is_better': True,
                'target_range': (0.4, 0.6),
                'impact_score': 7,
                'ease_of_change': 4,
                'description': 'Outpatient visits as ratio to total. OP shift affects aggregate CCR.',
                'formula_description': '(OP Visits) ÷ (Total Adjusted Encounters)',
                'hcris_reference': '(S-3 Pt I Line 15 Col 1 OP Visits) ÷ (S-3 Pt I Line 1 Col 1 + Line 15 Col 1 Adjusted)',
                'why_affects_parent': 'OP shift affects aggregate CCR',
                'improvement_levers': ['Expand outpatient services', 'Shift procedures to outpatient', 'Build ambulatory capacity'],
                'level_3_kpis': {
                    'ER_Visit_Pct': {
                        'level': 3,
                        'name': 'ER Visit %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'ER visits as % of outpatient',
                        'formula_description': '(ER Visits) ÷ (Total OP Visits)',
                        'hcris_reference': '(S-3 Pt I Line 15 Col 1 ER Portion) ÷ (S-3 Pt I Line 15 Col 1)'
                    },
                    'Clinic_Visit_Pct': {
                        'level': 3,
                        'name': 'Clinic Visit %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': True,
                        'description': 'Clinic visits as % of outpatient',
                        'formula_description': '(Clinic Visits) ÷ (Total OP Costs)',
                        'hcris_reference': '(A Line 91 Col 7 Clinic) ÷ (C Pt I Col 5 OP Sum)'
                    }
                }
            }
        }
    },

    # ========================================================================
    # LEVEL 1 KPI 5: Bad Debt + Charity as % of Net Revenue
    # ========================================================================
    'Bad_Debt_Charity_Pct': {
        'level': 1,
        'name': 'Bad Debt + Charity %',
        'category': 'Revenue Cycle',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (3, 8),
        'impact_score': 8,
        'ease_of_change': 5,
        'description': 'Uncompensated care burden. Measures charity care and bad debt as % of revenue.',
        'formula_description': '(Bad Debt + Charity Care) ÷ (Net Revenue - Provisions)',
        'hcris_reference': '(S-10 Line 29 Col 3 + Line 23 Col 3) ÷ (G-3 Line 3 - Provisions)',
        'improvement_levers': ['Improve financial screening', 'Reduce bad debt', 'Optimize charity policies'],
        'level_2_kpis': {
            'Charity_Care_Charge_Ratio': {
                'level': 2,
                'name': 'Charity Care Charge Ratio',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': False,
                'target_range': (2, 6),
                'impact_score': 7,
                'ease_of_change': 5,
                'description': 'Charity care charges as % of total charges. High charity increases uncompensated %.',
                'formula_description': '(Charity Care Charges) ÷ (Total Charges)',
                'hcris_reference': '(S-10 Line 20 Col 3) ÷ (C Pt I Col 8 Sum)',
                'why_affects_parent': 'High charity increases uncompensated %',
                'improvement_levers': ['Improve financial screening', 'Expand Medicaid enrollment', 'Optimize charity policies'],
                'level_3_kpis': {
                    'Insured_Charity_Pct': {
                        'level': 3,
                        'name': 'Insured Charity %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Insured patients receiving charity care',
                        'formula_description': '(Insured Charity) ÷ (Total Charity)',
                        'hcris_reference': '(S-10 Line 20 Col 2) ÷ (S-10 Line 20 Col 3)'
                    },
                    'Non_Covered_Charity_Pct': {
                        'level': 3,
                        'name': 'Non-Covered Charity %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Non-covered services charity care',
                        'formula_description': '(Non-Covered Charity) ÷ (Total Charity)',
                        'hcris_reference': '(S-10 Line 20 Col 1) ÷ (S-10 Line 20 Col 3)'
                    }
                }
            },
            'Bad_Debt_Recovery_Rate': {
                'level': 2,
                'name': 'Bad Debt Recovery Rate',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': True,
                'target_range': (10, 30),
                'impact_score': 7,
                'ease_of_change': 6,
                'description': 'Bad debt recovered as % of total bad debt. Low recoveries inflate bad debt %.',
                'formula_description': '(Bad Debt Recovered) ÷ (Total Bad Debt)',
                'hcris_reference': '(S-10 Line 26) ÷ (S-10 Line 25)',
                'why_affects_parent': 'Low recoveries inflate bad debt %',
                'improvement_levers': ['Improve collections', 'Use collection agencies', 'Better credit screening'],
                'level_3_kpis': {
                    'Medicare_Bad_Debt_Pct': {
                        'level': 3,
                        'name': 'Medicare Bad Debt %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Medicare bad debt share',
                        'formula_description': '(Medicare Bad Debt) ÷ (Total Bad Debt)',
                        'hcris_reference': '(E Pt A Line 64) ÷ (S-10 Line 25)'
                    },
                    'Non_Medicare_Bad_Debt_Pct': {
                        'level': 3,
                        'name': 'Non-Medicare Bad Debt %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Non-Medicare bad debt share',
                        'formula_description': '(Non-Medicare Bad Debt) ÷ (Total Bad Debt)',
                        'hcris_reference': '(S-10 Line 25 - E Pt A Line 64) ÷ (S-10 Line 25)'
                    }
                }
            },
            'Uninsured_Patient_Pct': {
                'level': 2,
                'name': 'Uninsured Patient %',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': False,
                'target_range': (5, 15),
                'impact_score': 8,
                'ease_of_change': 4,
                'description': 'Uninsured patients as % of total. Uninsured drive charity/bad debt.',
                'formula_description': '(Uninsured Encounters) ÷ (Total Encounters)',
                'hcris_reference': '(S-10 Line 20 Col 1 + Line 31) ÷ (S-3 Pt I Line 14 Col 8)',
                'why_affects_parent': 'Uninsured drive charity/bad debt',
                'improvement_levers': ['Expand Medicaid', 'Financial counseling', 'Community outreach'],
                'level_3_kpis': {
                    'Uninsured_Inpatient_Pct': {
                        'level': 3,
                        'name': 'Uninsured Inpatient %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Uninsured inpatient share',
                        'formula_description': '(Uninsured Inpatient Days) ÷ (Total Inpatient Days)',
                        'hcris_reference': '(S-10 Inpatient Portion Derived) ÷ (S-3 Pt I Line 8 Col 8)'
                    },
                    'Uninsured_OP_Pct': {
                        'level': 3,
                        'name': 'Uninsured OP %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Uninsured outpatient share',
                        'formula_description': '(Uninsured OP Visits) ÷ (Total OP Visits)',
                        'hcris_reference': '(S-10 OP Portion) ÷ (S-3 Pt I Line 15 Col 1)'
                    }
                }
            },
            'Medicaid_Shortfall_Pct': {
                'level': 2,
                'name': 'Medicaid Shortfall %',
                'category': 'Revenue Cycle',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': False,
                'target_range': (0, 5),
                'impact_score': 7,
                'ease_of_change': 3,
                'description': 'Medicaid payment shortfall as % of revenue. Shortfalls add to uncompensated load.',
                'formula_description': '(Medicaid Cost - Medicaid Payment) ÷ (Total Revenue)',
                'hcris_reference': '(S-10 Line 18 - Line 19) ÷ (G-3 Line 3)',
                'why_affects_parent': 'Shortfalls add to uncompensated load',
                'improvement_levers': ['Advocate for rate increases', 'Improve Medicaid efficiency', 'Optimize coding'],
                'level_3_kpis': {
                    'Medicaid_Days_Pct': {
                        'level': 3,
                        'name': 'Medicaid Days %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Medicaid patient days share',
                        'formula_description': '(Medicaid Days) ÷ (Total Patient Days)',
                        'hcris_reference': '(S-3 Pt I Line 14 Col 5+6) ÷ (S-3 Pt I Line 14 Col 8)'
                    },
                    'Medicaid_Payment_to_Cost': {
                        'level': 3,
                        'name': 'Medicaid Payment-to-Cost',
                        'unit': 'ratio',
                        'format': '.2f',
                        'higher_is_better': True,
                        'description': 'Medicaid payment adequacy',
                        'formula_description': '(Medicaid Payment) ÷ (Medicaid Cost)',
                        'hcris_reference': '(S-10 Line 18) ÷ (S-10 Line 19)'
                    }
                }
            }
        }
    },

    # ========================================================================
    # LEVEL 1 KPI 6: Current Ratio (Unrestricted)
    # ========================================================================
    'Current_Ratio': {
        'level': 1,
        'name': 'Current Ratio',
        'category': 'Liquidity',
        'unit': 'ratio',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (1.5, 2.5),
        'impact_score': 9,
        'ease_of_change': 5,
        'description': 'Short-term liquidity. Ability to meet current obligations with current assets.',
        'formula_description': '(Current Assets Unrestricted) ÷ (Current Liabilities)',
        'hcris_reference': '(G Balance Sheet Line 1-12 Col 3 Sum Unrestricted) ÷ (G Line 46-58 Col 3 Sum)',
        'improvement_levers': ['Build cash reserves', 'Improve collections', 'Manage payables'],
        'level_2_kpis': {
            'Cash_Equivalents_Pct_of_Assets': {
                'level': 2,
                'name': 'Cash + Equivalents % of Assets',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': True,
                'target_range': (10, 30),
                'impact_score': 8,
                'ease_of_change': 5,
                'description': 'Cash and equivalents as % of total assets. Boosts current assets for liquidity.',
                'formula_description': '(Cash + Marketable Securities) ÷ (Total Assets)',
                'hcris_reference': '(G Line 1+2 Col 3) ÷ (G Line 59 Col 3)',
                'why_affects_parent': 'Boosts current assets for liquidity',
                'improvement_levers': ['Build reserves', 'Retain earnings', 'Optimize cash management'],
                'level_3_kpis': {
                    'Operating_Cash_Flow': {
                        'level': 3,
                        'name': 'Operating Cash Flow',
                        'unit': '$M',
                        'format': '.1f',
                        'higher_is_better': True,
                        'description': 'Cash flow from operations',
                        'formula_description': '(Cash from Operations) ÷ (Cash + Equivalents)',
                        'hcris_reference': '(G-1 Line 1 Col 3) ÷ (G Line 1+2 Col 3)'
                    },
                    'Investment_Returns': {
                        'level': 3,
                        'name': 'Investment Returns',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': True,
                        'description': 'Investment income returns',
                        'formula_description': '(Investment Income) ÷ (Investments)',
                        'hcris_reference': '(G-1 Line 5 Col 3) ÷ (G Line 39 Col 3)'
                    }
                }
            },
            'Current_Liabilities_Ratio': {
                'level': 2,
                'name': 'Current Liabilities Ratio',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': False,
                'target_range': (20, 40),
                'impact_score': 7,
                'ease_of_change': 5,
                'description': 'Current liabilities as % of total liabilities. High liabilities strain ratio.',
                'formula_description': '(Current Liabilities) ÷ (Total Liabilities)',
                'hcris_reference': '(G Line 46-58 Col 3 Sum) ÷ (G Line 75 Col 3)',
                'why_affects_parent': 'High liabilities strain ratio',
                'improvement_levers': ['Extend payment terms', 'Refinance short-term debt', 'Manage payables'],
                'level_3_kpis': {
                    'Accounts_Payable_Pct': {
                        'level': 3,
                        'name': 'Accounts Payable %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'AP as % of current liabilities',
                        'formula_description': '(Accounts Payable) ÷ (Current Liabilities)',
                        'hcris_reference': '(G Line 47 Col 3) ÷ (G Line 46-58 Sum)'
                    },
                    'Short_Term_Debt_Pct': {
                        'level': 3,
                        'name': 'Short-Term Debt %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Short-term debt as % of current liabilities',
                        'formula_description': '(Short-Term Debt) ÷ (Current Liabilities)',
                        'hcris_reference': '(G Line 46 Col 3) ÷ (G Line 46-58 Sum)'
                    }
                }
            },
            'Inventory_Turnover': {
                'level': 2,
                'name': 'Inventory Turnover',
                'unit': 'ratio',
                'format': '.1f',
                'higher_is_better': True,
                'target_range': (20, 40),
                'impact_score': 6,
                'ease_of_change': 6,
                'description': 'Inventory efficiency. Low turnover ties up current assets.',
                'formula_description': '(Supply Expense) ÷ (Average Inventory)',
                'hcris_reference': '(A Line 71 Col 2 Supplies) ÷ (G Inventory Avg from Beg/End)',
                'why_affects_parent': 'Ties up current assets if low',
                'improvement_levers': ['Reduce inventory levels', 'Implement JIT', 'Improve supply chain'],
                'level_3_kpis': {
                    'Supply_Expense_Pct': {
                        'level': 3,
                        'name': 'Supply Expense %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Supply expenses as % of total',
                        'formula_description': '(Supply Expenses) ÷ (Total Operating Expenses)',
                        'hcris_reference': '(A Line 71 Col 7) ÷ (G-3 Line 25)'
                    },
                    'Days_in_Inventory': {
                        'level': 3,
                        'name': 'Days in Inventory',
                        'unit': 'days',
                        'format': '.0f',
                        'higher_is_better': False,
                        'description': 'Average days inventory on hand',
                        'formula_description': '(Inventory) ÷ (Supply Expense / 365)',
                        'hcris_reference': '(G Line 4 Col 3) ÷ ((A Line 71 Col 2) ÷ 365)'
                    }
                }
            },
            'Fund_Balance_Pct_Change': {
                'level': 2,
                'name': 'Fund Balance % Change',
                'unit': '%',
                'format': '.1f',
                'higher_is_better': True,
                'target_range': (2, 8),
                'impact_score': 7,
                'ease_of_change': 4,
                'description': 'Change in fund balance as % of beginning balance. Positive changes build reserves.',
                'formula_description': '(Change in Fund Balance) ÷ (Beginning Fund Balance)',
                'hcris_reference': '(G-1 Line 21 Col 3) ÷ (G Line 70 Col 3 Beg)',
                'why_affects_parent': 'Positive changes build reserves',
                'improvement_levers': ['Improve profitability', 'Retain earnings', 'Build reserves'],
                'level_3_kpis': {
                    'Retained_Earnings_Pct': {
                        'level': 3,
                        'name': 'Retained Earnings %',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': True,
                        'description': 'Retained earnings as % of total liabilities',
                        'formula_description': '(Retained Earnings) ÷ (Total Liabilities)',
                        'hcris_reference': '(G Line 73 Col 3) ÷ (G Line 75 Col 3)'
                    },
                    'Depreciation_Impact': {
                        'level': 3,
                        'name': 'Depreciation Impact',
                        'unit': '%',
                        'format': '.1f',
                        'higher_is_better': False,
                        'description': 'Depreciation as % of fund balance change',
                        'formula_description': '(Depreciation) ÷ (Fund Balance Change)',
                        'hcris_reference': '(G-1 Line 3 Col 3) ÷ (G-1 Line 21 Col 3)'
                    }
                }
            }
        }
    }
}


# Backward compatibility: create flat metadata dictionary
KPI_METADATA = {}


def flatten_kpi_hierarchy(hierarchy=None, parent_key=''):
    """
    Flatten the hierarchical KPI structure for backward compatibility
    Creates a flat dictionary with all KPIs at all levels
    """
    if hierarchy is None:
        hierarchy = KPI_HIERARCHY

    flat_dict = {}

    for key, value in hierarchy.items():
        if isinstance(value, dict) and 'level' in value:
            # Add this KPI to flat dictionary
            flat_dict[key] = {k: v for k, v in value.items() if k != 'level_2_kpis'}

            # Recursively flatten Level 2 KPIs
            if 'level_2_kpis' in value:
                for l2_key, l2_value in value['level_2_kpis'].items():
                    flat_dict[l2_key] = {k: v for k, v in l2_value.items() if k != 'level_3_kpis'}

                    # Recursively flatten Level 3 KPIs
                    if 'level_3_kpis' in l2_value:
                        for l3_key, l3_value in l2_value['level_3_kpis'].items():
                            flat_dict[l3_key] = l3_value

    return flat_dict


# Create flat metadata for backward compatibility
KPI_METADATA = flatten_kpi_hierarchy()


def get_level_1_kpis():
    """Get all Level 1 KPIs"""
    return {k: v for k, v in KPI_HIERARCHY.items() if v.get('level') == 1}


def get_level_2_kpis(level_1_key):
    """Get Level 2 KPIs for a specific Level 1 KPI"""
    if level_1_key in KPI_HIERARCHY and 'level_2_kpis' in KPI_HIERARCHY[level_1_key]:
        return KPI_HIERARCHY[level_1_key]['level_2_kpis']
    return {}


def get_level_3_kpis(level_1_key, level_2_key):
    """Get Level 3 KPIs for a specific Level 2 KPI"""
    if level_1_key in KPI_HIERARCHY:
        level_2_kpis = KPI_HIERARCHY[level_1_key].get('level_2_kpis', {})
        if level_2_key in level_2_kpis and 'level_3_kpis' in level_2_kpis[level_2_key]:
            return level_2_kpis[level_2_key]['level_3_kpis']
    return {}


def get_kpi_lineage(kpi_key):
    """
    Get the hierarchical lineage of a KPI
    Returns: {'level': 1/2/3, 'parent_l1': key, 'parent_l2': key}
    """
    # Check if it's a Level 1 KPI
    if kpi_key in KPI_HIERARCHY:
        return {'level': 1, 'parent_l1': None, 'parent_l2': None}

    # Check Level 2 and 3
    for l1_key, l1_value in KPI_HIERARCHY.items():
        if 'level_2_kpis' in l1_value:
            # Check if it's a Level 2 KPI
            if kpi_key in l1_value['level_2_kpis']:
                return {'level': 2, 'parent_l1': l1_key, 'parent_l2': None}

            # Check Level 3
            for l2_key, l2_value in l1_value['level_2_kpis'].items():
                if 'level_3_kpis' in l2_value and kpi_key in l2_value['level_3_kpis']:
                    return {'level': 3, 'parent_l1': l1_key, 'parent_l2': l2_key}

    return {'level': None, 'parent_l1': None, 'parent_l2': None}
