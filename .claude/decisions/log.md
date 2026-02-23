# Decision Log

All auto-decisions made under the YES-default policy are logged here.
Decisions marked "Needs Review" should be reviewed by a human at earliest convenience.

| Date | Context | Decision | Reasoning | Needs Review? |
|------|---------|----------|-----------|---------------|
| 2026-02-23 | Project structure for Claude config | Created `.claude/` directory with soul, skills, features, decisions subdirs | Standard organization pattern for Claude-configured projects | No |
| 2026-02-23 | Soul identity | Defined as "Core Techie" — hands-on builder | Matches the playground/experimentation nature of the project | No |
| 2026-02-23 | Primary execution model | Background agents first | User explicitly requested background-first approach | No |
| 2026-02-23 | Decision policy | YES-default with documentation | User explicitly requested YES-default with documentation | No |
| 2026-02-23 | Preferred Python package manager | uv (with pip/poetry as fallbacks) | uv is fastest, modern, actively maintained | No |
| 2026-02-23 | Preferred linter | ruff | Fastest Python linter, replaces flake8+isort+pylint | No |
| 2026-02-23 | Preferred test framework | pytest | Industry standard, rich ecosystem, simple syntax | No |
| 2026-02-23 | Preferred API framework | FastAPI | Async, typed, auto-docs, modern Python | No |
| 2026-02-23 | Skills file granularity | One file per skill domain (8 skills) | Enough detail without fragmentation | No |
| 2026-02-23 | Feature file granularity | One file per core feature (4 features) | Covers the key operational patterns | No |
