import * as vscode from 'vscode';
import { NeuroForgeAgent, TaskResult } from '../agent';

export class TaskProvider implements vscode.TreeDataProvider<TaskItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<TaskItem | undefined | null | void> = new vscode.EventEmitter<TaskItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<TaskItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private tasks: TaskResult[] = [];

    constructor(private agent: NeuroForgeAgent) {
        this.loadTasks();
    }

    refresh(): void {
        this.loadTasks();
        this._onDidChangeTreeData.fire();
    }

    private async loadTasks(): Promise<void> {
        try {
            // For now, we'll create some mock tasks including LLM tasks
            // TODO: Get actual tasks from the agent
            this.tasks = [
                {
                    taskId: 'task-1',
                    status: 'completed',
                    result: { message: 'Git auto-commit completed' }
                },
                {
                    taskId: 'task-2',
                    status: 'running',
                    result: { message: 'Running tests...' }
                },
                {
                    taskId: 'task-3',
                    status: 'pending',
                    result: { message: 'Waiting to start documentation generation' }
                },
                {
                    taskId: 'llm-analyzer-1',
                    status: 'completed',
                    result: { message: 'Code analysis completed - 3 issues found' }
                },
                {
                    taskId: 'llm-refactor-1',
                    status: 'running',
                    result: { message: 'Refactoring suggestions being generated...' }
                },
                {
                    taskId: 'llm-docs-1',
                    status: 'pending',
                    result: { message: 'AI documentation generation queued' }
                }
            ];
        } catch (error) {
            console.error('Failed to load tasks:', error);
        }
    }

    getTreeItem(element: TaskItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: TaskItem): Thenable<TaskItem[]> {
        if (!element) {
            // Root level - show task categories
            return Promise.resolve([
                new TaskItem('Running Tasks', vscode.TreeItemCollapsibleState.Expanded, 'running'),
                new TaskItem('Completed Tasks', vscode.TreeItemCollapsibleState.Collapsed, 'completed'),
                new TaskItem('Pending Tasks', vscode.TreeItemCollapsibleState.Collapsed, 'pending'),
                new TaskItem('Failed Tasks', vscode.TreeItemCollapsibleState.Collapsed, 'failed')
            ]);
        } else {
            // Show tasks for each category
            const filteredTasks = this.getTasksByCategory(element.category);
            return Promise.resolve(
                filteredTasks.map(task => 
                    new TaskItem(
                        this.getTaskDisplayName(task),
                        vscode.TreeItemCollapsibleState.None,
                        'task',
                        task
                    )
                )
            );
        }
    }

    private getTasksByCategory(category: string): TaskResult[] {
        switch (category) {
            case 'running':
                return this.tasks.filter(t => t.status === 'running');
            case 'completed':
                return this.tasks.filter(t => t.status === 'completed');
            case 'pending':
                return this.tasks.filter(t => t.status === 'pending');
            case 'failed':
                return this.tasks.filter(t => t.status === 'failed');
            default:
                return [];
        }
    }

    private getTaskDisplayName(task: TaskResult): string {
        const message = task.result?.message || task.error || 'Unknown task';
        return `${task.taskId}: ${message}`;
    }
}

export class TaskItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly category: string,
        public readonly task?: TaskResult
    ) {
        super(label, collapsibleState);
        
        this.tooltip = this.task ? 
            `Task ${this.task.taskId} - Status: ${this.task.status}` :
            `${this.label} category`;
            
        this.contextValue = this.task ? 'task' : 'category';
        
        if (this.task) {
            // Set icon based on task status
            switch (this.task.status) {
                case 'running':
                    this.iconPath = new vscode.ThemeIcon('sync~spin');
                    break;
                case 'completed':
                    this.iconPath = new vscode.ThemeIcon('check');
                    break;
                case 'pending':
                    this.iconPath = new vscode.ThemeIcon('clock');
                    break;
                case 'failed':
                    this.iconPath = new vscode.ThemeIcon('error');
                    break;
            }
            
            this.command = {
                command: 'neuroforge.openTask',
                title: 'Open Task',
                arguments: [this.task]
            };
        }
    }
}
