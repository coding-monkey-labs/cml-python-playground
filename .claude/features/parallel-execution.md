# Feature: Parallel Execution

## Overview

Maximize throughput by running independent operations concurrently.
If two things don't depend on each other, they run at the same time.

## Parallel Patterns

### Independent Tool Calls
When multiple tools need to run and none depend on each other's output,
call them all in a single message block.

**Example**: Reading 3 files simultaneously
```
Read(file_a.py)  |  Read(file_b.py)  |  Read(file_c.py)
```

### Independent Agent Spawns
Launch multiple Task agents in a single message for concurrent research.

**Example**: Exploring different aspects of a codebase
```
Task(Explore: "find all API endpoints")  |  Task(Explore: "find all test files")
```

### Independent Bash Commands
Run multiple commands simultaneously when they don't interfere.

**Example**: Install packages while running linter
```
Bash("uv pip install requests")  |  Bash("ruff check .")
```

## Dependency Detection

Before parallelizing, verify operations are truly independent:

| Independent (Parallel OK) | Dependent (Must Sequence) |
|---|---|
| Reading different files | Read file → Edit same file |
| Searching different patterns | Create dir → Write file in it |
| Running tests + linting | Install package → Import it |
| Multiple Explore agents | Git add → Git commit |

## Anti-Patterns

- **Don't parallelize** writes to the same file
- **Don't parallelize** commands that share state (same DB, same port)
- **Don't parallelize** when order matters (migrations, sequential scripts)
- **Don't guess** dependent values — wait for the prior step

## Maximize Parallelism Checklist

1. Identify all subtasks
2. Map dependencies between them
3. Group independent tasks
4. Execute each group in parallel
5. Sequence between groups
