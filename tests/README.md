# Unit Tests

This directory contains unit tests for the Hospital Dashboard application.

## Running Tests

### Install pytest
```bash
pip install pytest pytest-cov
```

### Run all tests
```bash
pytest tests/
```

### Run with coverage
```bash
pytest tests/ --cov=utils --cov=data_loaders --cov=callbacks
```

### Run specific test file
```bash
pytest tests/test_formatting.py -v
```

### Run specific test class
```bash
pytest tests/test_formatting.py::TestFormatCurrency -v
```

### Run specific test
```bash
pytest tests/test_formatting.py::TestFormatCurrency::test_format_millions -v
```

## Test Structure

### Current Tests

#### `test_formatting.py`
Tests for `utils/formatting.py`:
- `TestFormatCurrency` - Currency formatting (7 tests)
- `TestCleanReLineName` - Revenue & expenses name cleaning (5 tests)
- `TestCleanCostLineName` - Cost name cleaning (5 tests)
- `TestIsSubtotalLine` - Subtotal detection (10 tests)

**Total: 27 tests**

#### `test_financial_tables.py`
Tests for `utils/financial_tables.py`:
- `TestCreateMultiyearFinancialTable` - Table generation (7 tests)
- `TestTableHelpers` - Helper functions (1 test)

**Total: 8 tests**

### Planned Tests

#### `test_data_loaders.py` (TODO)
Tests for `data_loaders/valuation.py`:
- Test income statement loading
- Test expense detail loading
- Test error handling
- Test database vs parquet modes

#### `test_callbacks.py` (TODO)
Integration tests for callbacks:
- Test dashboard callbacks
- Test financial statements callbacks
- Test cost worksheets callbacks
- Mock data manager
- Test callback outputs

## Test Coverage Goals

- **Utils**: 90%+ coverage
- **Data Loaders**: 80%+ coverage
- **Callbacks**: 70%+ coverage (harder to test Dash callbacks)

## Writing New Tests

### Test File Naming
- Test files: `test_<module_name>.py`
- Test classes: `Test<FeatureName>`
- Test methods: `test_<what_is_being_tested>`

### Example Test Structure

```python
import pytest
from module_to_test import function_to_test

class TestFeatureName:
    """Test feature description"""

    def test_normal_case(self):
        """Test normal operation"""
        result = function_to_test(valid_input)
        assert result == expected_output

    def test_edge_case(self):
        """Test edge case"""
        result = function_to_test(edge_case_input)
        assert result == expected_edge_output

    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ExpectedError):
            function_to_test(invalid_input)
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Clear test names** describing what's being tested
3. **Arrange-Act-Assert** pattern
4. **Test both success and failure cases**
5. **Use fixtures** for common setup
6. **Mock external dependencies** (databases, APIs)

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline
- Before deploying to production

## Test Data

Test data should be:
- Minimal (just enough to test)
- Realistic (represents actual use cases)
- Isolated (doesn't depend on external state)
- Deterministic (same input = same output)
