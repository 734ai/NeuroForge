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
exports.TaskItem = exports.TaskProvider = void 0;
const vscode = __importStar(require("vscode"));
class TaskProvider {
    constructor(agent) {
        this.agent = agent;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.tasks = [];
        this.loadTasks();
    }
    refresh() {
        this.loadTasks();
        this._onDidChangeTreeData.fire();
    }
    async loadTasks() {
        try {
            // For now, we'll create some mock tasks
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
                }
            ];
        }
        catch (error) {
            console.error('Failed to load tasks:', error);
        }
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            // Root level - show task categories
            return Promise.resolve([
                new TaskItem('Running Tasks', vscode.TreeItemCollapsibleState.Expanded, 'running'),
                new TaskItem('Completed Tasks', vscode.TreeItemCollapsibleState.Collapsed, 'completed'),
                new TaskItem('Pending Tasks', vscode.TreeItemCollapsibleState.Collapsed, 'pending'),
                new TaskItem('Failed Tasks', vscode.TreeItemCollapsibleState.Collapsed, 'failed')
            ]);
        }
        else {
            // Show tasks for each category
            const filteredTasks = this.getTasksByCategory(element.category);
            return Promise.resolve(filteredTasks.map(task => new TaskItem(this.getTaskDisplayName(task), vscode.TreeItemCollapsibleState.None, 'task', task)));
        }
    }
    getTasksByCategory(category) {
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
    getTaskDisplayName(task) {
        const message = task.result?.message || task.error || 'Unknown task';
        return `${task.taskId}: ${message}`;
    }
}
exports.TaskProvider = TaskProvider;
class TaskItem extends vscode.TreeItem {
    constructor(label, collapsibleState, category, task) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.category = category;
        this.task = task;
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
exports.TaskItem = TaskItem;
//# sourceMappingURL=taskProvider.js.map