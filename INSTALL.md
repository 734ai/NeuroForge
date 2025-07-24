# NeuroForge Installation Guide

## Prerequisites

- VS Code version 1.74.0 or higher
- Python 3.8+ 
- Git

## Installation

### Method 1: Install from VSIX Package

1. Download the `neuroforge-0.1.0.vsix` file
2. Open VS Code
3. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
4. Type "Extensions: Install from VSIX..."
5. Select the downloaded `.vsix` file
6. Restart VS Code when prompted

### Method 2: Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/NeuroForge.git
   cd NeuroForge
   ```

2. Install Python dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install the extension:
   ```bash
   cd extension
   npm install
   npm run compile
   code --install-extension neuroforge-0.1.0.vsix
   ```

## First Run

1. Open VS Code in a workspace folder
2. Open the Command Palette (`Ctrl+Shift+P`)
3. Type "NeuroForge" to see available commands:
   - `NeuroForge: Show Memory Browser` - View your memory store
   - `NeuroForge: Show Task View` - View and manage tasks

## Python Environment Setup

The extension will automatically detect your Python environment. If you need to specify a custom environment:

1. Open VS Code Settings (`Ctrl+,`)
2. Search for "python.pythonPath"
3. Set the path to your Python interpreter

## Troubleshooting

### Extension Not Loading
- Ensure VS Code version is 1.74.0+
- Check the Output panel for error messages
- Restart VS Code

### Python Errors
- Verify Python is in your PATH
- Check that all dependencies are installed: `pip list`
- Ensure the virtual environment is activated

### Memory Store Issues
- The extension creates a `memory_store` directory in your workspace
- Check file permissions if you see access errors

## Development Setup

For developers who want to modify the extension:

1. Clone and setup as above
2. Open the `extension` folder in VS Code
3. Press `F5` to launch Extension Development Host
4. Make changes and reload with `Ctrl+R`

## Features

- **Memory Engine**: Persistent storage of code patterns and solutions
- **Task Automation**: AI-powered task completion and workflow optimization  
- **Smart Browser**: Visual exploration of your memory store
- **Command Integration**: Seamless VS Code command palette integration

## Support

For issues and questions:
- Check the [GitHub Issues](https://github.com/your-username/NeuroForge/issues)
- Read the documentation in `README.md`
- Review the development roadmap in `todo.md`
