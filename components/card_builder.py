"""
Card Builder - Factory for Creating KPI Cards
==============================================

This module provides a centralized card building system that:
1. Fetches card definitions from the card registry
2. Applies hierarchy configuration
3. Builds display-ready card components

This decouples card creation from card definitions and hierarchies.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd

from config.card_registry import CARD_REGISTRY, enrich_card_metadata
from config.hierarchy_config import get_hierarchy, get_children, get_lineage, flatten_hierarchy
from utils.kpi_helpers import calculate_percentile_rank, calculate_trend, create_sparkline
from utils.formatting import format_number_compact


class CardBuilder:
    """
    Factory class for building KPI cards with different templates
    """

    def __init__(self, hierarchy_name='default'):
        """
        Initialize card builder

        Args:
            hierarchy_name: Name of hierarchy to use for card relationships
        """
        self.hierarchy_name = hierarchy_name
        self.hierarchy = get_hierarchy(hierarchy_name)
        self.flat_hierarchy = flatten_hierarchy(hierarchy_name)

    def build_card(self, card_id, kpi_value, kpi_trend_values, fiscal_years,
                   benchmark_data=None, template='basic', **kwargs):
        """
        Build a card using specified template

        Args:
            card_id: Card identifier from registry
            kpi_value: Current KPI value
            kpi_trend_values: Historical values
            fiscal_years: Years for trend
            benchmark_data: Benchmark comparison data
            template: Template to use ('basic', 'enhanced', 'hierarchical')
            **kwargs: Additional arguments for specific templates

        Returns:
            Dash component
        """
        # Get card definition from registry
        card_def = CARD_REGISTRY.get(card_id)
        if not card_def:
            return self._build_error_card(f"Card '{card_id}' not found in registry")

        # Get hierarchy metadata
        hierarchy_meta = self.flat_hierarchy.get(card_id, {})

        # Merge card definition with hierarchy metadata
        card_data = {
            **card_def,
            'card_id': card_id,
            'level': hierarchy_meta.get('level', 1),
            'rank': hierarchy_meta.get('rank', 999),
            'parent': hierarchy_meta.get('parent'),
            'impact_score': hierarchy_meta.get('impact_score', 5),
            'ease_of_change': hierarchy_meta.get('ease_of_change', 5)
        }

        # Select template
        if template == 'basic':
            return self._build_basic_card(card_data, kpi_value, kpi_trend_values,
                                          fiscal_years, benchmark_data, **kwargs)
        elif template == 'enhanced':
            return self._build_enhanced_card(card_data, kpi_value, kpi_trend_values,
                                             fiscal_years, benchmark_data, **kwargs)
        elif template == 'hierarchical':
            return self._build_hierarchical_card(card_data, kpi_value, kpi_trend_values,
                                                 fiscal_years, benchmark_data, **kwargs)
        else:
            return self._build_basic_card(card_data, kpi_value, kpi_trend_values,
                                          fiscal_years, benchmark_data, **kwargs)

    def _build_basic_card(self, card_data, kpi_value, kpi_trend_values, fiscal_years,
                          benchmark_data, **kwargs):
        """Build a basic KPI card"""

        kpi_name = card_data['name']
        category = card_data['category']
        unit = card_data['unit']
        fmt = card_data['format']
        rank = card_data['rank']
        higher_is_better = card_data.get('higher_is_better', True)

        # Get benchmark comparison
        benchmark_kpis = benchmark_data.get('kpis', {}) if benchmark_data else {}
        kpi_benchmark = benchmark_kpis.get(card_data['card_id'], {})
        p25 = kpi_benchmark.get('P25')
        median = kpi_benchmark.get('Median')
        p75 = kpi_benchmark.get('P75')
        mean = kpi_benchmark.get('Mean')

        # Calculate performance vs benchmark
        perf_label, perf_color = calculate_percentile_rank(kpi_value, p25, median, p75)

        # Calculate trend
        trend_direction, trend_pct = calculate_trend(kpi_trend_values)

        # Trend icons and colors
        trend_icons = {'up': '↑', 'down': '↓', 'stable': '→'}
        trend_colors = {
            'up': 'success' if higher_is_better else 'danger',
            'down': 'danger' if higher_is_better else 'success',
            'stable': 'secondary'
        }

        # Create sparkline
        sparkline_fig = create_sparkline(kpi_trend_values, fiscal_years)

        # Build card
        card = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H6(kpi_name, className="mb-0"),
                        html.Small(category, className="text-muted")
                    ], width=8),
                    dbc.Col([
                        dbc.Badge(f"#{rank}", color="primary", className="float-end")
                    ], width=4)
                ])
            ]),
            dbc.CardBody([
                # Main KPI Value
                html.Div([
                    html.H2(
                        f"{kpi_value:{fmt}}{unit}" if not pd.isna(kpi_value) else "N/A",
                        className="mb-2"
                    ),
                    dbc.Badge(
                        f"{trend_icons[trend_direction]} {abs(trend_pct):.1f}%",
                        color=trend_colors[trend_direction],
                        className="me-2"
                    ),
                ]),

                # Sparkline
                html.Div([
                    dcc.Graph(
                        figure=sparkline_fig,
                        config={'displayModeBar': False},
                        style={'height': '50px'}
                    )
                ], className="mt-2 mb-3"),

                # Benchmark Comparison
                html.Div([
                    html.Hr(),
                    html.Small("Benchmark Comparison", className="text-muted d-block mb-2"),
                    html.Div([
                        html.Strong(f"Mean: {format(mean, fmt)}{unit}" if mean else "Mean: N/A",
                                   className="text-primary me-3"),
                        dbc.Badge(perf_label if perf_label else "N/A", color=perf_color, className="me-2")
                    ], className="mb-2"),
                    dbc.Progress([
                        dbc.Progress(value=25, color="danger", bar=True),
                        dbc.Progress(value=25, color="warning", bar=True),
                        dbc.Progress(value=25, color="info", bar=True),
                        dbc.Progress(value=25, color="success", bar=True),
                    ], className="mb-2", style={'height': '8px'}),
                    dbc.Row([
                        dbc.Col(html.Small(f"P25: {format(p25, fmt)}{unit}" if p25 else "N/A"), width=4),
                        dbc.Col(html.Small(f"Median: {format(median, fmt)}{unit}" if median else "N/A"), width=4),
                        dbc.Col(html.Small(f"P75: {format(p75, fmt)}{unit}" if p75 else "N/A"), width=4)
                    ])
                ])
            ])
        ], className="shadow-sm mb-3", style={'height': '100%'})

        return card

    def _build_enhanced_card(self, card_data, kpi_value, kpi_trend_values, fiscal_years,
                             all_benchmarks, **kwargs):
        """Build an enhanced L1 card with full benchmark comparison"""

        # Import from existing kpi_cards to reuse
        from components.kpi_cards import create_enhanced_level1_kpi_card

        return create_enhanced_level1_kpi_card(
            card_data['card_id'],
            kpi_value,
            kpi_trend_values,
            fiscal_years,
            all_benchmarks,
            card_data['rank'],
            **kwargs
        )

    def _build_hierarchical_card(self, card_data, kpi_value, kpi_trend_values, fiscal_years,
                                 benchmark_data, **kwargs):
        """Build a hierarchical card with child KPIs"""

        card_id = card_data['card_id']

        # Get children from hierarchy
        children = get_children(card_id, self.hierarchy_name)

        # Build child KPI section
        child_components = []
        for child_config in children:
            child_id = child_config.get('card_id')
            child_def = CARD_REGISTRY.get(child_id)

            if child_def:
                # Get child KPI values from kwargs if provided
                child_kpis = kwargs.get('l2_kpis', {})
                child_value = child_kpis.get(child_id)

                # Create child card component
                child_card = self._build_child_card(
                    child_id,
                    child_def,
                    child_value,
                    child_config
                )
                child_components.append(child_card)

        # Build main card with collapsible children
        from components.kpi_cards import create_hierarchical_kpi_card

        return create_hierarchical_kpi_card(
            card_data['card_id'],
            kpi_value,
            kpi_trend_values,
            fiscal_years,
            benchmark_data,
            card_data['rank'],
            card_data.get('impact_score', 50),
            **kwargs
        )

    def _build_child_card(self, child_id, child_def, child_value, child_config):
        """Build a small card for a child KPI"""

        name = child_def['name']
        unit = child_def['unit']
        fmt = child_def['format']

        if child_value is not None:
            display = f"{child_value:{fmt}}{unit}"
            color = "light"
        else:
            display = "N/A"
            color = "secondary"

        return dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Small(name, className="text-muted d-block mb-1"),
                    html.H6(display, className="mb-0")
                ], className="py-2")
            ], color=color, outline=True, className="mb-2")
        ], width=12)

    def _build_error_card(self, error_message):
        """Build an error card when card cannot be created"""

        return dbc.Card([
            dbc.CardBody([
                html.I(className="fas fa-exclamation-triangle fa-3x text-danger mb-3"),
                html.H5("Card Error", className="text-danger"),
                html.P(error_message, className="text-muted")
            ], className="text-center py-4")
        ], className="shadow-sm mb-3", color="danger", outline=True)

    def build_card_grid(self, card_ids, values_dict, trends_dict, years_dict,
                       benchmarks_dict=None, template='basic', columns=3, **kwargs):
        """
        Build a grid of cards

        Args:
            card_ids: List of card IDs to build
            values_dict: Dict mapping card IDs to current values
            trends_dict: Dict mapping card IDs to trend values
            years_dict: Dict mapping card IDs to fiscal years
            benchmarks_dict: Dict mapping card IDs to benchmark data
            template: Template to use for all cards
            columns: Number of columns in grid (1-4)

        Returns:
            Dash Row component with card grid
        """
        cards = []
        col_width = 12 // columns

        for card_id in card_ids:
            value = values_dict.get(card_id)
            trends = trends_dict.get(card_id, [])
            years = years_dict.get(card_id, [])
            benchmarks = benchmarks_dict.get(card_id) if benchmarks_dict else None

            card = self.build_card(
                card_id,
                value,
                trends,
                years,
                benchmarks,
                template=template,
                **kwargs
            )

            cards.append(dbc.Col(card, width=col_width, className="mb-4"))

        return dbc.Row(cards)

    def build_level_cards(self, level, values_dict, trends_dict, years_dict,
                         benchmarks_dict=None, template='enhanced', **kwargs):
        """
        Build all cards for a specific level

        Args:
            level: Level number (1, 2, or 3)
            values_dict: Dict mapping card IDs to current values
            trends_dict: Dict mapping card IDs to trend values
            years_dict: Dict mapping card IDs to fiscal years
            benchmarks_dict: Dict mapping card IDs to benchmark data
            template: Template to use for cards

        Returns:
            List of card components
        """
        # Get all cards at this level
        level_card_ids = [
            card_id for card_id, meta in self.flat_hierarchy.items()
            if meta.get('level') == level
        ]

        # Sort by rank
        level_card_ids.sort(
            key=lambda cid: self.flat_hierarchy[cid].get('rank', 999)
        )

        return self.build_card_grid(
            level_card_ids,
            values_dict,
            trends_dict,
            years_dict,
            benchmarks_dict,
            template=template,
            columns=2 if level == 1 else 3,
            **kwargs
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def build_card(card_id, kpi_value, kpi_trend_values, fiscal_years,
               benchmark_data=None, hierarchy_name='default', template='basic', **kwargs):
    """
    Convenience function to build a single card

    Args:
        card_id: Card identifier
        kpi_value: Current value
        kpi_trend_values: Historical values
        fiscal_years: Years
        benchmark_data: Benchmark data
        hierarchy_name: Hierarchy to use
        template: Template name

    Returns:
        Dash card component
    """
    builder = CardBuilder(hierarchy_name)
    return builder.build_card(
        card_id,
        kpi_value,
        kpi_trend_values,
        fiscal_years,
        benchmark_data,
        template=template,
        **kwargs
    )


def build_dashboard_layout(level=1, values_dict=None, trends_dict=None,
                          years_dict=None, benchmarks_dict=None,
                          hierarchy_name='default', template='enhanced'):
    """
    Build a complete dashboard layout for a level

    Args:
        level: Level number (1, 2, or 3)
        values_dict: Current values for cards
        trends_dict: Trend values for cards
        years_dict: Fiscal years for cards
        benchmarks_dict: Benchmark data for cards
        hierarchy_name: Hierarchy to use
        template: Card template

    Returns:
        Dash container with complete dashboard
    """
    builder = CardBuilder(hierarchy_name)

    return dbc.Container([
        html.H2(f"Level {level} KPIs", className="mb-4"),
        builder.build_level_cards(
            level,
            values_dict or {},
            trends_dict or {},
            years_dict or {},
            benchmarks_dict or {},
            template=template
        )
    ], fluid=True)
