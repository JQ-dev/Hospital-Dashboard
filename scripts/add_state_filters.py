"""Script to add state filtering to all ETL scripts."""
import re
from pathlib import Path

# List of ETL scripts to update
ETL_SCRIPTS = [
    'etl/create_balance_sheet.py',
    'etl/create_fund_balance_changes.py',
    'etl/create_revenue.py',
    'etl/create_revenue_expenses.py',
    'etl/create_costs_a000.py',
    'etl/create_costs_b100.py',
]

PROJECT_ROOT = Path(__file__).parent.parent

# Filter code to add after rpt merge
FILTER_CODE = """
        # APPLY STATE FILTER (if configured)
        if FILTER_STATES:
            before_filter = len(merged_df)
            merged_df = merged_df[merged_df['Provider_Number'].astype(str).str[:2].isin(FILTER_STATES)]
            logger.info(f"State filter applied: {before_filter:,} -> {len(merged_df):,} records (kept {len(FILTER_STATES)} states)")
"""

for script_path in ETL_SCRIPTS:
    full_path = PROJECT_ROOT / script_path
    print(f"Processing {script_path}...")

    with open(full_path, 'r') as f:
        content = f.read()

    # 1. Add FILTER_STATES to imports (if not already there)
    if 'FILTER_STATES' not in content:
        # Find the imports from config.paths
        imports_pattern = r'(from config\.paths import \([^)]+)'
        match = re.search(imports_pattern, content, re.DOTALL)
        if match:
            imports_section = match.group(1)
            if 'FILTER_STATES' not in imports_section:
                # Add FILTER_STATES before the closing parenthesis
                new_imports = imports_section.rstrip() + ',\n    FILTER_STATES'
                content = content.replace(imports_section, new_imports)
                print(f"  [OK] Added FILTER_STATES to imports")

    # 2. Add filter code after rpt merge (if not already there)
    if 'APPLY STATE FILTER' not in content:
        # Find the pattern after merging with rpt_df
        rpt_merge_pattern = r"(merged_df = pd\.merge\(merged_df, rpt_df, on=\['Report_Record_Number'\], how='left'\))\s+(# Add year column)"
        match = re.search(rpt_merge_pattern, content)
        if match:
            # Insert filter code between merge and "Add year column"
            replacement = match.group(1) + FILTER_CODE + "\n        " + match.group(2)
            content = content.replace(match.group(0), replacement)
            print(f"  [OK] Added state filter logic")
        else:
            print(f"  [WARN] Could not find rpt merge pattern - manual update needed")
    else:
        print(f"  [SKIP] State filter already present")

    # Write updated content
    with open(full_path, 'w') as f:
        f.write(content)

    print(f"  [OK] Updated {script_path}\n")

print("All ETL scripts updated with state filtering!")
