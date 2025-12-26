import * as vscode from 'vscode';
import * as cp from 'child_process';

/**
 * Interface for the Python Extension API
 * See: https://github.com/microsoft/vscode-python/blob/main/src/client/api/types.ts
 */
interface PythonExtensionApi {
    ready: Promise<void>;
    settings: {
        getExecutionDetails(resource?: vscode.Uri): {
            execCommand: string[] | undefined;
        };
    };
    environments: {
        getActiveEnvironmentPath(resource?: vscode.Uri): {
            path: string;
        };
    };
}

export class PythonEnvironmentManager {
    private statusBarItem: vscode.StatusBarItem;
    private onEnvironmentChangedEmitter = new vscode.EventEmitter<void>();
    public readonly onEnvironmentChanged = this.onEnvironmentChangedEmitter.event;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 90);
        this.statusBarItem.command = 'aimd.selectPythonEnvironment';
        this.updateStatusBar();
    }

    public registerCommands(context: vscode.ExtensionContext) {
        context.subscriptions.push(
            vscode.commands.registerCommand('aimd.selectPythonEnvironment', () => this.showEnvironmentPicker())
        );
        context.subscriptions.push(this.statusBarItem);

        // Listen for config changes
        context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('aimd.pythonMode') || e.affectsConfiguration('aimd.systemPythonPath')) {
                this.updateStatusBar();
                this.onEnvironmentChangedEmitter.fire();
            }
        }));

        // Start watching for Python extension changes
        this.watchPythonExtensionInterpreter();
    }

    /**
     * Watch for changes in the VS Code Python extension's active interpreter
     * and sync them to our configuration if in 'system' mode.
     */
    private async watchPythonExtensionInterpreter() {
        const extension = vscode.extensions.getExtension('ms-python.python');
        if (!extension) {
            return;
        }

        if (!extension.isActive) {
            await extension.activate();
        }

        const api = extension.exports as PythonExtensionApi;
        await api.ready;

        // Poll for changes (API events can be unreliable across versions)
        // Check every 2 seconds
        setInterval(async () => {
            const config = vscode.workspace.getConfiguration('aimd');
            const mode = config.get<string>('pythonMode');

            if (mode === 'system') {
                const currentExtPath = await this.getPythonExtensionInterpreter();
                const currentAimdPath = config.get<string>('systemPythonPath');

                if (currentExtPath && currentExtPath !== currentAimdPath) {
                    // Detected change in Python extension selection, sync it!
                    await config.update('systemPythonPath', currentExtPath, vscode.ConfigurationTarget.Global);

                    // Validate dependencies for the new environment
                    await this.validateAndPromptDependencies(currentExtPath);

                    // Prompt restart since environment changed
                    this.promptRestart(`System Python (${await this.getPythonVersion(currentExtPath)})`);
                }
            }
        }, 2000);
    }

    /**
     * Check if required dependencies are installed in the given python environment
     */
    public async validateAndPromptDependencies(pythonPath: string): Promise<boolean> {
        try {
            // Check for airalogy
            const checkCmd = `"${pythonPath}" -c "import airalogy"`;
            cp.execSync(checkCmd);
            return true;
        } catch (e) {
            // Missing dependency
            const action = await vscode.window.showWarningMessage(
                `The selected Python environment is missing the required 'airalogy' package.`,
                'Install airalogy', 'Cancel'
            );

            if (action === 'Install airalogy') {
                const term = vscode.window.createTerminal('AIMD Dependency Install');
                term.show();
                term.sendText(`"${pythonPath}" -m pip install git+https://github.com/airalogy/airalogy`);
                return false; // Will need re-check or user to restart
            }
            return false;
        }
    }

    /**
     * Get the active Python path from the Official Python Extension
     */
    public async getPythonExtensionInterpreter(): Promise<string | undefined> {
        const extension = vscode.extensions.getExtension('ms-python.python');
        if (!extension) {
            return undefined;
        }

        if (!extension.isActive) {
            await extension.activate();
        }

        const api = extension.exports as PythonExtensionApi;
        await api.ready;

        // Try new API first (getActiveEnvironmentPath)
        if (api.environments && api.environments.getActiveEnvironmentPath) {
            const env = api.environments.getActiveEnvironmentPath(vscode.window.activeTextEditor?.document.uri);
            if (env && env.path) {
                return env.path;
            }
        }

        // Fallback to legacy settings API
        if (api.settings && api.settings.getExecutionDetails) {
            const details = api.settings.getExecutionDetails(vscode.window.activeTextEditor?.document.uri);
            if (details.execCommand && details.execCommand.length > 0) {
                return details.execCommand[0];
            }
        }

        return undefined;
    }

    private async showEnvironmentPicker() {
        const config = vscode.workspace.getConfiguration('aimd');
        const currentMode = config.get<string>('pythonMode');

        // Get current interpreter from Python Extension to show in detail
        const pythonExtPath = await this.getPythonExtensionInterpreter();

        let pythonExtLabel = 'Select via Python Extension...';
        if (pythonExtPath) {
            const version = await this.getPythonVersion(pythonExtPath);
            pythonExtLabel = version ? `${version} ${pythonExtPath}` : pythonExtPath;
        }

        const items: vscode.QuickPickItem[] = [
            {
                label: '$(package) Bundled Python',
                description: 'Use the embedded Python environment',
                detail: 'Recommended for standard usage. Includes all standard dependencies.',
                picked: currentMode === 'bundled'
            },
            {
                label: '$(terminal) System Python',
                description: 'Use environment selected in Python Extension',
                detail: pythonExtLabel,
                picked: currentMode === 'system'
            }
        ];

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select AIMD Python Environment'
        });

        if (selected) {
            if (selected.label.includes('Bundled')) {
                if (currentMode !== 'bundled') {
                    await config.update('pythonMode', 'bundled', vscode.ConfigurationTarget.Global);
                    this.promptRestart('Bundled Python');
                }
            } else {
                // User selected Custom/System mode
                const extension = vscode.extensions.getExtension('ms-python.python');
                if (!extension) {
                    const install = await vscode.window.showWarningMessage(
                        'The official Python extension is required for custom environments. Install it?',
                        'Install', 'Cancel'
                    );
                    if (install === 'Install') {
                        vscode.commands.executeCommand('workbench.extensions.installExtension', 'ms-python.python');
                    }
                    return;
                }

                // Activate selection immediately
                vscode.commands.executeCommand('python.setInterpreter');

                // Ensure we are in system mode
                if (currentMode !== 'system') {
                    await config.update('pythonMode', 'system', vscode.ConfigurationTarget.Global);

                    // We also want to validate dependencies immediately if we can guess the path, 
                    // but python.setInterpreter is async and UI blocking.
                    // The watcher will likely pick it up.

                    // Wait a moment for watcher to pick up or rely on user selecting.
                }
            }
        }
    }

    private async promptRestart(mode: string | undefined) {
        const message = mode
            ? `Switched to ${mode}. Restart backend to apply?`
            : 'Python environment changed. Restart backend to apply?';

        const action = await vscode.window.showInformationMessage(
            message,
            'Restart Now'
        );

        if (action === 'Restart Now') {
            vscode.commands.executeCommand('aimd.restartBackend');
        }
    }

    private async updateStatusBar() {
        const config = vscode.workspace.getConfiguration('aimd');
        const mode = config.get<string>('pythonMode');
        const systemPath = config.get<string>('systemPythonPath') || 'python3';

        if (mode === 'bundled') {
            this.statusBarItem.text = '$(package) AIMD: Bundled';
            this.statusBarItem.tooltip = 'Using bundled Python environment';
            this.statusBarItem.backgroundColor = undefined;
        } else {
            // Get version for display
            const versionString = await this.getPythonVersion(systemPath);
            // Display: "Python 3.9.6"
            this.statusBarItem.text = `$(terminal) AIMD: ${versionString || 'Python'}`;
            this.statusBarItem.tooltip = `Using system Python: ${systemPath}`;
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        }
        this.statusBarItem.show();
    }

    private async getPythonVersion(pythonPath: string): Promise<string | undefined> {
        try {
            const cmd = `"${pythonPath}" --version`;
            const result = cp.execSync(cmd).toString().trim();
            // result is like "Python 3.9.6"
            return result;
        } catch (e) {
            try {
                // Try python3 if python failed (sometimes path is just 'python')
                if (pythonPath === 'python') {
                    return cp.execSync('python3 --version').toString().trim();
                }
            } catch (ignored) { }
            return undefined;
        }
    }


    public async checkSystemPython(pythonPath: string): Promise<boolean> {
        try {
            // Check version >= 3.8
            const checkCmd = `${pythonPath} -c "import sys; print(sys.version_info >= (3, 8))"`;
            const result = cp.execSync(checkCmd).toString().trim();
            return result === 'True';
        } catch (e) {
            return false;
        }
    }
}
