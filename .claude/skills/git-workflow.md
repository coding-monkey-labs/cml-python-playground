# Skill: Git Workflow

## Capability

Version control operations — branching, committing, pushing, PR management.

## Tools Used

- **Bash** — all git commands (git, gh CLI)

## Patterns

### Branch Management
```bash
git checkout -b claude/<feature>-<session-id>
git push -u origin <branch-name>
```

### Commit Flow
```bash
git add <specific-files>
git commit -m "$(cat <<'EOF'
Descriptive commit message

<session-link>
EOF
)"
```

### PR Creation
```bash
gh pr create --title "Short title" --body "$(cat <<'EOF'
## Summary
- bullet points

## Test plan
- [ ] checklist
EOF
)"
```

### Retry on Network Failure
Retry up to 4 times with exponential backoff: 2s, 4s, 8s, 16s.

## Rules

- Never force push to main/master
- Never use `--no-verify` unless explicitly asked
- Always create NEW commits (never amend unless asked)
- Never commit .env, credentials, or secrets
- Stage specific files, not `git add -A`
- Commit messages: focus on "why" not "what"

## Background Agent Usage

- Push operations can run in background
- Parallel git status + git diff for pre-commit analysis
