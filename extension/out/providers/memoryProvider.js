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
exports.MemoryItem = exports.MemoryProvider = void 0;
const vscode = __importStar(require("vscode"));
class MemoryProvider {
    constructor(agent) {
        this.agent = agent;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.memories = [];
        this.loadMemories();
    }
    refresh() {
        this.loadMemories();
        this._onDidChangeTreeData.fire();
    }
    async loadMemories() {
        try {
            // For now, we'll create some mock memories
            // TODO: Get actual memories from the agent
            this.memories = [
                {
                    id: 'mem-1',
                    content: { type: 'code_snippet', text: 'function example() { return "hello"; }' },
                    tags: ['javascript', 'function'],
                    timestamp: new Date().toISOString(),
                    session_id: 'session-1'
                },
                {
                    id: 'mem-2',
                    content: { type: 'workspace_context', files: ['src/index.ts'] },
                    tags: ['workspace', 'context'],
                    timestamp: new Date().toISOString(),
                    session_id: 'session-1'
                }
            ];
        }
        catch (error) {
            console.error('Failed to load memories:', error);
        }
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            // Root level - show memory categories
            return Promise.resolve([
                new MemoryItem('Recent Memories', vscode.TreeItemCollapsibleState.Expanded, 'recent'),
                new MemoryItem('Code Snippets', vscode.TreeItemCollapsibleState.Collapsed, 'code'),
                new MemoryItem('Workspace Context', vscode.TreeItemCollapsibleState.Collapsed, 'workspace'),
                new MemoryItem('Search Results', vscode.TreeItemCollapsibleState.Collapsed, 'search')
            ]);
        }
        else {
            // Show memories for each category
            const filteredMemories = this.getMemoriesByCategory(element.category);
            return Promise.resolve(filteredMemories.map(memory => new MemoryItem(this.getMemoryDisplayName(memory), vscode.TreeItemCollapsibleState.None, 'memory', memory)));
        }
    }
    getMemoriesByCategory(category) {
        switch (category) {
            case 'recent':
                return this.memories.slice(-5); // Last 5 memories
            case 'code':
                return this.memories.filter(m => m.tags.includes('code') || m.tags.includes('javascript'));
            case 'workspace':
                return this.memories.filter(m => m.tags.includes('workspace'));
            case 'search':
                return []; // Will be populated when search is performed
            default:
                return [];
        }
    }
    getMemoryDisplayName(memory) {
        if (memory.content.type === 'code_snippet') {
            return `Code: ${memory.content.text.substring(0, 30)}...`;
        }
        else if (memory.content.type === 'workspace_context') {
            return `Workspace: ${memory.content.files?.length || 0} files`;
        }
        return `Memory: ${memory.id}`;
    }
}
exports.MemoryProvider = MemoryProvider;
class MemoryItem extends vscode.TreeItem {
    constructor(label, collapsibleState, category, memory) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.category = category;
        this.memory = memory;
        this.tooltip = this.memory ?
            `${this.memory.content.type || 'Memory'} - ${this.memory.tags.join(', ')}` :
            `${this.label} category`;
        this.contextValue = this.memory ? 'memory' : 'category';
        if (this.memory) {
            this.command = {
                command: 'neuroforge.openMemory',
                title: 'Open Memory',
                arguments: [this.memory]
            };
        }
    }
}
exports.MemoryItem = MemoryItem;
//# sourceMappingURL=memoryProvider.js.map