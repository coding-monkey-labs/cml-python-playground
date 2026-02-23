# Skill: Testing

## Capability

Write and run tests. Validate code correctness. Ensure nothing breaks.

## Tools Used

- **Bash** — run pytest, unittest, coverage tools
- **Write/Edit** — create and modify test files
- **Read** — inspect test output and existing tests

## Patterns

### Run Tests
```bash
pytest
pytest -v                    # verbose
pytest tests/test_specific.py # single file
pytest -k "test_name"        # by name
pytest --tb=short            # short tracebacks
```

### Coverage
```bash
pytest --cov=src --cov-report=term-missing
```

### Test Structure
```python
def test_function_does_expected_thing():
    # Arrange
    input_data = setup()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected
```

### Quick Validation
```bash
python3 -c "assert 1 + 1 == 2; print('pass')"
```

## Conventions

- Tests in `tests/` directory or alongside source as `test_*.py`
- Name tests descriptively: `test_<what>_<condition>_<expected>`
- Arrange-Act-Assert pattern
- No mocks unless testing external dependencies
- Prefer real integration over mocked units

## Background Agent Usage

- Run full test suites in background
- Parallel test execution for independent test files
- Background coverage reports while working on code
