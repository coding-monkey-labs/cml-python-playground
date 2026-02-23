# Skill: Code Quality

## Capability

Lint, format, and type-check Python code. Maintain consistent code standards.

## Tools Used

- **Bash** — run linters, formatters, type checkers
- **Edit** — fix issues inline
- **Read** — inspect flagged files

## Patterns

### Linting (ruff)
```bash
ruff check .
ruff check --fix .           # auto-fix
```

### Formatting
```bash
ruff format .
# or:
black .
```

### Type Checking
```bash
mypy src/
pyright src/
```

### All-in-One Check
```bash
ruff check . && ruff format --check . && mypy src/
```

## Conventions

- ruff is preferred over flake8/pylint (faster, unified)
- Format on commit, not continuously
- Type hints required for public APIs
- Ignore style warnings that don't affect readability
- Fix real bugs, not lint pedantry

## Configuration

Prefer `pyproject.toml` for all tool config:
```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.mypy]
strict = true
```

## Background Agent Usage

- Run linters in background after code changes
- Parallel lint + type check for faster feedback
- Background format check before commits
