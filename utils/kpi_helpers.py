"""
KPI Helper Functions - Calculations and utilities for KPI processing
"""

import pandas as pd
import plotly.graph_objects as go
from kpi_hierarchy_config import KPI_METADATA


def calculate_importance_score(kpi_key):
    """Calculate BASE importance score = Impact × Ease of Change"""
    meta = KPI_METADATA.get(kpi_key, {})
    impact = meta.get('impact_score', 5)
    ease = meta.get('ease_of_change', 5)
    return impact * ease


def calculate_dynamic_priority(kpi_key, hospital_value, benchmark_median, higher_is_better=True):
    """
    Calculate DYNAMIC priority for this hospital based on:
    1. Base importance (impact × ease)
    2. Performance gap from benchmark
    3. Direction matters (worse performance = higher priority)

    Returns: priority score (0-1000)
    """
    base_importance = calculate_importance_score(kpi_key)

    if pd.isna(hospital_value) or pd.isna(benchmark_median) or benchmark_median == 0:
        return base_importance

    # Calculate gap percentage
    gap_pct = abs((hospital_value - benchmark_median) / benchmark_median) * 100

    # Determine if hospital is underperforming
    if higher_is_better:
        underperforming = hospital_value < benchmark_median
    else:
        underperforming = hospital_value > benchmark_median

    # Priority multiplier based on performance
    if underperforming:
        gap_multiplier = 1 + min(gap_pct / 100, 0.5)
    else:
        gap_multiplier = 0.5

    priority = base_importance * gap_multiplier
    return priority


def calculate_percentile_rank(value, p25, median, p75):
    """Determine which quartile the value falls into"""
    if pd.isna(value) or p25 is None or median is None or p75 is None:
        return None, 'secondary'

    if value <= p25:
        return 'Bottom Quartile', 'danger'
    elif value <= median:
        return 'Below Median', 'warning'
    elif value <= p75:
        return 'Above Median', 'info'
    else:
        return 'Top Quartile', 'success'


def calculate_trend(values):
    """Calculate trend direction and magnitude"""
    if len(values) < 2:
        return 'stable', 0

    recent = values[0]
    older = values[1]

    if pd.isna(recent) or pd.isna(older) or older == 0:
        return 'stable', 0

    change_pct = ((recent - older) / abs(older)) * 100

    if abs(change_pct) < 2:
        return 'stable', change_pct
    elif change_pct > 0:
        return 'up', change_pct
    else:
        return 'down', change_pct


def create_sparkline(values, fiscal_years):
    """Create a mini sparkline chart for trend"""
    if len(values) < 2:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(fiscal_years),
        y=list(values),
        mode='lines',
        line=dict(color='#2C3E50', width=2),
        fill='tozeroy',
        fillcolor='rgba(44, 62, 80, 0.1)'
    ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=50,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode=False
    )

    return fig


def get_professional_datatable_style():
    """
    Returns professional styling for DataTable components
    Inspired by financial presentation tables
    """
    return {
        'style_table': {
            'overflowX': 'auto',
            'borderRadius': '8px',
            'overflow': 'hidden',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'
        },
        'style_cell': {
            'textAlign': 'left',
            'padding': '12px 14px',
            'fontSize': '0.9rem',
            'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            'border': '1px solid #e8e8e8',
            'whiteSpace': 'normal',
            'height': 'auto',
            'minHeight': '44px'
        },
        'style_cell_conditional': [
            {
                'if': {'column_type': 'numeric'},
                'textAlign': 'right',
                'fontFamily': 'Monaco, Consolas, "Courier New", monospace',
                'fontWeight': '500'
            },
            {
                'if': {'column_id': 'Line'},
                'width': '80px',
                'textAlign': 'center',
                'fontWeight': '600',
                'color': '#5a6c7d'
            }
        ],
        'style_header': {
            'backgroundColor': '#34495e',
            'color': 'white',
            'fontWeight': '600',
            'fontSize': '0.95rem',
            'padding': '14px',
            'textAlign': 'center',
            'border': 'none',
            'textTransform': 'none'
        },
        'style_data': {
            'border': '1px solid #e8e8e8',
            'color': '#2c3e50'
        },
        'style_data_conditional': [
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'row_index': 'even'},
                'backgroundColor': 'white'
            },
            {
                'if': {'state': 'selected'},
                'backgroundColor': '#e8f4f8',
                'border': '1px solid #3498db'
            }
        ]
    }
