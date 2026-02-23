# Feature: Background Agents

## Overview

Background agents are the **primary execution model** for this project.
Every task that can run independently SHOULD run in the background.

## Why Background-First

- **Parallelism** — multiple agents working simultaneously
- **Non-blocking** — foreground stays free for decision-making
- **Throughput** — more work done per unit of interaction
- **Autonomy** — agents complete work without constant supervision

## Agent Types

### Explore Agent (Background)
- Codebase research and discovery
- File pattern analysis
- Dependency mapping
- Architecture understanding
```
Task(subagent_type=Explore, run_in_background=true)
```

### Plan Agent (Background)
- Implementation strategy design
- Architecture decisions
- Trade-off analysis
```
Task(subagent_type=Plan, run_in_background=true)
```

### Bash Agent (Background)
- Long-running commands (tests, builds, installs)
- Server processes
- Data processing scripts
```
Bash(run_in_background=true)
```

### General-Purpose Agent (Background)
- Complex multi-step tasks
- Research requiring multiple tools
- Code generation with validation
```
Task(subagent_type=general-purpose, run_in_background=true)
```

## Patterns

### Parallel Research
Spawn multiple Explore agents for different questions simultaneously.

### Build-While-Code
Run tests/linters in background while continuing to write code.

### Research-Then-Act
1. Launch background research agent
2. Continue working on known tasks
3. Incorporate research findings when agent completes

### Fan-Out / Fan-In
1. Spawn N background agents for independent subtasks
2. Collect results from all agents
3. Synthesize into final output

## Rules

- **Foreground only when**: result needed for the immediate next step
- **Background when**: task is independent of current work
- **Always check**: background agent output before proceeding with dependent work
- **Never guess**: what a background agent will return — wait for the result
