# 🧠 NeuroForge

> **Memory-Controlled Processing for Task Automation in VSCode — State-of-the-Art Dev Agent Core**

**NeuroForge** is an advanced memory engine and task automation controller designed to operate within **Visual Studio Code** and **VSCode Insider**. It brings long-term memory, code-awareness, and agent-like orchestration to your local development environment — without relying on the cloud.

Whether you're automating repetitive workflows, integrating local LLMs, or building a powerful AI-driven IDE, NeuroForge is the missing memory + automation layer for the future of developer productivity.

---

## ✨ Features

* 🧠 **Hybrid Memory Engine** — Uses RAM for rapid state access and persistent LMDB/SQLite/ChromaDB for long-term memory.
* 📚 **Contextual Awareness** — Fully aware of your open workspace, Git diffs, open files, and development stack.
* 🤖 **Agent-Oriented Execution** — Run smart agents for testing, fixing, documenting, debugging, or refactoring code.
* 🧩 **Toolchain Integration** — Hooks into Git, Docker, Kubernetes, Bash, and any CLI you define.
* ⚙️ **VSCode Native Extension** — Seamless UI integration via Command Palette, WebView panel, and Notifications.
* 🗂️ **Modular Task Plugins** — Write automation logic in Python, Node, or Bash. Supports chained actions.
* 🔄 **Self-Learning Feedback Loop** — Save, update, and replay memory states across sessions and tasks.
* 🧬 **LLM-Aware (Optional)** — Integrates with Ollama, GPT-4, Claude, or your own local models.
* 🔐 **Offline-First & Secure** — Operates airgapped, stores memory locally, supports AES-encrypted logs.

---

## 📦 Project Structure

```
neuroforge/
├── extension/                  # VSCode extension logic (TypeScript)
│   ├── src/
│   ├── webview/
│   └── package.json
├── agent/                      # Python-based agent and memory logic
│   ├── memory_engine.py        # RAM + persistent store memory backend
│   ├── task_agent.py           # Main agent loop
│   └── plugins/                # Action modules
│       ├── git_autocommit.py
│       ├── test_runner.py
│       └── doc_writer.py
├── memory_store/              # Memory database snapshots
├── mcp.json                   # Component registry & agent/task definitions
├── requirements.md            # Software dependencies
├── todo.md                    # Feature roadmap and dev checklist
└── README.md
```

---

## 🚀 Usage

### ⚙️ Install Extension (Dev)

1. Clone this repo
2. Open in VSCode
3. Press `F5` to run the extension in a dev window

### 🧪 Run an Agent Task

Open Command Palette → `MCP: Run Task` →

Example:

> "Generate unit tests for recently changed Python files and fix style issues."

NeuroForge will:

* Check memory for prior test attempts
* Load recent diffs
* Execute chained plugins (TestGenAgent → LinterFixAgent)
* Display results and memory trace in the panel

---

## 📡 Integrations (Optional)

* 🧠 LLMs: OpenAI, Ollama, Claude, LM Studio
* 🧪 DevTools: PyTest, ESLint, Docker, Git, Bash
* 🗂 Memory Engines: LMDB, ChromaDB, DuckDB, SQLite

---

## 🛡 OPSEC & Privacy

* No telemetry
* Offline memory by default
* Encrypted storage optional (AES256)
* Entire system sandboxable

---

## 📝 License

MIT License © 2025 Muzan Sano
