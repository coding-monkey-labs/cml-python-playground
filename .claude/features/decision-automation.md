# Feature: Decision Automation (YES-Default)

## Overview

When running autonomously (especially as background agents), decisions will arise
that would normally require human input. To avoid blocking, we use a **YES-default**
policy: proceed with the most reasonable option and document the decision.

## Policy

### Default: YES

When a decision point is encountered during autonomous execution:

1. **Choose YES** — the most forward-moving, reasonable option
2. **Document** — log the decision in `.claude/decisions/log.md`
3. **Continue** — don't block, keep working
4. **Flag** — note if the decision might need review

### Exception: STOP and Ask

Pause and ask the user when:

- **Destructive action** — deleting data, force-pushing, dropping tables
- **Irreversible change** — architectural decisions that are hard to undo
- **Security-sensitive** — anything involving credentials, permissions, access
- **Ambiguous requirement** — when "YES" doesn't clearly map to an option
- **Cost-incurring** — actions that spend money or resources

## Decision Log Format

Every auto-decision gets logged to `.claude/decisions/log.md`:

```markdown
| Date | Context | Decision | Reasoning | Needs Review? |
|------|---------|----------|-----------|---------------|
| 2026-02-23 | Package choice for HTTP | Chose httpx | Modern, async-native, typed | No |
| 2026-02-23 | Test framework | Chose pytest | Industry standard, rich plugins | No |
```

## Examples

### YES-Default (Proceed)
- "Should I create a virtual environment?" → **YES**, document it
- "Should I add type hints?" → **YES**, document it
- "Which test framework?" → **pytest** (most reasonable default), document it
- "Should I add a .gitignore entry?" → **YES**, document it

### STOP (Ask User)
- "Should I delete the production database?" → **STOP**
- "Should I force-push to main?" → **STOP**
- "Should I commit the .env file?" → **STOP**
- "OAuth or JWT for auth?" → **STOP** (architectural, hard to change later)

## Integration with Background Agents

Background agents MUST follow this policy:
1. Make YES-default decisions autonomously
2. Log every decision made
3. Return a summary of decisions in their output
4. Flag any decisions that need user review
