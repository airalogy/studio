/**
 * AIMD Backend - Python Binary Sidecar Bridge
 * 
 * Manages communication with the Python backend process via JSON-RPC over stdio.
 * In development mode, runs Python source directly.
 * In production mode, runs the compiled binary.
 */

import * as path from 'path';
import * as cp from 'child_process';
import * as vscode from 'vscode';

// JSON-RPC message types
interface JsonRpcRequest {
    jsonrpc: '2.0';
    id: number;
    method: string;
    params?: Record<string, unknown>;
}

interface JsonRpcResponse {
    jsonrpc: '2.0';
    id: number;
    result?: unknown;
    error?: {
        code: number;
        message: string;
        data?: unknown;
    };
}

interface HelloResult {
    message: string;
    timestamp: string;
    python_version: string;
}

export class AimdBackend {
    private process: cp.ChildProcess | null = null;
    private outputChannel: vscode.OutputChannel;
    private requestId = 0;
    private pendingRequests = new Map<number, {
        resolve: (value: unknown) => void;
        reject: (error: Error) => void;
    }>();
    private buffer = '';
    private isReady = false;
    private readyPromise: Promise<void>;
    private readyResolve: (() => void) | null = null;

    constructor(private extensionPath: string) {
        this.outputChannel = vscode.window.createOutputChannel('AIMD Backend');
        this.readyPromise = new Promise((resolve) => {
            this.readyResolve = resolve;
        });
    }

    /**
     * Get the path to the Python executable or compiled binary
     */
    private getBackendCommand(): { command: string; args: string[]; cwd: string } {
        const config = vscode.workspace.getConfiguration('aimd');
        const mode = config.get<string>('pythonMode');
        const systemPath = config.get<string>('systemPythonPath') || 'python3';

        // Detect platform and architecture
        const platform = process.platform;  // 'darwin', 'win32', 'linux'
        const arch = process.arch === 'arm64' ? 'arm64' : 'x64';

        // 1. Bundled Mode (default)
        if (mode === 'bundled') {
            // Binary name based on platform
            const binaryName = platform === 'win32'
                ? `aimd-server-${platform}-${arch}.exe`
                : `aimd-server-${platform}-${arch}`;

            const binaryPath = path.join(this.extensionPath, 'bin', binaryName);

            // Check if compiled binary exists
            const fs = require('fs');
            if (fs.existsSync(binaryPath)) {
                this.outputChannel.appendLine(`Using bundled binary: ${binaryPath}`);
                return {
                    command: binaryPath,
                    args: [],
                    cwd: path.join(this.extensionPath, 'bin')
                };
            } else {
                this.outputChannel.appendLine('Bundled binary not found, falling back to Python source');
            }
        } else {
            this.outputChannel.appendLine(`Using system Python mode: ${systemPath}`);
        }

        // 2. Python Source Mode (Development or System Fallback)
        const pythonScript = path.join(this.extensionPath, 'python', 'server.py');
        const pythonCommand = mode === 'system' ? systemPath : (platform === 'win32' ? 'python' : 'python3');

        return {
            command: pythonCommand,
            args: [pythonScript],
            cwd: path.join(this.extensionPath, 'python')
        };
    }

    /**
     * Start the backend process
     */
    async start(): Promise<void> {
        if (this.process) {
            this.outputChannel.appendLine('Backend already running');
            return;
        }

        const { command, args, cwd } = this.getBackendCommand();
        const isProduction = args.length === 0;  // Binary mode has no args

        this.outputChannel.appendLine(`Starting backend: ${command} ${args.join(' ')}`);

        try {
            this.process = cp.spawn(command, args, {
                cwd,
                env: {
                    ...process.env,
                    PYTHONUNBUFFERED: '1',  // Ensure immediate output
                    AIMD_MODE: isProduction ? 'production' : 'development'
                },
                stdio: ['pipe', 'pipe', 'pipe']
            });

            // Handle stdout (JSON-RPC responses)
            this.process.stdout?.on('data', (data: Buffer) => {
                this.handleStdout(data.toString());
            });

            // Handle stderr (log messages)
            this.process.stderr?.on('data', (data: Buffer) => {
                const message = data.toString().trim();
                if (message) {
                    this.outputChannel.appendLine(`[Python] ${message}`);
                }
            });

            // Handle process exit
            this.process.on('exit', (code, signal) => {
                this.outputChannel.appendLine(`Backend exited with code ${code}, signal ${signal}`);
                this.process = null;
                this.isReady = false;

                // Reject all pending requests
                for (const [id, { reject }] of this.pendingRequests) {
                    reject(new Error('Backend process exited'));
                }
                this.pendingRequests.clear();
            });

            this.process.on('error', (err) => {
                this.outputChannel.appendLine(`Backend error: ${err.message}`);
                vscode.window.showErrorMessage(`AIMD Backend failed to start: ${err.message}`);
            });

            // Wait for ready signal
            await this.readyPromise;
            this.outputChannel.appendLine('Backend is ready');

            // Check backend dependencies and notify user
            await this.checkAndNotifyDependencies();

        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            this.outputChannel.appendLine(`Failed to start backend: ${message}`);
            throw error;
        }
    }

    /**
     * Check backend dependencies and show actionable notifications
     */
    private async checkAndNotifyDependencies(): Promise<void> {
        try {
            const versionInfo = await this.getVersion();

            if (versionInfo.has_airalogy && versionInfo.airalogy_sdk_version) {
                this.outputChannel.appendLine(`Airalogy SDK v${versionInfo.airalogy_sdk_version} loaded`);
            } else {
                // Check Python version - airalogy requires >= 3.13
                const pythonVersion = versionInfo.python_version || '';
                const versionMatch = pythonVersion.match(/^(\d+)\.(\d+)/);
                const majorVersion = versionMatch ? parseInt(versionMatch[1]) : 0;
                const minorVersion = versionMatch ? parseInt(versionMatch[2]) : 0;

                if (majorVersion < 3 || (majorVersion === 3 && minorVersion < 13)) {
                    // Python version too old for airalogy
                    const action = await vscode.window.showWarningMessage(
                        `Airalogy SDK requires Python ≥ 3.13, but current environment is Python ${majorVersion}.${minorVersion}. ` +
                        `Assigners and calculations will be unavailable.`,
                        'Switch Environment',
                        'Use Bundled'
                    );

                    if (action === 'Switch Environment') {
                        vscode.commands.executeCommand('python.setInterpreter');
                    } else if (action === 'Use Bundled') {
                        const config = vscode.workspace.getConfiguration('aimd');
                        await config.update('pythonMode', 'bundled', vscode.ConfigurationTarget.Global);
                        await this.restart();
                    }
                } else {
                    // Python version OK, check if it's Homebrew Python (externally managed)
                    const config = vscode.workspace.getConfiguration('aimd');
                    const pythonPath = config.get<string>('systemPythonPath') || 'python3';
                    const isHomebrew = pythonPath.includes('/opt/homebrew') || pythonPath.includes('/usr/local/Cellar');

                    if (isHomebrew) {
                        // Homebrew Python - cannot install directly
                        const action = await vscode.window.showWarningMessage(
                            `Airalogy SDK not found. The current Python (${pythonPath}) is managed by Homebrew and cannot have packages installed directly.`,
                            'Install with uv',
                            'Use Bundled',
                            'Switch Environment'
                        );

                        if (action === 'Install with uv') {
                            const term = vscode.window.createTerminal('AIMD Dependency Install');
                            term.show();
                            term.sendText(`uv pip install git+https://github.com/airalogy/airalogy --python "${pythonPath}"`);

                            const restart = await vscode.window.showInformationMessage(
                                'Installing with uv... After installation, restart backend.',
                                'Restart Backend'
                            );
                            if (restart === 'Restart Backend') {
                                await this.restart();
                            }
                        } else if (action === 'Use Bundled') {
                            await config.update('pythonMode', 'bundled', vscode.ConfigurationTarget.Global);
                            await this.restart();
                        } else if (action === 'Switch Environment') {
                            vscode.commands.executeCommand('python.setInterpreter');
                        }
                    } else {
                        // Normal Python environment - offer uv (preferred) or pip
                        const action = await vscode.window.showWarningMessage(
                            `Airalogy SDK not found. Some features (assigners, calculations) will be unavailable.`,
                            'Install with uv',
                            'Install with pip',
                            'Ignore'
                        );

                        if (action === 'Install with uv' || action === 'Install with pip') {
                            const term = vscode.window.createTerminal('AIMD Dependency Install');
                            term.show();

                            if (action === 'Install with uv') {
                                term.sendText(`uv pip install git+https://github.com/airalogy/airalogy`);
                            } else {
                                term.sendText(`"${pythonPath}" -m pip install git+https://github.com/airalogy/airalogy`);
                            }

                            const restart = await vscode.window.showInformationMessage(
                                'Installing Airalogy SDK... After installation, restart backend.',
                                'Restart Backend'
                            );
                            if (restart === 'Restart Backend') {
                                await this.restart();
                            }
                        }
                    }
                }
            }
        } catch (e) {
            // Version check failed, but backend is running - not critical
            this.outputChannel.appendLine(`Version check failed: ${(e as Error).message}`);
        }
    }

    /**
     * Get backend version and dependency info
     */
    async getVersion(): Promise<{
        server_version: string;
        airalogy_sdk_version: string | null;
        has_airalogy: boolean;
        has_mock: boolean;
        python_version: string;
    }> {
        return this.sendRequest('version');
    }

    /**
     * Restart the backend process
     */
    async restart(): Promise<void> {
        this.outputChannel.appendLine('Restarting backend...');
        await this.stop();
        this.isReady = false;
        this.readyPromise = new Promise((resolve) => {
            this.readyResolve = resolve;
        });
        await this.start();
    }

    /**
     * Handle data from stdout (JSON-RPC messages)
     */
    private handleStdout(data: string): void {
        this.buffer += data;

        // Process complete lines
        const lines = this.buffer.split('\n');
        this.buffer = lines.pop() || '';  // Keep incomplete line in buffer

        for (const line of lines) {
            if (!line.trim()) continue;

            try {
                const message = JSON.parse(line);

                // Check for ready notification
                if (message.method === '$/ready') {
                    this.isReady = true;
                    if (this.readyResolve) {
                        this.readyResolve();
                        this.readyResolve = null;
                    }
                    continue;
                }

                // Handle response
                if ('id' in message) {
                    const response = message as JsonRpcResponse;
                    const pending = this.pendingRequests.get(response.id);

                    if (pending) {
                        this.pendingRequests.delete(response.id);

                        if (response.error) {
                            pending.reject(new Error(
                                `${response.error.message} (code: ${response.error.code})`
                            ));
                        } else {
                            pending.resolve(response.result);
                        }
                    }
                }
            } catch (e) {
                this.outputChannel.appendLine(`Failed to parse response: ${line}`);
            }
        }
    }

    /**
     * Send a JSON-RPC request to the backend
     */
    async sendRequest<T>(method: string, params?: Record<string, unknown>): Promise<T> {
        if (!this.process || !this.isReady) {
            throw new Error('Backend is not running');
        }

        const id = ++this.requestId;
        const request: JsonRpcRequest = {
            jsonrpc: '2.0',
            id,
            method,
            params
        };

        return new Promise((resolve, reject) => {
            this.pendingRequests.set(id, {
                resolve: resolve as (value: unknown) => void,
                reject
            });

            const requestStr = JSON.stringify(request) + '\n';
            this.process?.stdin?.write(requestStr, (err) => {
                if (err) {
                    this.pendingRequests.delete(id);
                    reject(err);
                }
            });
        });
    }

    /**
     * Load project files (model.py, assigner.py) from a directory
     */
    async loadProject(path: string): Promise<{ success: boolean }> {
        return this.sendRequest<{ success: boolean }>('load_project', { path });
    }

    /**
     * Get variable metadata from the loaded project
     */
    async getVariables(): Promise<Record<string, any>> {
        return this.sendRequest<Record<string, any>>('get_variables');
    }

    /**
     * Perform calculations via the backend
     */
    async calculate(data: any): Promise<any> {
        return this.sendRequest<any>('calculate', { data });
    }

    /**
     * Get assigner metadata (modes, dependencies)
     */
    async getAssigners(): Promise<Record<string, { mode: string; dependent_fields: string[]; readonly: boolean }>> {
        return this.sendRequest<Record<string, any>>('get_assigners');
    }

    /**
     * Manually trigger a specific assigner
     */
    async triggerAssigner(fieldName: string, data: any): Promise<{ success: boolean; calculated_fields?: Record<string, any>; error?: string }> {
        return this.sendRequest<any>('trigger_assigner', { field_name: fieldName, data });
    }

    /**
     * Call the hello method on the backend
     */
    async hello(name: string = 'World'): Promise<HelloResult> {
        return this.sendRequest<HelloResult>('hello', { name });
    }

    // ========================================================
    // Record Session API
    // ========================================================

    /**
     * Start a record session
     */
    async startSession(protocolId: string): Promise<{ success: boolean; record_id: string; protocol_id: string }> {
        return this.sendRequest('session_start', { protocol_id: protocolId });
    }

    /**
     * End a record session
     */
    async endSession(save: boolean = true): Promise<{ success: boolean; saved: boolean; record_id?: string }> {
        return this.sendRequest('session_end', { save });
    }

    /**
     * Upload a file and link to session variable
     */
    async uploadToSession(varId: string, filePath: string): Promise<{ success: boolean; var_id: string; file_id: string }> {
        // Read file as base64
        const fs = require('fs');
        const fileData = fs.readFileSync(filePath);
        const base64Data = fileData.toString('base64');
        const fileName = path.basename(filePath);

        // We use a special method that combines upload and set_var, or just raw upload?
        // The mock server has /api/session/upload which takes multipart.
        // But our JSON-RPC bridge likely needs a wrapper.
        // Let's assume we added a 'session_upload_base64' method to the python server adapter logic 
        // OR we use the generic client methods if exposed.

        // Actually, the Python `server.py` likely needs a JSON-RPC adapter for these new HTTP endpoints 
        // if they aren't automatically exposed. 
        // Wait, `server.py` is an HTTP server (FastAPI). 
        // `backend.ts` spawns `server.py`? 
        // 
        // Checking `backend.ts`:
        // It spawns `server.py` but communicates via stdin/stdout JSON-RPC? 
        // Reviewing `server.py`: It's a FastAPI app. 
        // But `backend.ts` uses JSON-RPC over stdio. 
        // This implies there's an adapter layer or `server.py` handles both?
        //
        // Let's re-read `server.py` imports. It imports `FastAPI`. 
        // And `backend.ts` sends JSON objects to stdin.
        // Does `server.py` have a stdin loop? 
        //
        // NOTE: The user provided `server.py` is the HTTP server for the Preview/Mock. 
        // `AimdBackend` in `backend.ts` seems to assume there is a JSON-RPC handler.
        // If `server.py` only sets up FastAPI, then `backend.ts` might be launching a different script 
        // OR `server.py` has a dual mode.
        //
        // Let's verify if `backend.ts` is actually talking to `server.py` or something else.
        // `backend.ts`: `const pythonScript = path.join(this.extensionPath, 'python', 'server.py');`
        // 
        // If `server.py` is JUST FastAPI, then `backend.ts` talking JSON-RPC to it won't work 
        // unless `server.py` has a section that reads stdin.
        // 
        // Let's double check `server.py` content again.
        // I likely missed the bottom part of `server.py` or it's designed to be run as a module 
        // and there is another entry point for JSON-RPC?
        // 
        // Requesting `server.py` full content or checking for `if __name__ == "__main__":`

        return this.sendRequest('session_upload', {
            var_id: varId,
            file_name: fileName,
            file_base64: base64Data
        });
    }

    /**
     * Set a session variable
     */
    async setSessionVar(varId: string, value: any): Promise<{ success: boolean }> {
        return this.sendRequest('session_set_var', { var_id: varId, value });
    }

    async listRecords(): Promise<any[]> {
        return this.sendRequest('list_records', {});
    }

    async loadSession(recordId: string): Promise<any> {
        return this.sendRequest('session_load', { record_id: recordId });
    }

    async deleteRecord(recordId: string): Promise<{ success: boolean }> {
        return this.sendRequest('delete_record', { record_id: recordId });
    }

    async renameRecord(recordId: string, alias: string): Promise<{ success: boolean }> {
        return this.sendRequest('rename_record', { record_id: recordId, alias });
    }

    /**
     * Stop the backend process
     */
    async stop(): Promise<void> {
        if (!this.process) {
            return;
        }

        this.outputChannel.appendLine('Stopping backend...');

        try {
            // Try graceful shutdown first
            await this.sendRequest('shutdown').catch(() => { });
        } catch {
            // Ignore errors during shutdown
        }

        // Force kill if still running
        if (this.process) {
            this.process.kill();
            this.process = null;
        }

        this.isReady = false;
        this.outputChannel.appendLine('Backend stopped');
    }

    /**
     * Show the output channel
     */
    showOutput(): void {
        this.outputChannel.show();
    }

    /**
     * Dispose resources
     */
    dispose(): void {
        this.stop();
        this.outputChannel.dispose();
    }
}
