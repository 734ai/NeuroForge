# NeuroForge Requirements

## System Requirements

### Core Dependencies
- **Python**: 3.9+ (for agent backend)
- **Node.js**: 16+ (for VSCode extension)
- **VSCode**: 1.70+ or VSCode Insiders

### Python Dependencies
```
# Core agent framework
asyncio
dataclasses
typing-extensions
pydantic>=2.0

# Memory & Storage
lmdb>=1.4.0
sqlite3 (built-in)
chromadb>=0.4.0
duckdb>=0.9.0

# Git integration
GitPython>=3.1.0

# Task execution
subprocess32
psutil

# Optional LLM integrations
openai>=1.0.0
anthropic
ollama-python

# Testing
pytest>=7.0.0
pytest-asyncio
```

### VSCode Extension Dependencies
```json
{
  "devDependencies": {
    "@types/vscode": "^1.70.0",
    "@types/node": "16.x",
    "typescript": "^4.9.0",
    "webpack": "^5.0.0",
    "webpack-cli": "^4.0.0"
  },
  "dependencies": {
    "node-pty": "^0.10.1",
    "ws": "^8.0.0"
  }
}
```

## Architecture Requirements

### Memory Engine
- **RAM Buffer**: Fast access for active tasks and recent context
- **Persistent Store**: LMDB for session data, SQLite for structured data
- **Vector Store**: ChromaDB for semantic code search and similarity
- **Encryption**: Optional AES256 for sensitive data

### Agent System
- **Task Queue**: Async processing with priority scheduling
- **Plugin Architecture**: Modular actions (Git, Test, Lint, etc.)
- **Context Awareness**: VSCode workspace, open files, Git state
- **Memory Integration**: Load/save state between sessions

### VSCode Integration
- **Extension Host**: TypeScript extension with WebView UI
- **Command Palette**: MCP commands and quick actions
- **Status Bar**: Memory state and active task indicators
- **Output Panel**: Task results and debug logs

### Security & Privacy
- **Offline Operation**: No cloud dependencies by default
- **Local Storage**: All data stored on user machine
- **Sandboxing**: Isolated execution environments
- **No Telemetry**: Zero data collection

## Performance Targets
- **Memory Startup**: < 2 seconds
- **Task Execution**: < 5 seconds for simple tasks
- **Context Loading**: < 1 second for workspace analysis
- **Storage Size**: < 100MB for typical project memory
