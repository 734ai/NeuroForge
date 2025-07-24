"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.MemoryWebView = void 0;
const vscode = __importStar(require("vscode"));
class MemoryWebView {
    constructor(context, agent) {
        this.context = context;
        this.agent = agent;
    }
    show() {
        if (this.panel) {
            this.panel.reveal();
            return;
        }
        this.panel = vscode.window.createWebviewPanel('neuroforgeMemoryBrowser', 'NeuroForge Memory Browser', vscode.ViewColumn.Two, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        this.panel.webview.html = this.getWebviewContent();
        this.panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'search':
                    await this.handleSearch(message.query);
                    break;
                case 'storeMemory':
                    await this.handleStoreMemory(message.content, message.tags);
                    break;
            }
        }, undefined, this.context.subscriptions);
        this.panel.onDidDispose(() => {
            this.panel = undefined;
        });
    }
    showSearchResults(query, results) {
        if (!this.panel) {
            this.show();
        }
        this.panel.webview.postMessage({
            command: 'showSearchResults',
            query: query,
            results: results
        });
    }
    async handleSearch(query) {
        try {
            const results = await this.agent.searchMemory(query);
            this.panel.webview.postMessage({
                command: 'searchResults',
                results: results
            });
        }
        catch (error) {
            vscode.window.showErrorMessage(`Search failed: ${error}`);
        }
    }
    async handleStoreMemory(content, tags) {
        try {
            const contextId = await this.agent.storeMemory(content, tags);
            this.panel.webview.postMessage({
                command: 'memoryStored',
                contextId: contextId
            });
            vscode.window.showInformationMessage('Memory stored successfully');
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to store memory: ${error}`);
        }
    }
    getWebviewContent() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NeuroForge Memory Browser</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .search-section {
            margin-bottom: 30px;
        }
        
        .search-box {
            width: 100%;
            padding: 12px;
            border: 1px solid var(--vscode-input-border);
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 4px;
            font-size: 14px;
        }
        
        .search-button, .store-button {
            padding: 10px 20px;
            margin: 10px 5px 0 0;
            border: none;
            border-radius: 4px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            cursor: pointer;
            font-size: 14px;
        }
        
        .search-button:hover, .store-button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        
        .memory-item {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            background: var(--vscode-editor-background);
        }
        
        .memory-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .memory-id {
            font-family: monospace;
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
        }
        
        .memory-tags {
            display: flex;
            gap: 5px;
        }
        
        .tag {
            background: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
        }
        
        .memory-content {
            background: var(--vscode-textCodeBlock-background);
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
            white-space: pre-wrap;
            margin: 10px 0;
        }
        
        .store-section {
            border-top: 1px solid var(--vscode-panel-border);
            padding-top: 20px;
            margin-top: 30px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .form-input, .form-textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid var(--vscode-input-border);
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
        }
        
        .form-textarea {
            height: 100px;
            resize: vertical;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 NeuroForge Memory Browser</h1>
        
        <div class="search-section">
            <h2>Search Memories</h2>
            <input type="text" id="searchQuery" class="search-box" placeholder="Enter search terms...">
            <button class="search-button" onclick="searchMemories()">Search</button>
        </div>
        
        <div id="searchResults"></div>
        
        <div class="store-section">
            <h2>Store New Memory</h2>
            <div class="form-group">
                <label class="form-label" for="memoryContent">Content:</label>
                <textarea id="memoryContent" class="form-textarea" placeholder="Enter memory content..."></textarea>
            </div>
            <div class="form-group">
                <label class="form-label" for="memoryTags">Tags (comma-separated):</label>
                <input type="text" id="memoryTags" class="form-input" placeholder="e.g. important, code, idea">
            </div>
            <button class="store-button" onclick="storeMemory()">Store Memory</button>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        
        function searchMemories() {
            const query = document.getElementById('searchQuery').value.trim();
            if (!query) {
                return;
            }
            
            vscode.postMessage({
                command: 'search',
                query: query
            });
        }
        
        function storeMemory() {
            const content = document.getElementById('memoryContent').value.trim();
            const tagsStr = document.getElementById('memoryTags').value.trim();
            
            if (!content) {
                return;
            }
            
            const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()) : [];
            
            vscode.postMessage({
                command: 'storeMemory',
                content: { text: content, type: 'user_input' },
                tags: tags
            });
            
            // Clear form
            document.getElementById('memoryContent').value = '';
            document.getElementById('memoryTags').value = '';
        }
        
        // Handle Enter key in search box
        document.getElementById('searchQuery').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchMemories();
            }
        });
        
        // Listen for messages from the extension
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.command) {
                case 'searchResults':
                    displaySearchResults(message.results);
                    break;
                case 'showSearchResults':
                    document.getElementById('searchQuery').value = message.query;
                    displaySearchResults(message.results);
                    break;
                case 'memoryStored':
                    console.log('Memory stored with ID:', message.contextId);
                    break;
            }
        });
        
        function displaySearchResults(results) {
            const container = document.getElementById('searchResults');
            
            if (!results || results.length === 0) {
                container.innerHTML = '<p>No memories found.</p>';
                return;
            }
            
            let html = '<h3>Search Results (' + results.length + ')</h3>';
            
            results.forEach(memory => {
                const contentStr = typeof memory.content === 'string' ? 
                    memory.content : 
                    JSON.stringify(memory.content, null, 2);
                
                html += \`
                    <div class="memory-item">
                        <div class="memory-header">
                            <span class="memory-id">\${memory.id}</span>
                            <div class="memory-tags">
                                \${memory.tags.map(tag => \`<span class="tag">\${tag}</span>\`).join('')}
                            </div>
                        </div>
                        <div class="memory-content">\${contentStr}</div>
                        <small>Stored: \${new Date(memory.timestamp).toLocaleString()}</small>
                    </div>
                \`;
            });
            
            container.innerHTML = html;
        }
    </script>
</body>
</html>`;
    }
}
exports.MemoryWebView = MemoryWebView;
//# sourceMappingURL=memoryWebView.js.map