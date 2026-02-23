# Skill: Python Core Development

## Capability

Write, execute, debug, and iterate on Python code. This is the foundational skill
that everything else builds on.

## Tools Used

- **Bash** — run Python scripts, install packages, manage environments
- **Write** — create new Python files
- **Edit** — modify existing Python code
- **Read** — inspect Python source files

## Patterns

### Quick Script
```bash
python3 script.py
```

### Virtual Environment
```bash
python3 -m venv .venv && source .venv/bin/activate
# or with uv:
uv venv && source .venv/bin/activate
```

### Package Install
```bash
uv pip install <package>
# or:
pip install <package>
```

### REPL Experimentation
```bash
python3 -c "print('quick test')"
```

## Conventions

- Python 3.10+ features preferred (match/case, type unions with |)
- Use `if __name__ == '__main__':` for runnable scripts
- Type hints on public functions
- Docstrings for non-obvious functions
- Standard library first, third-party only when justified

## Background Agent Usage

- Run scripts in background when output isn't needed immediately
- Parallel execution of independent scripts
- Background install of dependencies while writing code
