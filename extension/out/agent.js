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
exports.NeuroForgeAgent = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const child_process_1 = require("child_process");
class NeuroForgeAgent {
    constructor(context) {
        this.context = context;
        this.pythonProcess = null;
        this.ws = null;
        this.isConnected = false;
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
        this.config = vscode.workspace.getConfiguration('neuroforge');
        this.startPythonAgent();
    }
    async startPythonAgent() {
        try {
            const pythonPath = this.config.get('pythonPath') || 'python';
            const agentPath = path.join(this.context.extensionPath, '..', 'agent', 'task_agent.py');
            console.log('Starting Python agent:', pythonPath, agentPath);
            this.pythonProcess = (0, child_process_1.spawn)(pythonPath, [agentPath, '--vscode-mode'], {
                cwd: this.workspaceRoot,
                stdio: ['pipe', 'pipe', 'pipe']
            });
            this.pythonProcess.stdout?.on('data', (data) => {
                console.log('Python stdout:', data.toString());
            });
            this.pythonProcess.stderr?.on('data', (data) => {
                console.error('Python stderr:', data.toString());
            });
            this.pythonProcess.on('exit', (code) => {
                console.log('Python process exited with code:', code);
                this.isConnected = false;
            });
            // Wait a moment for the Python process to start
            await new Promise(resolve => setTimeout(resolve, 2000));
            // TODO: Connect via WebSocket or stdio for communication
            this.isConnected = true;
        }
        catch (error) {
            console.error('Failed to start Python agent:', error);
            vscode.window.showErrorMessage(`Failed to start NeuroForge agent: ${error}`);
        }
    }
    async storeMemory(content, tags = []) {
        if (!this.isConnected) {
            throw new Error('Agent not connected');
        }
        // For now, return a mock response
        // TODO: Implement actual communication with Python agent
        return new Promise((resolve) => {
            const contextId = Math.random().toString(36).substring(7);
            console.log('Storing memory:', { content, tags, contextId });
            resolve(contextId);
        });
    }
    async searchMemory(query) {
        if (!this.isConnected) {
            throw new Error('Agent not connected');
        }
        // For now, return mock results
        // TODO: Implement actual communication with Python agent
        return new Promise((resolve) => {
            console.log('Searching memory for:', query);
            resolve([
                {
                    id: 'mock-1',
                    content: { text: 'Mock search result for: ' + query },
                    tags: ['search', 'mock'],
                    timestamp: new Date().toISOString(),
                    session_id: 'mock-session'
                }
            ]);
        });
    }
    async submitTask(taskName, parameters = {}) {
        if (!this.isConnected) {
            throw new Error('Agent not connected');
        }
        // For now, return a mock response
        // TODO: Implement actual communication with Python agent
        return new Promise((resolve) => {
            const taskId = Math.random().toString(36).substring(7);
            console.log('Submitting task:', { taskName, parameters, taskId });
            // Simulate async task completion
            setTimeout(() => {
                resolve({
                    taskId,
                    status: 'completed',
                    result: { message: `Task ${taskName} completed successfully` }
                });
            }, 1000);
        });
    }
    async runPlugin(pluginName, parameters = {}) {
        if (!this.isConnected) {
            throw new Error('Agent not connected');
        }
        // For now, return mock results based on plugin name
        // TODO: Implement actual communication with Python agent
        return new Promise((resolve, reject) => {
            console.log('Running plugin:', { pluginName, parameters });
            switch (pluginName) {
                case 'git_autocommit':
                    resolve({ commit_hash: 'mock-hash-123', message: 'Auto-commit completed' });
                    break;
                case 'test_runner':
                    resolve({ success: true, passed: 8, total: 10, coverage: '85%' });
                    break;
                case 'doc_writer':
                    resolve({ files_created: ['README.md', 'API.md'], success: true });
                    break;
                default:
                    reject(new Error(`Unknown plugin: ${pluginName}`));
            }
        });
    }
    async updateWorkspaceContext() {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        const activeEditor = vscode.window.activeTextEditor;
        const context = {
            workspace: workspaceFolders?.map(f => f.uri.fsPath) || [],
            activeFile: activeEditor?.document.fileName,
            openFiles: vscode.window.visibleTextEditors.map(e => e.document.fileName),
            timestamp: new Date().toISOString()
        };
        await this.storeMemory(context, ['workspace-context']);
    }
    dispose() {
        if (this.ws) {
            this.ws.close();
        }
        if (this.pythonProcess) {
            this.pythonProcess.kill();
        }
    }
}
exports.NeuroForgeAgent = NeuroForgeAgent;
//# sourceMappingURL=agent.js.map