"""Error handling utilities for dashboards."""
import logging
import plotly.graph_objs as go
from functools import wraps


def create_error_figure(message):
    """Create an error message figure for dashboards."""
    return {
        'data': [],
        'layout': {
            'xaxis': {'visible': False},
            'yaxis': {'visible': False},
            'annotations': [{
                'text': message,
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 20, 'color': 'red'},
                'x': 0.5,
                'y': 0.5
            }]
        }
    }


def safe_db_operation(error_message="Database operation failed"):
    """Decorator for safe database operations."""
    def decorator(operation):
        @wraps(operation)
        def wrapper(*args, **kwargs):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                logging.error(f"{error_message}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator