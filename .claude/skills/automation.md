# Skill: Automation & Scripting

## Capability

Automate repetitive tasks, build CLI tools, manage system operations.

## Tools Used

- **Bash** — execute scripts, system commands, process management
- **Write** — create automation scripts
- **Edit** — modify existing scripts
- **TodoWrite** — plan and track multi-step automation tasks

## Patterns

### CLI Tool (click)
```python
import click

@click.command()
@click.argument("name")
@click.option("--count", default=1, help="Number of greetings")
def hello(name, count):
    for _ in range(count):
        click.echo(f"Hello, {name}!")

if __name__ == "__main__":
    hello()
```

### File Processing
```python
from pathlib import Path

for path in Path(".").rglob("*.py"):
    content = path.read_text()
    # process...
```

### Task Scheduling
```python
import subprocess
result = subprocess.run(["python3", "task.py"], capture_output=True, text=True)
print(result.stdout)
```

### Environment Management
```bash
export KEY=value
python3 -c "import os; print(os.environ['KEY'])"
```

## Conventions

- Use pathlib over os.path
- subprocess.run over os.system
- click or argparse for CLI tools
- Log to stderr, output to stdout
- Exit codes: 0 success, 1 error

## Background Agent Usage

- Long-running scripts in background
- Parallel file processing tasks
- Background system monitoring while coding
