# Skill: Search & Exploration

## Capability

Find files, search code, explore codebases, research documentation.

## Tools Used

- **Glob** — find files by pattern (fast, preferred for file discovery)
- **Grep** — search file contents by regex (fast, preferred for content search)
- **Read** — inspect file contents
- **Task (Explore)** — deep codebase exploration (slower, more thorough)
- **Task (Plan)** — architectural analysis and planning
- **WebSearch** — search the web for documentation and solutions
- **WebFetch** — fetch and analyze specific web pages

## Patterns

### Find Files
```
Glob: **/*.py          # all Python files
Glob: tests/**/*.py    # test files only
Glob: **/config*       # config files
```

### Search Code
```
Grep: "def function_name"     # find function definitions
Grep: "import module"         # find imports
Grep: "TODO|FIXME|HACK"      # find markers
```

### Deep Exploration
Use Task(Explore) for:
- Understanding unfamiliar codebases
- Finding all usages of a pattern
- Mapping dependencies between modules
- Answering architectural questions

### Web Research
- WebSearch for finding documentation, Stack Overflow answers, library comparisons
- WebFetch for reading specific documentation pages

## Conventions

- Glob/Grep first (fast, specific)
- Task(Explore) for open-ended research
- Read files directly when you know the path
- Never use bash grep/find — use the dedicated tools

## Background Agent Usage

- **Always use background Explore agents** for codebase research
- Parallel Glob + Grep for multi-pattern search
- Background WebSearch while working on implementation
- Multiple background agents for independent research questions
