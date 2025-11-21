"""
Financial Tables - Multi-year financial statement table generation
"""

import pandas as pd
from dash import html
import dash_bootstrap_components as dbc
from utils.formatting import format_currency, clean_re_line_name, clean_cost_line_name, is_subtotal_line


def create_multiyear_financial_table(df, title, statement_type):
    """Create a professionally formatted financial statement table with all years as columns"""
    if df is None or df.empty:
        return html.Div("No data available", className="alert alert-info")

    # Get unique years and sort (oldest to newest, so newest is on right)
    years = sorted(df['Fiscal_Year'].unique())

    # Pivot data to get years as columns
    # First, create a unique key for each line item and clean detail names
    # Include Line number for proper ordering

    # Handle unknown categories with sequential naming
    unknown_counters = {'major': 0, 'sub': 0}

    def get_category_name(value, level):
        """Get category name, handling blanks with sequential numbers"""
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
        else:
            unknown_counters[level] += 1
            return f"Other {unknown_counters[level]}"

    if statement_type == 'balance_sheet':
        # Use Acc_name for clean names (no prefixes)
        df['major'] = df['Acc_level2'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = df['Acc_level3'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['Acc_name'].fillna('Unknown item')
        df['is_subtotal'] = df['Acc_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    elif statement_type == 'revenue':
        # Revenue hierarchy: Revenue_Center -> Revenue_Group -> Revenue_Subgroup -> Revenue_Subgroup_Detail
        df['major'] = df['Revenue_Center'].apply(lambda x: get_category_name(x, 'major') if pd.notna(x) and str(x).strip() else '')
        df['sub'] = df['Revenue_Group'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['sub2'] = df['Revenue_Subgroup'].apply(lambda x: get_category_name(x, 'sub2') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['Revenue_Subgroup_Detail'].fillna('Unknown item')
        df['is_subtotal'] = df['Revenue_Subgroup_Detail'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['sub2'] + '|' + df['Line'].astype(str)

    elif statement_type == 'revenue_expenses':
        # Revenue & Expenses: Sort by Line, indent by RE_Level (1 or 2)
        df['clean_name'] = df['RE_Line_Name'].apply(clean_re_line_name)
        df['level'] = df['RE_Level'].fillna(1).astype(int)  # Level 1 or 2
        df['detail'] = df['clean_name'].replace('', 'Unknown item')
        df['is_subtotal'] = df['clean_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        # Use line_num directly for sorting, level for grouping
        df['line_key'] = df['Line'].astype(str)

    elif statement_type == 'costs':
        # Clean Cost_Center_Name
        df['clean_name'] = df['Cost_Center_Name'].apply(clean_cost_line_name)
        df['major'] = df['Cost_Class'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = df['Cost_Allocation_Type'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['clean_name'].replace('', 'Unknown item')
        df['is_subtotal'] = df['clean_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    elif statement_type == 'cost-summary':
        # Cost Summary from B100 (lines 3000-20200, column 2600)
        df['major'] = df['Account_group'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = ''  # No subcategories for cost summary
        df['detail'] = df['Account_name'].fillna('Unknown item')
        df['is_subtotal'] = df['Account_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['Line'].astype(str)

    elif statement_type == 'fund_balance_changes':
        # Fund Balance Changes (similar structure to balance sheet)
        df['major'] = df['Acc_level1'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = df['Acc_level2'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['Acc_name'].fillna('Unknown item')
        df['is_subtotal'] = df['Acc_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    elif statement_type == 'detailed-costs':
        # Detailed Costs (Schedule A + B combined, unpivoted by cost component)
        # Structure: Account_name (cost center) → Cost_Component (subgroup) → Value
        df['major'] = df['Account_name'].fillna('Unknown Cost Center')
        df['sub'] = df['Cost_Component'].fillna('Unknown Component')
        df['detail'] = ''  # No detail level for unpivoted structure
        df['is_subtotal'] = df['Account_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    else:
        return html.Div("Unknown statement type", className="alert alert-warning")

    # Pivot: one row per line_key, columns for each year
    # Include line_num and is_subtotal in index for sorting
    # Dynamically build index columns based on statement type
    index_cols = ['line_key']

    if 'major' in df.columns:
        # For balance_sheet, revenue, costs (hierarchical structure)
        index_cols.extend(['major', 'sub'])
        if 'sub2' in df.columns:
            index_cols.append('sub2')
        if 'sub3' in df.columns:
            index_cols.append('sub3')
    elif 'level' in df.columns:
        # For revenue_expenses (flat structure with level)
        index_cols.append('level')

    index_cols.extend(['detail', 'line_num', 'is_subtotal'])

    pivot_df = df.pivot_table(
        index=index_cols,
        columns='Fiscal_Year',
        values='Value',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Group data by major categories (with support for up to 4 levels)
    # Skip grouping for revenue_expenses (it uses flat structure)
    grouped_data = {}

    if statement_type != 'revenue_expenses':
        for _, row in pivot_df.iterrows():
            major = row['major']
            sub = row['sub']
            sub2 = row.get('sub2', '')
            sub3 = row.get('sub3', '')
            detail = row['detail']
            line_num = row['line_num']
            is_subtotal = row['is_subtotal']

            # Get values for each year
            year_values = {year: row.get(year, 0) for year in years}

            # Build nested structure: major -> sub -> sub2 -> sub3 -> items
            if major not in grouped_data:
                grouped_data[major] = {}

            sub_key = sub if sub else '_items'
            if sub_key not in grouped_data[major]:
                grouped_data[major][sub_key] = {}

            # For revenue with 4 levels, use sub2 as next level
            if sub2:
                sub2_key = sub2 if sub2 else '_items'
                if sub2_key not in grouped_data[major][sub_key]:
                    grouped_data[major][sub_key][sub2_key] = {}

                if sub3:
                    sub3_key = sub3 if sub3 else '_items'
                    if sub3_key not in grouped_data[major][sub_key][sub2_key]:
                        grouped_data[major][sub_key][sub2_key][sub3_key] = []

                    grouped_data[major][sub_key][sub2_key][sub3_key].append({
                        'detail': detail,
                        'line_num': line_num,
                        'is_subtotal': is_subtotal,
                        'year_values': year_values
                    })
                else:
                    # 3 levels only
                    if '_items' not in grouped_data[major][sub_key][sub2_key]:
                        grouped_data[major][sub_key][sub2_key]['_items'] = []
                    grouped_data[major][sub_key][sub2_key]['_items'].append({
                        'detail': detail,
                        'line_num': line_num,
                        'is_subtotal': is_subtotal,
                        'year_values': year_values
                    })
            else:
                # 2 levels only (original logic)
                if '_items' not in grouped_data[major][sub_key]:
                    grouped_data[major][sub_key]['_items'] = []
                grouped_data[major][sub_key]['_items'].append({
                    'detail': detail,
                    'line_num': line_num,
                    'is_subtotal': is_subtotal,
                    'year_values': year_values
                })

    # Build table rows
    table_rows = []

    # Helper function to calculate totals recursively
    def calc_totals_recursive(data, years):
        totals = {year: 0 for year in years}
        if isinstance(data, list):
            # Base case: list of items
            for item in data:
                if not item.get('is_subtotal', False):
                    for year in years:
                        totals[year] += item['year_values'].get(year, 0)
        elif isinstance(data, dict):
            # Recursive case: dict of sub-categories
            for value in data.values():
                sub_totals = calc_totals_recursive(value, years)
                for year in years:
                    totals[year] += sub_totals[year]
        return totals

    # Helper function to get minimum line number from nested structure
    def get_min_line_num(data):
        """Recursively find the minimum line number in a nested structure"""
        if isinstance(data, list):
            # Base case: list of items
            return min([item['line_num'] for item in data], default=999999)
        elif isinstance(data, dict):
            # Recursive case: dict of sub-categories
            min_nums = []
            for key, value in data.items():
                if key != '_items':
                    min_nums.append(get_min_line_num(value))
                else:
                    # _items is a list
                    min_nums.append(get_min_line_num(value))
            return min(min_nums, default=999999) if min_nums else 999999
        return 999999

    # Use statement-specific rendering
    if statement_type == 'revenue_expenses':
        # Revenue & Expenses: Simple rendering sorted by line, indented by level (1 or 2)
        sorted_items = sorted(pivot_df.to_dict('records'), key=lambda x: x['line_num'])

        for item in sorted_items:
            level = item.get('level', 1)
            detail = item['detail']
            is_subtotal = item.get('is_subtotal', False)

            # Determine indentation based on level
            if level == 1:
                padding_class = "ps-2"
                row_class = "table-secondary"
                use_bold = True
            else:  # level == 2
                padding_class = "ps-4"
                row_class = ""
                use_bold = is_subtotal

            # Create row
            if use_bold or is_subtotal:
                row_cells = [html.Td(html.Strong(detail), className=padding_class)]
            else:
                row_cells = [html.Td(detail, className=padding_class)]

            for year in years:
                value = item.get(year, 0)
                if use_bold or is_subtotal:
                    row_cells.append(html.Td(html.Strong(format_currency(value)), className="text-end"))
                else:
                    row_cells.append(html.Td(format_currency(value), className="text-end"))

            if is_subtotal:
                table_rows.append(html.Tr(row_cells, className="table-info"))
            elif row_class:
                table_rows.append(html.Tr(row_cells, className=row_class))
            else:
                table_rows.append(html.Tr(row_cells))

    elif statement_type == 'revenue':
        # Revenue-specific rendering: 3 levels (Revenue_Center -> Revenue_Group -> Revenue_Subgroup -> Detail)
        for major, subcats in sorted(grouped_data.items()):
            # Level 1: Revenue_Center (major) - ps-2
            major_totals = calc_totals_recursive(subcats, years)
            major_row_cells = [html.Td(html.Strong(major), className="text-uppercase ps-2")]
            for year in years:
                major_row_cells.append(
                    html.Td(html.Strong(format_currency(major_totals[year])), className="text-end")
                )
            table_rows.append(html.Tr(major_row_cells, className="table-primary"))

            # Level 2: Revenue_Group (sub) - ps-3 - sort by minimum line number
            for sub, sub_data in sorted(subcats.items(), key=lambda x: get_min_line_num(x[1])):
                if sub and sub != '_items':
                    sub_totals = calc_totals_recursive(sub_data, years)
                    sub_row_cells = [html.Td(html.Strong(sub), className="ps-3")]
                    for year in years:
                        sub_row_cells.append(
                            html.Td(html.Strong(format_currency(sub_totals[year])), className="text-end")
                        )
                    table_rows.append(html.Tr(sub_row_cells, className="table-secondary"))

                    # Level 3: Revenue_Subgroup (sub2) - ps-4 - sort by minimum line number
                    if isinstance(sub_data, dict):
                        for sub2, items_data in sorted(sub_data.items(), key=lambda x: get_min_line_num(x[1]) if x[0] != '_items' else 0):
                            if sub2 and sub2 != '_items':
                                sub2_totals = calc_totals_recursive(items_data, years)
                                sub2_row_cells = [html.Td(sub2, className="ps-4 fw-bold")]
                                for year in years:
                                    sub2_row_cells.append(
                                        html.Td(format_currency(sub2_totals[year]), className="text-end")
                                    )
                                table_rows.append(html.Tr(sub2_row_cells, style={'background-color': '#f8f9fa'}))

                            # Detail items: Revenue_Subgroup_Detail - ps-5
                            items_list = items_data.get('_items', []) if isinstance(items_data, dict) else items_data
                            if isinstance(items_list, list):
                                sorted_items = sorted(items_list, key=lambda x: x['line_num'])
                                for item in sorted_items:
                                    is_subtotal = item.get('is_subtotal', False)
                                    if is_subtotal:
                                        detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-5 fw-bold")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                                    else:
                                        detail_row_cells = [html.Td(item['detail'], className="ps-5")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells))
    else:
        # Generic rendering for other statement types (balance_sheet, revenue_expenses, costs)

        # Sort major categories - use line numbers for costs, custom order for balance sheet
        if statement_type == 'balance_sheet' or statement_type == 'fund_balance_changes':
            # For balance sheet: Assets first, then Liabilities, then Fund Balances
            def sort_major(item):
                major = item[0]
                if major == 'Assets':
                    return '0'
                elif major == 'Liabilities':
                    return '1'
                elif 'Fund' in major or 'Equity' in major or 'Balance' in major:
                    return '2'
                else:
                    return '3_' + major  # Other categories at end
            sorted_majors = sorted(grouped_data.items(), key=sort_major)
        else:
            # For costs and other statements: sort by minimum line number
            sorted_majors = sorted(grouped_data.items(), key=lambda x: get_min_line_num(x[1]))

        for major, subcats in sorted_majors:
            # Calculate major category totals for each year
            major_totals = calc_totals_recursive(subcats, years)

            # Major category header row
            major_row_cells = [html.Td(html.Strong(major), className="text-uppercase ps-2")]
            for year in years:
                major_row_cells.append(
                    html.Td(html.Strong(format_currency(major_totals[year])), className="text-end")
                )
            table_rows.append(html.Tr(major_row_cells, className="table-primary"))

            # Process subcategories (level 2) - sort by minimum line number
            for subcat, sub_data in sorted(subcats.items(), key=lambda x: get_min_line_num(x[1])):
                if subcat and subcat != '_items':
                    # Subcategory header row (Level 2)
                    subcat_totals = calc_totals_recursive(sub_data, years)
                    subcat_row_cells = [html.Td(f"  {subcat}", className="fw-bold ps-3")]
                    for year in years:
                        subcat_row_cells.append(
                            html.Td(format_currency(subcat_totals[year]), className="text-end fw-bold")
                        )
                    table_rows.append(html.Tr(subcat_row_cells, className="table-secondary"))

                # Check if sub_data contains another level or items
                if isinstance(sub_data, dict):
                    for sub2_key, sub2_data in sorted(sub_data.items(), key=lambda x: get_min_line_num(x[1]) if x[0] != '_items' else 0):
                        if sub2_key and sub2_key != '_items':
                            # Level 3 header (sub2)
                            sub2_totals = calc_totals_recursive(sub2_data, years)
                            sub2_row_cells = [html.Td(f"    {sub2_key}", className="fw-bold ps-4")]
                            for year in years:
                                sub2_row_cells.append(
                                    html.Td(format_currency(sub2_totals[year]), className="text-end")
                                )
                            table_rows.append(html.Tr(sub2_row_cells, style={'background-color': '#f8f9fa'}))

                        # Check if sub2_data contains another level or items
                        if isinstance(sub2_data, dict):
                            for sub3_key, sub3_data in sorted(sub2_data.items(), key=lambda x: get_min_line_num(x[1]) if x[0] != '_items' else 0):
                                if sub3_key and sub3_key != '_items':
                                    # Level 4 header (sub3)
                                    sub3_totals = calc_totals_recursive(sub3_data, years)
                                    sub3_row_cells = [html.Td(f"      {sub3_key}", className="ps-5")]
                                    for year in years:
                                        sub3_row_cells.append(
                                            html.Td(format_currency(sub3_totals[year]), className="text-end")
                                        )
                                    table_rows.append(html.Tr(sub3_row_cells, style={'background-color': '#fafafa'}))

                                # Render items at level 5 (detail items under level 4 header)
                                items_list = sub3_data if isinstance(sub3_data, list) else sub3_data.get('_items', [])
                                sorted_items = sorted(items_list, key=lambda x: x['line_num'])
                                for item in sorted_items:
                                    is_subtotal = item.get('is_subtotal', False)
                                    if is_subtotal:
                                        # Subtotals at level 5 (indented under level 4)
                                        detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-6 fw-bold")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                                    else:
                                        # Regular detail items at level 5
                                        detail_row_cells = [html.Td(item['detail'], className="ps-6")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells))
                        elif isinstance(sub2_data, list):
                            # Items directly at level 4 (under level 3 header)
                            sorted_items = sorted(sub2_data, key=lambda x: x['line_num'])
                            for item in sorted_items:
                                is_subtotal = item.get('is_subtotal', False)
                                if is_subtotal:
                                    # Subtotals at level 4
                                    detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-5 fw-bold")]
                                    for year in years:
                                        detail_row_cells.append(
                                            html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                        )
                                    table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                                else:
                                    # Regular detail items at level 4
                                    detail_row_cells = [html.Td(item['detail'], className="ps-5")]
                                    for year in years:
                                        detail_row_cells.append(
                                            html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                        )
                                    table_rows.append(html.Tr(detail_row_cells))
                elif isinstance(sub_data, list):
                    # Items directly at level 3 (under level 2 header, original 2-level structure)
                    sorted_items = sorted(sub_data, key=lambda x: x['line_num'])
                    for item in sorted_items:
                        is_subtotal = item.get('is_subtotal', False)
                        if is_subtotal:
                            # Subtotals at level 3
                            detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-4 fw-bold")]
                            for year in years:
                                detail_row_cells.append(
                                    html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                )
                            table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                        else:
                            # Regular detail items at level 3
                            detail_row_cells = [html.Td(item['detail'], className="ps-4")]
                            for year in years:
                                detail_row_cells.append(
                                    html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                )
                            table_rows.append(html.Tr(detail_row_cells))

    # Create table header with years - Professional styling
    header_cells = [html.Th("Account", className="text-start",
                           style={'min-width': '300px', 'backgroundColor': '#34495e', 'color': 'white',
                                  'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'})]
    for year in years:
        header_cells.append(html.Th(str(int(year)), className="text-end",
                                   style={'min-width': '130px', 'backgroundColor': '#34495e', 'color': 'white',
                                          'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}))

    # Create table with professional styling
    table = dbc.Table([
        html.Thead(html.Tr(header_cells)),
        html.Tbody(table_rows)
    ], bordered=True, hover=True, responsive=True, className="table-sm",
       style={'font-size': '0.9rem', 'borderRadius': '8px', 'overflow': 'hidden',
              'boxShadow': '0 2px 8px rgba(0,0,0,0.08)', 'border': '1px solid #dee2e6'})

    return html.Div([
        html.H5(title, className="mb-3",
               style={'color': '#2c3e50', 'fontWeight': '600', 'fontSize': '1.3rem'}),
        html.P([
            html.Strong("Note: "),
            f"All amounts in millions (USD). Showing {len(years)} fiscal years: {min(years)} - {max(years)}"
        ], className="text-muted mb-3", style={'fontSize': '0.95rem'}),
        html.Div(table, style={'overflowX': 'auto'})
    ])
