## Modular KPI Card System

### Overview

The KPI card system has been refactored into a modular architecture that separates:

1. **Card Definitions** (`config/card_registry.py`) - What cards exist
2. **Hierarchy Configuration** (`config/hierarchy_config.py`) - How cards are organized
3. **Card Builder** (`components/card_builder.py`) - How cards are created

This makes it easy to:
- Add new cards without touching hierarchy code
- Reorganize hierarchies without changing card code
- Reuse cards in multiple trees
- A/B test different hierarchies
- Create custom views per user/role

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CARD REGISTRY                            │
│  (card_registry.py)                                         │
│                                                              │
│  Defines WHAT each card is:                                 │
│  - Name, category, unit, format                            │
│  - Description, formula                                     │
│  - Target ranges, improvement levers                        │
│  - Calculation components                                   │
│                                                              │
│  Cards are completely independent                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  HIERARCHY CONFIGURATION                     │
│  (hierarchy_config.py)                                      │
│                                                              │
│  Defines HOW cards are organized:                           │
│  - Tree structure (parent-child relationships)             │
│  - Level assignment (L1, L2, L3)                           │
│  - Ranking within levels                                    │
│  - Impact scores, ease of change                            │
│                                                              │
│  Multiple hierarchies can exist for same cards              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      CARD BUILDER                            │
│  (card_builder.py)                                          │
│                                                              │
│  Creates card components:                                    │
│  - Fetches card definition from registry                   │
│  - Applies hierarchy metadata (level, rank)                │
│  - Builds UI component using template                       │
│  - Handles data binding (values, trends, benchmarks)        │
│                                                              │
│  Factory pattern for card creation                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### 1. Adding a New Card

**Step 1:** Add card definition to `card_registry.py`

```python
# config/card_registry.py

CARD_REGISTRY = {
    # ... existing cards ...

    'New_Card_Name': {
        'name': 'My New KPI',
        'category': 'Efficiency',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (10, 20),
        'description': 'Measures efficiency of operations',
        'formula_description': '(Output) ÷ (Input)',
        'improvement_levers': ['Improve process', 'Reduce waste']
    }
}
```

**Step 2:** Add to hierarchy (if needed) in `hierarchy_config.py`

```python
# config/hierarchy_config.py

DEFAULT_KPI_HIERARCHY = {
    'Operating_Expense_per_Adjusted_Discharge': {
        'level': 1,
        'rank': 3,
        'children': [
            {
                'card_id': 'New_Card_Name',  # ← Add here
                'level': 2,
                'rank': 5,
                'children': []
            }
        ]
    }
}
```

**Done!** The card is now available for use.

---

### 2. Building a Single Card

```python
from components.card_builder import build_card

# Build a single card
card = build_card(
    card_id='Net_Income_Margin',
    kpi_value=5.2,
    kpi_trend_values=[4.8, 4.9, 5.0, 5.1, 5.2],
    fiscal_years=[2020, 2021, 2022, 2023, 2024],
    benchmark_data=benchmark_data,
    hierarchy_name='default',
    template='enhanced'
)
```

---

### 3. Building Multiple Cards (Grid)

```python
from components.card_builder import CardBuilder

# Initialize builder
builder = CardBuilder(hierarchy_name='default')

# Build a grid of cards
card_grid = builder.build_card_grid(
    card_ids=['Net_Income_Margin', 'AR_Days', 'Current_Ratio'],
    values_dict={
        'Net_Income_Margin': 5.2,
        'AR_Days': 45.0,
        'Current_Ratio': 2.1
    },
    trends_dict={
        'Net_Income_Margin': [4.8, 4.9, 5.0, 5.1, 5.2],
        'AR_Days': [48, 47, 46, 45.5, 45],
        'Current_Ratio': [1.9, 2.0, 2.0, 2.1, 2.1]
    },
    years_dict={
        'Net_Income_Margin': [2020, 2021, 2022, 2023, 2024],
        'AR_Days': [2020, 2021, 2022, 2023, 2024],
        'Current_Ratio': [2020, 2021, 2022, 2023, 2024]
    },
    benchmarks_dict=benchmarks_dict,
    template='basic',
    columns=3
)
```

---

### 4. Building All Cards for a Level

```python
# Build all Level 1 cards
level_1_layout = builder.build_level_cards(
    level=1,
    values_dict=values,
    trends_dict=trends,
    years_dict=years,
    benchmarks_dict=benchmarks,
    template='enhanced'
)
```

---

### 5. Using Different Hierarchies

```python
# Use cost-focused hierarchy
cost_builder = CardBuilder(hierarchy_name='cost_focused')

# Use revenue-focused hierarchy
revenue_builder = CardBuilder(hierarchy_name='revenue_focused')

# Same cards, different organizations!
```

---

### 6. Creating a Custom Hierarchy

```python
# config/hierarchy_config.py

CUSTOM_CFO_HIERARCHY = {
    'Current_Ratio': {
        'level': 1,
        'rank': 1,
        'children': [
            {'card_id': 'AR_Days', 'level': 2, 'rank': 1, 'children': []},
            {'card_id': 'Collection_Rate', 'level': 2, 'rank': 2, 'children': []}
        ]
    },
    'Net_Income_Margin': {
        'level': 1,
        'rank': 2,
        'children': [
            {'card_id': 'Operating_Expense_Ratio', 'level': 2, 'rank': 1, 'children': []}
        ]
    }
}

# Then use it
cfo_builder = CardBuilder(hierarchy_name='cfo_focused')
```

---

### 7. Querying Card Metadata

```python
from config.card_registry import CARD_REGISTRY
from config.hierarchy_config import get_children, get_lineage

# Get card definition
card_def = CARD_REGISTRY['Net_Income_Margin']
print(card_def['description'])
print(card_def['formula_description'])

# Get card's children in hierarchy
children = get_children('Net_Income_Margin', hierarchy_name='default')
print(f"Children: {[c['card_id'] for c in children]}")

# Get card's lineage (path from root)
lineage = get_lineage('FTE_per_Bed', hierarchy_name='default')
print(f"Lineage: {lineage}")
# Output: ['Net_Income_Margin', 'Operating_Expense_Ratio', 'FTE_per_Bed']
```

---

## Benefits

### ✅ Easy to Add New Cards

1. Add definition to `CARD_REGISTRY`
2. Add to hierarchy if needed
3. Done!

No need to modify card creation functions or touch multiple files.

### ✅ Easy to Reorganize

Want to move a card from one parent to another?
- Edit `hierarchy_config.py` only
- No changes to card code

### ✅ Reusable Cards

Same card can appear in multiple hierarchies:
- Default hierarchy
- Cost-focused hierarchy
- Revenue-focused hierarchy
- Custom per-user hierarchies

### ✅ Easy Testing

Test different organizations:
```python
# A/B test hierarchies
hierarchy_a = CardBuilder('version_a')
hierarchy_b = CardBuilder('version_b')

# Same data, different structures
layout_a = hierarchy_a.build_level_cards(1, data...)
layout_b = hierarchy_b.build_level_cards(1, data...)
```

### ✅ Role-Based Views

```python
# Different hierarchies for different roles
if user.role == 'CFO':
    builder = CardBuilder('cfo_focused')
elif user.role == 'COO':
    builder = CardBuilder('operations_focused')
else:
    builder = CardBuilder('default')
```

---

## Templates

The card builder supports multiple templates:

### `basic` Template
- Simple card with value, trend, sparkline
- Benchmark comparison bar
- Compact design

### `enhanced` Template
- Full benchmark table (all 4 levels)
- Historical quartile coloring
- Calculation components display
- Drill-down button
- Rich tooltips

### `hierarchical` Template
- Expandable child KPIs
- Multi-level drill-down
- Driver analysis
- Impact scores

Usage:
```python
card = build_card(..., template='enhanced')
```

---

## Migration from Old System

The old system (`kpi_hierarchy_config.py`) is still supported for backward compatibility.

### Old Way (Hard-coded hierarchy):
```python
from kpi_hierarchy_config import KPI_HIERARCHY, KPI_METADATA

# Hierarchy embedded in metadata
meta = KPI_METADATA['Net_Income_Margin']
l2_kpis = KPI_HIERARCHY['Net_Income_Margin']['level_2_kpis']
```

### New Way (Modular):
```python
from config.card_registry import CARD_REGISTRY
from config.hierarchy_config import get_children

# Card definition separate from hierarchy
card_def = CARD_REGISTRY['Net_Income_Margin']
children = get_children('Net_Income_Margin')
```

### Gradual Migration

1. Keep using old system for existing pages
2. Use new system for new features
3. Gradually migrate old pages to new system
4. Eventually deprecate old system

---

## File Structure

```
Hospital-Dashboard/
├── config/
│   ├── card_registry.py           # Card definitions (independent)
│   └── hierarchy_config.py         # Tree structures (relationships)
│
├── components/
│   ├── card_builder.py             # Card factory
│   └── kpi_cards.py                # Legacy card functions (deprecated)
│
└── kpi_hierarchy_config.py         # Legacy (backward compatibility)
```

---

## Best Practices

### 1. Keep Cards Independent

Cards should not reference their hierarchy:
```python
# ❌ Bad - card knows about hierarchy
CARD_REGISTRY = {
    'My_Card': {
        'parent': 'Some_Other_Card',  # Don't do this
        'level': 2  # Don't do this
    }
}

# ✅ Good - card is self-contained
CARD_REGISTRY = {
    'My_Card': {
        'name': 'My KPI',
        'description': '...',
        'formula': '...'
    }
}
```

### 2. Put Hierarchy Info in Hierarchy Config

```python
# ✅ Good - hierarchy in hierarchy_config.py
DEFAULT_KPI_HIERARCHY = {
    'Parent_Card': {
        'level': 1,
        'children': [
            {'card_id': 'My_Card', 'level': 2, 'rank': 1}
        ]
    }
}
```

### 3. Use CardBuilder for Consistency

```python
# ❌ Bad - direct card creation
card = create_kpi_card(...)  # Old way

# ✅ Good - use builder
builder = CardBuilder()
card = builder.build_card(...)  # New way
```

### 4. Version Your Hierarchies

```python
# Support multiple versions
HIERARCHY_V1 = {...}
HIERARCHY_V2 = {...}

# Easy rollback if needed
```

---

## Advanced Usage

### Dynamic Hierarchies from Database

```python
def get_user_hierarchy(user_id):
    """Load user's custom hierarchy from database"""
    hierarchy = db.query(f"SELECT hierarchy FROM users WHERE id={user_id}")
    return hierarchy

# Use custom hierarchy
builder = CardBuilder(hierarchy_name=get_user_hierarchy(current_user_id))
```

### Filtering Cards

```python
from config.card_registry import get_card_by_category

# Get only cost management cards
cost_cards = get_card_by_category('Cost Management')

# Build only those cards
builder.build_card_grid(
    card_ids=list(cost_cards.keys()),
    ...
)
```

### Custom Card Templates

```python
class MyCardBuilder(CardBuilder):
    def _build_custom_template(self, card_data, ...):
        """Custom template for special cards"""
        return html.Div([...])

# Use custom builder
builder = MyCardBuilder()
card = builder.build_card(..., template='custom')
```

---

## Summary

The modular card system provides:

- **Separation of Concerns**: Cards, hierarchies, and display are independent
- **Flexibility**: Easy to add, modify, reorganize
- **Reusability**: Same cards in multiple contexts
- **Testability**: Easy A/B testing and experimentation
- **Maintainability**: Changes are localized
- **Scalability**: Support for custom hierarchies per user/role

**Key Principle**: *Cards define WHAT they are, Hierarchies define HOW they're organized, Builder creates the display.*
