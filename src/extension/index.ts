import * as vscode from 'vscode';
import { VuePreviewProvider } from './preview/provider';
import { AimdBackend } from './backend/backend';
import { MemFS } from './providers/FileSystemProvider';
import { PythonEnvironmentManager } from './services/PythonEnvironmentManager';

let statusBarItem: vscode.StatusBarItem;
let aimdBackend: AimdBackend | null = null;

/**
 * 获取配置值
 */
function getConfig(): {
    icon: string;
    text: string;
    tooltip: string;
    priority: number;
    backgroundColor: string;
} {
    const config = vscode.workspace.getConfiguration('aimd.preview');
    return {
        icon: config.get<string>('buttonIcon', 'open-preview'),
        text: config.get<string>('buttonText', 'AIMD Preview'),
        tooltip: config.get<string>('buttonTooltip', 'Open AIMD Preview (点击打开预览)'),
        priority: config.get<number>('buttonPriority', 100),
        backgroundColor: config.get<string>('buttonBackgroundColor', '')
    };
}

/**
 * 更新状态栏按钮的显示状态
 */
function updateStatusBar(editor: vscode.TextEditor | undefined) {
    if (editor && editor.document.languageId === 'aimd') {
        const config = getConfig();

        statusBarItem.text = `$(${config.icon}) ${config.text}`;
        statusBarItem.tooltip = config.tooltip;
        statusBarItem.command = 'aimd.preview';

        if (config.backgroundColor) {
            statusBarItem.backgroundColor = new vscode.ThemeColor(config.backgroundColor);
        } else {
            statusBarItem.backgroundColor = undefined;
        }

        statusBarItem.show();
    } else {
        statusBarItem.hide();
    }
}

/**
 * 执行预览命令
 */
function executePreview() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('Please open an AIMD file to preview.');
        return;
    }

    const uri = editor.document.uri;
    if (uri.scheme !== 'file' || !uri.fsPath.endsWith('.aimd')) {
        vscode.window.showWarningMessage('Please open an .aimd file to preview.');
        return;
    }

    VuePreviewProvider.createOrShow(uri, vscode.ViewColumn.Beside);
}

export async function activate(context: vscode.ExtensionContext) {
    console.log('AIMD Studio is activating...');

    // Initialize Python Backend (async, non-blocking)
    aimdBackend = new AimdBackend(context.extensionPath);
    aimdBackend.start().catch(err => {
        console.error('Failed to start AIMD backend:', err);
    });

    // Initialize Vue Preview Provider
    VuePreviewProvider.initialize(context, aimdBackend);

    // Initialize Python Environment Manager
    const pythonEnvManager = new PythonEnvironmentManager();
    pythonEnvManager.registerCommands(context);

    const initialConfig = getConfig();

    // 创建状态栏按钮
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        initialConfig.priority
    );
    context.subscriptions.push(statusBarItem);

    // 监听配置变化
    const configWatcher = vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('aimd.preview')) {
            const newConfig = getConfig();
            if (statusBarItem.priority !== newConfig.priority) {
                statusBarItem.dispose();
                statusBarItem = vscode.window.createStatusBarItem(
                    vscode.StatusBarAlignment.Right,
                    newConfig.priority
                );
                context.subscriptions.push(statusBarItem);
            }
            updateStatusBar(vscode.window.activeTextEditor);
        }

        if (e.affectsConfiguration('aimd.preview.experimental')) {
            VuePreviewProvider.refreshAll();
        }
    });
    context.subscriptions.push(configWatcher);

    // Register MemFS for virtual documents
    const memFs = new MemFS();
    context.subscriptions.push(vscode.workspace.registerFileSystemProvider('airalogy-fs', memFs, { isCaseSensitive: true }));


    // 注册预览命令
    const previewCommand = vscode.commands.registerCommand('aimd.preview', executePreview);

    const previewToSideCommand = vscode.commands.registerCommand('aimd.previewToSide', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('Please open an AIMD file to preview.');
            return;
        }

        const uri = editor.document.uri;
        if (uri.scheme !== 'file' || !uri.fsPath.endsWith('.aimd')) {
            vscode.window.showWarningMessage('Please open an .aimd file to preview.');
            return;
        }

        VuePreviewProvider.createOrShow(uri, vscode.ViewColumn.Beside);
    });

    // Register hello backend command (for testing Python integration)
    const helloBackendCommand = vscode.commands.registerCommand('aimd.helloBackend', async () => {
        if (!aimdBackend) {
            vscode.window.showErrorMessage('AIMD Backend is not initialized');
            return;
        }

        try {
            aimdBackend.showOutput();
            const result = await aimdBackend.hello('AIMD User');
            vscode.window.showInformationMessage(
                `🐍 ${result.message}\n⏰ ${result.timestamp}`
            );
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Backend error: ${message}`);
        }
    });

    // Register restart backend command
    const restartBackendCommand = vscode.commands.registerCommand('aimd.restartBackend', async () => {
        if (aimdBackend) {
            try {
                await aimdBackend.restart();
                vscode.window.showInformationMessage('AIMD Backend restarted successfully');
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to restart backend: ${(error as Error).message}`);
            }
        }
    });

    // 监听编辑器变化
    const editorChangeDisposable = vscode.window.onDidChangeActiveTextEditor(editor => {
        updateStatusBar(editor);
    });

    const documentOpenDisposable = vscode.workspace.onDidOpenTextDocument(() => {
        updateStatusBar(vscode.window.activeTextEditor);
    });

    // 初始化状态栏
    updateStatusBar(vscode.window.activeTextEditor);

    // 注册文档监听器
    const documentWatcher = VuePreviewProvider.registerDocumentWatcher();
    const saveWatcher = VuePreviewProvider.registerSaveWatcher();
    const scrollWatcher = VuePreviewProvider.registerScrollWatcher();
    const pythonFileWatcher = VuePreviewProvider.registerPythonFileWatcher();

    // 添加到订阅
    context.subscriptions.push(previewCommand);
    context.subscriptions.push(previewToSideCommand);
    context.subscriptions.push(helloBackendCommand);
    context.subscriptions.push(restartBackendCommand);
    context.subscriptions.push(editorChangeDisposable);
    context.subscriptions.push(documentOpenDisposable);
    context.subscriptions.push(documentWatcher);
    context.subscriptions.push(saveWatcher);
    context.subscriptions.push(scrollWatcher);
    context.subscriptions.push(pythonFileWatcher);

    console.log('AIMD Studio activated (Vue mode).');
}

export function deactivate() {
    VuePreviewProvider.disposeAll();

    // Stop Python backend
    if (aimdBackend) {
        aimdBackend.dispose();
        aimdBackend = null;
    }
}
