# Skill: Web Development & APIs

## Capability

Build web applications, REST APIs, and HTTP clients using Python frameworks.

## Tools Used

- **Bash** — run servers, curl endpoints, install frameworks
- **Write/Edit** — create and modify web application code
- **WebFetch** — fetch and analyze web content
- **WebSearch** — research APIs, documentation, libraries

## Patterns

### FastAPI (Preferred for APIs)
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}
```
```bash
uvicorn main:app --reload
```

### Flask (Lightweight)
```python
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "ok"
```

### HTTP Client
```python
import httpx  # or requests
response = httpx.get("https://api.example.com/data")
data = response.json()
```

### API Testing
```bash
curl -s http://localhost:8000/api/endpoint | python3 -m json.tool
```

## Conventions

- FastAPI for new APIs (async, typed, auto-docs)
- Flask for simple web apps
- Django for full-stack applications
- httpx over requests for async support
- Always validate external input
- Never hardcode secrets — use environment variables

## Background Agent Usage

- Run servers in background during development
- Background API testing while writing code
- Parallel endpoint testing for multiple routes
