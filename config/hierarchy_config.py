"""
Hierarchy Configuration - Card Tree Structures
===============================================

This module defines how cards are organized into hierarchical trees.
Cards can be reused in multiple trees and hierarchies can be easily modified.

Hierarchies are defined separately from card definitions, allowing:
- Easy restructuring of card relationships
- Multiple different tree structures for same cards
- A/B testing of different hierarchies
- Custom hierarchies per user/role
"""

# ============================================================================
# DEFAULT KPI HIERARCHY (3 Levels)
# ============================================================================

DEFAULT_KPI_HIERARCHY = {
    'Net_Income_Margin': {
        'level': 1,
        'rank': 1,
        'impact_score': 10,
        'ease_of_change': 4,
        'children': [
            {
                'card_id': 'Operating_Expense_Ratio',
                'level': 2,
                'rank': 1,
                'impact_score': 9,
                'ease_of_change': 5,
                'children': [
                    {'card_id': 'FTE_per_Bed', 'level': 3, 'rank': 1},
                    {'card_id': 'Salary_Pct_of_Expenses', 'level': 3, 'rank': 2}
                ]
            },
            {
                'card_id': 'Non_Operating_Income_Pct',
                'level': 2,
                'rank': 2,
                'impact_score': 7,
                'ease_of_change': 3,
                'children': [
                    {'card_id': 'Investment_Income_Share', 'level': 3, 'rank': 1},
                    {'card_id': 'Donation_Grant_Pct', 'level': 3, 'rank': 2}
                ]
            },
            {
                'card_id': 'Payer_Mix_Medicare_Pct',
                'level': 2,
                'rank': 3,
                'impact_score': 8,
                'ease_of_change': 3,
                'children': [
                    {'card_id': 'Medicare_Inpatient_Days_Pct', 'level': 3, 'rank': 1},
                    {'card_id': 'Medicare_Outpatient_Revenue_Pct', 'level': 3, 'rank': 2}
                ]
            },
            {
                'card_id': 'Capital_Cost_Pct_of_Expenses',
                'level': 2,
                'rank': 4,
                'impact_score': 6,
                'ease_of_change': 2,
                'children': [
                    {'card_id': 'Depreciation_Pct_of_Capital', 'level': 3, 'rank': 1},
                    {'card_id': 'Interest_Expense_Ratio', 'level': 3, 'rank': 2}
                ]
            }
        ]
    },

    'AR_Days': {
        'level': 1,
        'rank': 2,
        'impact_score': 9,
        'ease_of_change': 7,
        'children': [
            {
                'card_id': 'Denial_Rate',
                'level': 2,
                'rank': 1,
                'impact_score': 8,
                'ease_of_change': 6,
                'children': [
                    {'card_id': 'Medicare_Denial_Pct', 'level': 3, 'rank': 1},
                    {'card_id': 'Non_Medicare_Adjustment_Pct', 'level': 3, 'rank': 2}
                ]
            },
            {
                'card_id': 'Payer_Mix_Commercial_Pct',
                'level': 2,
                'rank': 2,
                'impact_score': 7,
                'ease_of_change': 4,
                'children': [
                    {'card_id': 'Commercial_Inpatient_Pct', 'level': 3, 'rank': 1},
                    {'card_id': 'Self_Pay_Pct', 'level': 3, 'rank': 2}
                ]
            },
            {
                'card_id': 'Billing_Efficiency_Ratio',
                'level': 2,
                'rank': 3,
                'impact_score': 7,
                'ease_of_change': 6,
                'children': []
            },
            {
                'card_id': 'Collection_Rate',
                'level': 2,
                'rank': 4,
                'impact_score': 9,
                'ease_of_change': 6,
                'children': []
            }
        ]
    },

    'Operating_Expense_per_Adjusted_Discharge': {
        'level': 1,
        'rank': 3,
        'impact_score': 9,
        'ease_of_change': 6,
        'children': [
            {
                'card_id': 'Labor_Cost_per_Discharge',
                'level': 2,
                'rank': 1,
                'impact_score': 9,
                'ease_of_change': 5,
                'children': []
            },
            {
                'card_id': 'Supply_Cost_per_Discharge',
                'level': 2,
                'rank': 2,
                'impact_score': 8,
                'ease_of_change': 6,
                'children': []
            },
            {
                'card_id': 'Overhead_Allocation_Ratio',
                'level': 2,
                'rank': 3,
                'impact_score': 7,
                'ease_of_change': 4,
                'children': []
            },
            {
                'card_id': 'Case_Mix_Index',
                'level': 2,
                'rank': 4,
                'impact_score': 8,
                'ease_of_change': 3,
                'children': []
            }
        ]
    },

    'Medicare_CCR': {
        'level': 1,
        'rank': 4,
        'impact_score': 7,
        'ease_of_change': 5,
        'children': []  # Add L2 children as needed
    },

    'Bad_Debt_Charity_Pct': {
        'level': 1,
        'rank': 5,
        'impact_score': 8,
        'ease_of_change': 5,
        'children': []  # Add L2 children as needed
    },

    'Current_Ratio': {
        'level': 1,
        'rank': 6,
        'impact_score': 9,
        'ease_of_change': 5,
        'children': []  # Add L2 children as needed
    }
}


# ============================================================================
# ALTERNATIVE HIERARCHIES (Examples)
# ============================================================================

# Cost-focused hierarchy
COST_FOCUSED_HIERARCHY = {
    'Operating_Expense_per_Adjusted_Discharge': {
        'level': 1,
        'rank': 1,
        'children': [
            {'card_id': 'Labor_Cost_per_Discharge', 'level': 2, 'rank': 1, 'children': []},
            {'card_id': 'Supply_Cost_per_Discharge', 'level': 2, 'rank': 2, 'children': []},
            {'card_id': 'Overhead_Allocation_Ratio', 'level': 2, 'rank': 3, 'children': []}
        ]
    },
    'Operating_Expense_Ratio': {
        'level': 1,
        'rank': 2,
        'children': []
    },
    'Capital_Cost_Pct_of_Expenses': {
        'level': 1,
        'rank': 3,
        'children': []
    }
}

# Revenue-focused hierarchy
REVENUE_FOCUSED_HIERARCHY = {
    'AR_Days': {
        'level': 1,
        'rank': 1,
        'children': [
            {'card_id': 'Denial_Rate', 'level': 2, 'rank': 1, 'children': []},
            {'card_id': 'Collection_Rate', 'level': 2, 'rank': 2, 'children': []},
            {'card_id': 'Billing_Efficiency_Ratio', 'level': 2, 'rank': 3, 'children': []}
        ]
    },
    'Non_Operating_Income_Pct': {
        'level': 1,
        'rank': 2,
        'children': []
    },
    'Payer_Mix_Commercial_Pct': {
        'level': 1,
        'rank': 3,
        'children': []
    }
}


# ============================================================================
# HIERARCHY UTILITIES
# ============================================================================

def get_hierarchy(hierarchy_name='default'):
    """
    Get a named hierarchy configuration

    Args:
        hierarchy_name: Name of hierarchy ('default', 'cost_focused', 'revenue_focused')

    Returns:
        Hierarchy configuration dict
    """
    hierarchies = {
        'default': DEFAULT_KPI_HIERARCHY,
        'cost_focused': COST_FOCUSED_HIERARCHY,
        'revenue_focused': REVENUE_FOCUSED_HIERARCHY
    }

    return hierarchies.get(hierarchy_name, DEFAULT_KPI_HIERARCHY)


def get_level_1_cards(hierarchy_name='default'):
    """Get all Level 1 card IDs from a hierarchy"""
    hierarchy = get_hierarchy(hierarchy_name)
    return list(hierarchy.keys())


def get_children(card_id, hierarchy_name='default'):
    """
    Get all child cards for a given card

    Args:
        card_id: Parent card ID
        hierarchy_name: Hierarchy to search

    Returns:
        List of child card configurations
    """
    hierarchy = get_hierarchy(hierarchy_name)

    # Check if card_id is a Level 1 card
    if card_id in hierarchy:
        return hierarchy[card_id].get('children', [])

    # Search in Level 2 cards
    for l1_card_id, l1_config in hierarchy.items():
        for l2_child in l1_config.get('children', []):
            if l2_child.get('card_id') == card_id:
                return l2_child.get('children', [])

    return []


def get_parent(card_id, hierarchy_name='default'):
    """
    Get the parent card ID for a given card

    Args:
        card_id: Card ID to find parent for
        hierarchy_name: Hierarchy to search

    Returns:
        Parent card ID or None
    """
    hierarchy = get_hierarchy(hierarchy_name)

    # Check if it's a Level 1 card (no parent)
    if card_id in hierarchy:
        return None

    # Search in Level 2 cards
    for l1_card_id, l1_config in hierarchy.items():
        for l2_child in l1_config.get('children', []):
            if l2_child.get('card_id') == card_id:
                return l1_card_id

            # Search in Level 3 cards
            for l3_child in l2_child.get('children', []):
                if l3_child.get('card_id') == card_id:
                    return l2_child.get('card_id')

    return None


def get_lineage(card_id, hierarchy_name='default'):
    """
    Get the full lineage path for a card (from root to card)

    Args:
        card_id: Card ID
        hierarchy_name: Hierarchy to search

    Returns:
        List of card IDs from root to card, e.g., ['Net_Income_Margin', 'Operating_Expense_Ratio', 'FTE_per_Bed']
    """
    hierarchy = get_hierarchy(hierarchy_name)

    # Level 1 card
    if card_id in hierarchy:
        return [card_id]

    # Level 2/3 cards - build lineage
    for l1_card_id, l1_config in hierarchy.items():
        for l2_child in l1_config.get('children', []):
            if l2_child.get('card_id') == card_id:
                return [l1_card_id, card_id]

            for l3_child in l2_child.get('children', []):
                if l3_child.get('card_id') == card_id:
                    return [l1_card_id, l2_child.get('card_id'), card_id]

    return []


def get_all_descendants(card_id, hierarchy_name='default'):
    """
    Get all descendant cards (children, grandchildren, etc.)

    Args:
        card_id: Parent card ID
        hierarchy_name: Hierarchy to search

    Returns:
        List of all descendant card IDs
    """
    descendants = []
    children = get_children(card_id, hierarchy_name)

    for child in children:
        child_id = child.get('card_id')
        descendants.append(child_id)
        # Recursively get grandchildren
        descendants.extend(get_all_descendants(child_id, hierarchy_name))

    return descendants


def flatten_hierarchy(hierarchy_name='default'):
    """
    Flatten a hierarchy into a simple dict mapping card IDs to their metadata

    Returns:
        Dict with keys as card IDs and values as metadata (level, rank, etc.)
    """
    hierarchy = get_hierarchy(hierarchy_name)
    flat = {}

    for l1_card_id, l1_config in hierarchy.items():
        flat[l1_card_id] = {
            'level': l1_config.get('level'),
            'rank': l1_config.get('rank'),
            'impact_score': l1_config.get('impact_score'),
            'ease_of_change': l1_config.get('ease_of_change'),
            'parent': None
        }

        for l2_child in l1_config.get('children', []):
            l2_card_id = l2_child.get('card_id')
            flat[l2_card_id] = {
                'level': l2_child.get('level'),
                'rank': l2_child.get('rank'),
                'impact_score': l2_child.get('impact_score'),
                'ease_of_change': l2_child.get('ease_of_change'),
                'parent': l1_card_id
            }

            for l3_child in l2_child.get('children', []):
                l3_card_id = l3_child.get('card_id')
                flat[l3_card_id] = {
                    'level': l3_child.get('level'),
                    'rank': l3_child.get('rank'),
                    'parent': l2_card_id
                }

    return flat
