# Dashboard Integration Documentation

## How app_with_auth.py Uses dashboard.py

The deployment application (`app_with_auth.py`) is designed to use all components from the working `dashboard.py` file without modifying it.

### Component Imports

```python
from dashboard import (
    data_manager,              # Pre-initialized HospitalDataManager instance
    create_kpi_card,           # Function to create interactive KPI cards
    calculate_dynamic_priority, # Function to calculate KPI priority ranking
    calculate_trend,           # Function to calculate trend direction
    calculate_percentile_rank, # Function to determine benchmark quartile
    create_sparkline          # Function to create mini trend charts
)
from kpi_hierarchy_config import KPI_METADATA
```

### Data Manager Methods Used

1. **get_available_hospitals()** - Returns list of hospitals with metadata
2. **classify_hospital_type(ccn)** - Returns hospital type classification
3. **calculate_kpis(ccn)** - Returns KPI data for a hospital
4. **get_benchmarks(ccn, fiscal_year, benchmark_level)** - Returns benchmark data

### KPI Card Creation Flow

```python
# 1. Get hospital data
hospital_type = data_manager.classify_hospital_type(ccn)
kpi_data = data_manager.calculate_kpis(ccn)

# 2. Get benchmarks
benchmark_data = data_manager.get_benchmarks(ccn, latest_year, benchmark_level)

# 3. Rank KPIs by priority
for kpi_key in KPI_METADATA.keys():
    dynamic_priority = calculate_dynamic_priority(kpi_key, kpi_value, median, higher_is_better)
    # Calculate performance gap and trend
    # Add to rankings

# 4. Sort by selected method
kpi_rankings.sort(key=lambda x: x['dynamic_priority'], reverse=True)

# 5. Create KPI cards
for idx, ranking in enumerate(kpi_rankings):
    card = create_kpi_card(
        kpi_key=ranking['kpi_key'],
        kpi_value=ranking['kpi_value'],
        kpi_trend_values=ranking['kpi_values'],
        fiscal_years=kpi_data['Fiscal_Year'].values,
        benchmark_data=benchmark_data,
        rank=idx + 1,
        importance_score=ranking['dynamic_priority']
    )
```

### Files in Deployment

- **app_with_auth.py** - Main deployment app (uses dashboard.py)
- **dashboard.py** - Working dashboard with all KPI logic (DO NOT MODIFY)
- **auth_components.py** - UI components for login/registration
- **auth_manager.py** - Authentication logic
- **auth_models.py** - Database models for users
- **kpi_hierarchy_config.py** - KPI metadata and hierarchy
- **data_manager.py** - Data access layer (if separate)

### Deployment Settings

- **Procfile**: `web: gunicorn app:server --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120`
- **Entry Point**: `app.py` (imports from `app_with_auth.py`)
- **Main App**: `app_with_auth.py` (imports from `dashboard.py`)

## Key Points

1. ✅ **dashboard.py is NOT modified** - All changes are in app_with_auth.py
2. ✅ **Shared data_manager** - Uses the same instance from dashboard.py
3. ✅ **Identical KPI logic** - Same functions for calculations and rendering
4. ✅ **Complete integration** - All 78 KPIs with benchmarks and sorting
