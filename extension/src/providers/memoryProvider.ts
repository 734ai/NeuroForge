import * as vscode from 'vscode';
import { NeuroForgeAgent, MemoryContext } from '../agent';

export class MemoryProvider implements vscode.TreeDataProvider<MemoryItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<MemoryItem | undefined | null | void> = new vscode.EventEmitter<MemoryItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<MemoryItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private memories: MemoryContext[] = [];

    constructor(private agent: NeuroForgeAgent) {
        this.loadMemories();
    }

    refresh(): void {
        this.loadMemories();
        this._onDidChangeTreeData.fire();
    }

    private async loadMemories(): Promise<void> {
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
        } catch (error) {
            console.error('Failed to load memories:', error);
        }
    }

    getTreeItem(element: MemoryItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: MemoryItem): Thenable<MemoryItem[]> {
        if (!element) {
            // Root level - show memory categories
            return Promise.resolve([
                new MemoryItem('Recent Memories', vscode.TreeItemCollapsibleState.Expanded, 'recent'),
                new MemoryItem('Code Snippets', vscode.TreeItemCollapsibleState.Collapsed, 'code'),
                new MemoryItem('Workspace Context', vscode.TreeItemCollapsibleState.Collapsed, 'workspace'),
                new MemoryItem('Search Results', vscode.TreeItemCollapsibleState.Collapsed, 'search')
            ]);
        } else {
            // Show memories for each category
            const filteredMemories = this.getMemoriesByCategory(element.category);
            return Promise.resolve(
                filteredMemories.map(memory => 
                    new MemoryItem(
                        this.getMemoryDisplayName(memory),
                        vscode.TreeItemCollapsibleState.None,
                        'memory',
                        memory
                    )
                )
            );
        }
    }

    private getMemoriesByCategory(category: string): MemoryContext[] {
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

    private getMemoryDisplayName(memory: MemoryContext): string {
        if (memory.content.type === 'code_snippet') {
            return `Code: ${memory.content.text.substring(0, 30)}...`;
        } else if (memory.content.type === 'workspace_context') {
            return `Workspace: ${memory.content.files?.length || 0} files`;
        }
        return `Memory: ${memory.id}`;
    }
}

export class MemoryItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly category: string,
        public readonly memory?: MemoryContext
    ) {
        super(label, collapsibleState);
        
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
