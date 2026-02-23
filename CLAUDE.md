# CLAUDE.md - CML Python Playground

## Project Identity

This is a **Python playground** for experimenting with Python concepts, patterns, and tools.
Owned by **coding-monkey-labs**. Licensed under MIT.

## Soul

See [.claude/soul.md](.claude/soul.md) for core identity and personality.

## Operating Mode: Background Agents First

**Primary execution model**: Run tasks as background agents whenever possible.
Use `run_in_background: true` for all independent, parallelizable work.
Only run foreground when results are needed immediately for the next step.

### Decision Policy: YES-Default

When a decision is needed during autonomous/background execution:
- **Default answer: YES** — proceed with the most reasonable option
- **Document every auto-decision** in `.claude/decisions/log.md`
- Format: `| date | context | decision | reasoning | override? |`
- Never block on a decision that can be safely defaulted
- If the decision is destructive or irreversible, pause and ask

## Project Structure

```
.
├── CLAUDE.md                    # This file - top-level Claude config
├── .claude/
│   ├── soul.md                  # Core techie soul/identity
│   ├── skills/                  # Available tool skills
│   │   ├── python-core.md       # Python development
│   │   ├── git-workflow.md      # Git operations
│   │   ├── testing.md           # Testing frameworks
│   │   ├── code-quality.md      # Linting, formatting, type checking
│   │   ├── data-science.md      # Data processing & notebooks
│   │   ├── web-dev.md           # Web frameworks & APIs
│   │   ├── automation.md        # Scripting & task automation
│   │   └── search-explore.md    # Codebase search & exploration
│   ├── features/                # Capability definitions
│   │   ├── background-agents.md # Background agent patterns
│   │   ├── parallel-execution.md# Parallel task execution
│   │   ├── task-management.md   # Todo tracking & planning
│   │   └── decision-automation.md# YES-default decision system
│   └── decisions/
│       └── log.md               # Decision audit log
├── .gitignore
├── LICENSE
└── README.md
```

## Tech Stack

- **Language**: Python 3.x
- **Package Management**: uv (preferred), pip, poetry
- **Testing**: pytest
- **Type Checking**: mypy
- **Linting**: ruff
- **Formatting**: ruff format, black
- **Notebooks**: Jupyter
- **Frameworks**: Flask, Django, FastAPI (as needed)

## Conventions

- Write clean, minimal Python — no over-engineering
- Prefer standard library when possible
- Use type hints for public interfaces
- Tests live alongside code or in `tests/` directory
- One concept per module/script
- Document experiments in docstrings, not separate files

## Background Agent Patterns

When working on tasks:

1. **Explore** — spawn background Explore agents for codebase research
2. **Plan** — use Plan agents for architecture decisions
3. **Execute** — run independent file operations in parallel
4. **Validate** — background agents for testing and linting
5. **Report** — aggregate results and surface to user

Always maximize parallelism. If two tasks don't depend on each other, run them concurrently.
