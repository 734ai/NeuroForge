import * as vscode from 'vscode';
import { NeuroForgeAgent } from './agent';
import { MemoryProvider } from './providers/memoryProvider';
import { TaskProvider } from './providers/taskProvider';
import { MemoryWebView } from './webview/memoryWebView';

export function activate(context: vscode.ExtensionContext) {
    console.log('NeuroForge extension is now active!');

    // Initialize the agent
    const agent = new NeuroForgeAgent(context);
    
    // Initialize providers
    const memoryProvider = new MemoryProvider(agent);
    const taskProvider = new TaskProvider(agent);
    
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
    const memoryWebView = new MemoryWebView(context, agent);

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
            } catch (error) {
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
                        vscode.window.showInformationMessage(
                            `Tests completed: ${result.passed}/${result.total} passed`
                        );
                    } else {
                        vscode.window.showErrorMessage(`Tests failed: ${result.error}`);
                    }
                });
            } catch (error) {
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

export function deactivate() {
    console.log('NeuroForge extension deactivated');
}
