# Feature: Task Management

## Overview

Every non-trivial task gets a todo list. Track progress visibly.
Never work from memory — always work from a tracked list.

## Tool: TodoWrite

### When to Use
- Task has 3+ steps
- Multiple files to modify
- Multi-phase work (research → plan → implement → test)
- User provides a list of requirements

### When NOT to Use
- Single simple task
- Trivial one-step operation
- Pure Q&A / informational response

## Task States

| State | Meaning | Rule |
|---|---|---|
| `pending` | Not started | Created during planning |
| `in_progress` | Currently working on | **Max 1 at a time** |
| `completed` | Done | Mark **immediately** after finishing |

## Workflow

1. **Receive task** → decompose into steps
2. **Create todos** → all steps as pending
3. **Start first** → mark in_progress
4. **Complete** → mark completed, start next
5. **Adapt** → add new todos if discovered during work
6. **Finish** → all todos completed

## Naming Convention

- `content`: imperative form — "Fix the auth bug"
- `activeForm`: present continuous — "Fixing the auth bug"

## Rules

- Mark completed IMMEDIATELY — no batching
- Only ONE in_progress at a time
- Remove irrelevant todos — don't leave stale items
- Break large tasks into smaller pieces
- Never mark completed if there are unresolved errors
- Update the list as new work is discovered

## Integration with Background Agents

- Create todos before spawning background agents
- Mark in_progress when agent starts
- Mark completed when agent output is verified
- Add new todos if agent discovers additional work
