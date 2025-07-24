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
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
const agent_1 = require("./agent");
const memoryProvider_1 = require("./providers/memoryProvider");
const taskProvider_1 = require("./providers/taskProvider");
const memoryWebView_1 = require("./webview/memoryWebView");
function activate(context) {
    console.log('NeuroForge extension is now active!');
    // Initialize the agent
    const agent = new agent_1.NeuroForgeAgent(context);
    // Initialize providers
    const memoryProvider = new memoryProvider_1.MemoryProvider(agent);
    const taskProvider = new taskProvider_1.TaskProvider(agent);
    // Register tree views
    vscode.window.createTreeView('neuroforgeMemory', {
        treeDataProvider: memoryProvider,
        showCollapseAll: true
    });
    vscode.window.createTreeView('neuroforgeTasks', {
        treeDataProvider: taskProvider,
        showCollapseAll: true
    });
    // Initialize webview
    const memoryWebView = new memoryWebView_1.MemoryWebView(context, agent);
    // Register commands
    const commands = [
        vscode.commands.registerCommand('neuroforge.showMemoryBrowser', () => {
            memoryWebView.show();
        }),
        vscode.commands.registerCommand('neuroforge.runTask', async () => {
            const taskName = await vscode.window.showInputBox({
                prompt: 'Enter task name or description',
                placeHolder: 'e.g., "run tests", "commit changes", "generate docs"'
            });
            if (taskName) {
                const result = await agent.submitTask(taskName, {});
                vscode.window.showInformationMessage(`Task submitted: ${result.taskId}`);
                taskProvider.refresh();
            }
        }),
        vscode.commands.registerCommand('neuroforge.storeMemory', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active editor');
                return;
            }
            const selection = editor.selection;
            const text = editor.document.getText(selection.isEmpty ? undefined : selection);
            const fileName = editor.document.fileName;
            const tags = await vscode.window.showInputBox({
                prompt: 'Enter tags (comma-separated)',
                placeHolder: 'e.g., important, bug-fix, refactor'
            });
            const tagList = tags ? tags.split(',').map(t => t.trim()) : [];
            await agent.storeMemory({
                content: text,
                file: fileName,
                selection: selection.isEmpty ? null : {
                    start: { line: selection.start.line, character: selection.start.character },
                    end: { line: selection.end.line, character: selection.end.character }
                }
            }, tagList);
            vscode.window.showInformationMessage('Memory stored successfully');
            memoryProvider.refresh();
        }),
        vscode.commands.registerCommand('neuroforge.searchMemory', async () => {
            const query = await vscode.window.showInputBox({
                prompt: 'Search memory',
                placeHolder: 'Enter search terms...'
            });
            if (query) {
                const results = await agent.searchMemory(query);
                memoryWebView.showSearchResults(query, results);
            }
        }),
        vscode.commands.registerCommand('neuroforge.autoCommit', async () => {
            try {
                const result = await agent.runPlugin('git_autocommit', {});
                vscode.window.showInformationMessage(`Auto-commit completed: ${result.commit_hash}`);
            }
            catch (error) {
                vscode.window.showErrorMessage(`Auto-commit failed: ${error}`);
            }
        }),
        vscode.commands.registerCommand('neuroforge.runTests', async () => {
            try {
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: "Running tests with NeuroForge...",
                    cancellable: false
                }, async (progress) => {
                    const result = await agent.runPlugin('test_runner', {});
                    if (result.success) {
                        vscode.window.showInformationMessage(`Tests completed: ${result.passed}/${result.total} passed`);
                    }
                    else {
                        vscode.window.showErrorMessage(`Tests failed: ${result.error}`);
                    }
                });
            }
            catch (error) {
                vscode.window.showErrorMessage(`Test execution failed: ${error}`);
            }
        })
    ];
    // Register event listeners
    const disposables = [
        // Auto-store context on file changes (if enabled)
        vscode.workspace.onDidChangeTextDocument(async (event) => {
            const config = vscode.workspace.getConfiguration('neuroforge');
            if (config.get('autoStoreContext')) {
                // Debounce to avoid too frequent updates
                setTimeout(async () => {
                    await agent.updateWorkspaceContext();
                    memoryProvider.refresh();
                }, 2000);
            }
        }),
        // Update context on file open/close
        vscode.window.onDidChangeActiveTextEditor(async () => {
            await agent.updateWorkspaceContext();
            memoryProvider.refresh();
        }),
        // Track workspace folder changes
        vscode.workspace.onDidChangeWorkspaceFolders(async () => {
            await agent.updateWorkspaceContext();
            memoryProvider.refresh();
        })
    ];
    // Add all disposables to context
    context.subscriptions.push(...commands, ...disposables);
    // Initialize workspace context
    agent.updateWorkspaceContext();
    vscode.window.showInformationMessage('NeuroForge is ready! 🧠');
}
exports.activate = activate;
function deactivate() {
    console.log('NeuroForge extension deactivated');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map