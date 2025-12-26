import * as vscode from 'vscode';
import * as path from 'path';
import { getVueWebviewHtml } from './html';
import { escapeHtml } from '../../shared/utils';

/**
 * Vue-based Preview Provider
 * 
 * This provider uses a Vue 3 application for rendering the preview.
 * It communicates with the Vue app via postMessage.
 */
export class VuePreviewProvider {
    private static readonly viewType = 'aimd.preview.vue';
    private static readonly previewTitle = 'AIMD Preview';

    private static previewPanels = new Map<string, vscode.WebviewPanel>();
    private static updateTimeouts = new Map<string, NodeJS.Timeout>();
    private static scrollDebounceTimeouts = new Map<string, NodeJS.Timeout>();
    private static extensionUri: vscode.Uri;
    private static backend: import('../backend/backend').AimdBackend | null = null;

    /**
     * Initialize the provider with extension context and backend
     */
    public static initialize(context: vscode.ExtensionContext, backend?: import('../backend/backend').AimdBackend): void {
        this.extensionUri = context.extensionUri;
        if (backend) {
            this.backend = backend;
        }
    }

    /**
     * Create or show preview panel
     */
    public static createOrShow(
        uri: vscode.Uri,
        viewColumn: vscode.ViewColumn = vscode.ViewColumn.Beside
    ): void {
        if (!this.extensionUri) {
            vscode.window.showErrorMessage('VuePreviewProvider not initialized');
            return;
        }

        const resourcePath = uri.toString();

        // If panel exists, reveal it
        let panel = this.previewPanels.get(resourcePath);
        if (panel) {
            panel.reveal(viewColumn);
            return;
        }

        // Get the document's directory for loading local resources (images, etc.)
        const documentDir = vscode.Uri.file(path.dirname(uri.fsPath));

        // Create new panel
        panel = vscode.window.createWebviewPanel(
            this.viewType,
            `${this.previewTitle}: ${uri.fsPath.split('/').pop() || uri.fsPath.split('\\').pop()}`,
            viewColumn,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(this.extensionUri, 'out', 'webview'),
                    documentDir  // Allow loading local images from document directory
                ]
            }
        );

        // Set initial HTML (Vue app shell)
        panel.webview.html = getVueWebviewHtml(panel.webview, this.extensionUri);

        // Handle messages from webview
        panel.webview.onDidReceiveMessage(
            message => this.handleWebviewMessage(panel!, uri, message),
            undefined
        );

        // Handle panel disposal
        panel.onDidDispose(() => {
            this.previewPanels.delete(resourcePath);
            const timeout = this.updateTimeouts.get(resourcePath);
            if (timeout) {
                clearTimeout(timeout);
                this.updateTimeouts.delete(resourcePath);
            }
        }, null);

        // Store panel reference
        this.previewPanels.set(resourcePath, panel);
    }

    /**
     * Handle messages from the Vue webview
     */
    private static handleWebviewMessage(
        panel: vscode.WebviewPanel,
        uri: vscode.Uri,
        message: any
    ): void {
        switch (message.type) {
            case 'ready':
                // Webview is ready, send initial content
                this.sendContent(panel, uri);
                break;
            case 'error':
                vscode.window.showErrorMessage(`Preview error: ${message.error}`);
                break;
            case 'trigger-assigner':
                // Handle manual assigner trigger from webview (with session data)
                this.handleTriggerAssigner(panel, uri, message.fieldName, message.sessionData);
                break;
            // Native Bridge Navigation
            case 'nav:open-resource':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleOpenResource } = require('./nativeBridge');
                handleOpenResource(panel, uri, message.payload);
                break;
            // File Operations
            case 'file:select':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleFileSelect } = require('./nativeBridge');
                handleFileSelect(panel, uri, message.payload);
                break;
            case 'file:upload':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleFileUpload } = require('./nativeBridge');
                handleFileUpload(panel, uri, message.payload);
                break;
            case 'variable:update':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleVariableUpdate } = require('./nativeBridge');
                handleVariableUpdate(panel, uri, message.payload);
                break;
            case 'record:search':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleRecordSearch } = require('./nativeBridge');
                handleRecordSearch(panel, uri, message.payload, this.backend);
                break;
            // Record Session
            case 'session:start':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleSessionStart } = require('./nativeBridge');
                handleSessionStart(panel, uri, message.payload, this.backend);
                break;
            case 'session:end':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleSessionEnd } = require('./nativeBridge');
                handleSessionEnd(panel, uri, message.payload, this.backend);
                break;
            case 'session:upload':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleSessionUpload } = require('./nativeBridge');
                handleSessionUpload(panel, uri, message.payload, this.backend);
                break;
            case 'session:set-var':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleSessionSetVar } = require('./nativeBridge');
                handleSessionSetVar(panel, uri, message.payload, this.backend);
                break;
            case 'session:list-records':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleSessionListRecords } = require('./nativeBridge');
                handleSessionListRecords(panel, uri, this.backend);
                break;
            case 'session:load':
                // eslint-disable-next-line @typescript-eslint/no-var-requires
                const { handleSessionLoadRecord } = require('./nativeBridge');
                handleSessionLoadRecord(panel, uri, message.payload, this.backend);
                break;
        }
    }

    /**
     * Handle manual assigner trigger from webview
     */
    private static async handleTriggerAssigner(
        panel: vscode.WebviewPanel,
        uri: vscode.Uri,
        fieldName: string,
        sessionData?: Record<string, any>
    ): Promise<void> {
        if (!this.backend || !fieldName) {
            console.log('[AIMD Debug] No backend or fieldName for trigger');
            return;
        }

        try {
            console.log('[AIMD Debug] Triggering assigner:', fieldName);
            console.log('[AIMD Debug] Session data received:', sessionData ? Object.keys(sessionData) : 'none');

            // Get current variable values (we need to pass data to the assigner)
            const projectDir = path.dirname(uri.fsPath);
            await this.backend.loadProject(projectDir);
            const variablesMetadata = await this.backend.getVariables();

            // Build initial data from default values
            const currentData: Record<string, any> = {};
            for (const [name, meta] of Object.entries(variablesMetadata)) {
                if (meta.default_value !== undefined) {
                    currentData[name] = meta.default_value;
                } else if (meta.default !== undefined) {
                    currentData[name] = meta.default;
                }
            }

            // CRITICAL: Merge session values (uploaded files, user inputs in Record Mode)
            if (sessionData) {
                Object.assign(currentData, sessionData);
                console.log('[AIMD Debug] Merged session data, currentData keys:', Object.keys(currentData));
            }

            // Get existing calculated values FIRST (to preserve other fields' calculations)
            const existingCalcResult = await this.backend.calculate(currentData);
            const existingCalcFields = existingCalcResult.calculated_fields || {};
            console.log('[AIMD Debug] Existing calculated fields:', Object.keys(existingCalcFields));

            // Merge existing calculated values into currentData for accurate dependency resolution
            Object.assign(currentData, existingCalcFields);

            // Trigger the specific assigner with up-to-date data
            const result = await this.backend.triggerAssigner(fieldName, currentData);

            if (result.success) {
                console.log('[AIMD Debug] Assigner triggered successfully:', result.calculated_fields);
                // Merge: preserve existing calculated + override with newly triggered fields
                const mergedFields = { ...existingCalcFields, ...result.calculated_fields };
                // Refresh the preview to show new values, passing the merged calculated fields
                this.sendContent(panel, uri, mergedFields);
            } else {
                console.error('[AIMD Debug] Assigner trigger failed:', result.error);
                await this.handleAssignerError(result.error || 'Unknown error');
            }
        } catch (error) {
            console.error('[AIMD Debug] Error triggering assigner:', error);
            vscode.window.showErrorMessage(`Error: ${(error as Error).message}`);
        }
    }

    /**
     * Handle assigner errors with smart dependency detection
     */
    private static async handleAssignerError(errorMsg: string): Promise<void> {
        // Check for missing optional dependency patterns
        const pipInstallMatch = errorMsg.match(/pip install ["\']?([^"'\s]+)["\']?/i);
        const uvInstallMatch = errorMsg.match(/uv (?:add|pip install) ["\']?([^"'\s]+)["\']?/i);

        const packageToInstall = uvInstallMatch?.[1] || pipInstallMatch?.[1];

        if (packageToInstall) {
            // Extract a friendly package name for the message
            const friendlyName = packageToInstall.replace(/^airalogy\[/, '').replace(/\]$/, '');

            const action = await vscode.window.showWarningMessage(
                `Missing dependency: ${friendlyName}. Install it to use this feature.`,
                'Install with uv',
                'Install with pip',
                'Cancel'
            );

            if (action === 'Install with uv' || action === 'Install with pip') {
                const config = vscode.workspace.getConfiguration('aimd');
                const pythonPath = config.get<string>('systemPythonPath') || 'python3';

                const term = vscode.window.createTerminal('AIMD Dependency Install');
                term.show();

                if (action === 'Install with uv') {
                    term.sendText(`uv pip install "${packageToInstall}"`);
                } else {
                    term.sendText(`"${pythonPath}" -m pip install "${packageToInstall}"`);
                }

                // Offer to retry after install
                const retry = await vscode.window.showInformationMessage(
                    `Installing ${friendlyName}... After installation, restart backend to load the new dependency.`,
                    'Restart Backend'
                );
                if (retry === 'Restart Backend') {
                    vscode.commands.executeCommand('aimd.restartBackend');
                }
            }
        } else {
            // No recognizable install pattern, show generic error
            vscode.window.showWarningMessage(`Assigner failed: ${errorMsg}`);
        }
    }

    /**
     * Send rendered content to webview
     */
    private static async sendContent(
        panel: vscode.WebviewPanel,
        uri: vscode.Uri,
        additionalCalculatedFields?: Record<string, any>
    ): Promise<void> {
        try {
            const document = await vscode.workspace.openTextDocument(uri);
            const content = document.getText();

            // Load project and get metadata from backend if available
            let variablesMetadata: Record<string, any> = {};
            let calculatedFields: Record<string, any> = {};
            let assignersMetadata: Record<string, any> = {};

            if (this.backend) {
                try {
                    const projectDir = vscode.Uri.file(require('path').dirname(uri.fsPath)).fsPath;
                    console.log('[AIMD Debug] Loading project:', projectDir);
                    await this.backend.loadProject(projectDir);

                    console.log('[AIMD Debug] Project loaded, getting variables...');
                    variablesMetadata = await this.backend.getVariables();
                    console.log('[AIMD Debug] Got variables:', Object.keys(variablesMetadata).length, 'fields');

                    // Get assigner metadata (modes, dependencies)
                    assignersMetadata = await this.backend.getAssigners();
                    console.log('[AIMD Debug] Got assigners:', Object.keys(assignersMetadata).length, 'assigners');

                    // Build initial data from default values for calculation
                    const initialData: Record<string, any> = {};
                    for (const [name, meta] of Object.entries(variablesMetadata)) {
                        if (meta.default_value !== undefined) {
                            initialData[name] = meta.default_value;
                        } else if (meta.default !== undefined) {
                            initialData[name] = meta.default;
                        }
                    }

                    // Run calculations with default values
                    if (Object.keys(initialData).length > 0) {
                        console.log('[AIMD Debug] Running calculations with', Object.keys(initialData).length, 'initial values');
                        const calcResult = await this.backend.calculate(initialData);
                        calculatedFields = calcResult.calculated_fields || {};
                        console.log('[AIMD Debug] Calculated fields:', Object.keys(calculatedFields));
                    }

                    // Merge additional fields from manual trigger (they take priority)
                    if (additionalCalculatedFields) {
                        Object.assign(calculatedFields, additionalCalculatedFields);
                        console.log('[AIMD Debug] Merged manual trigger fields:', Object.keys(additionalCalculatedFields));
                    }
                } catch (backendError) {
                    console.error('[AIMD Debug] Backend error:', backendError);
                }
            } else {
                console.log('[AIMD Debug] No backend available');
            }

            // Use MDX compiler for rendering
            const { compileAimdToHtml } = require('./compiler');
            const result = await compileAimdToHtml(content, variablesMetadata, calculatedFields, assignersMetadata);

            if (result.error) {
                throw new Error(result.error);
            }

            // Convert relative image paths to webview URIs
            const documentDir = path.dirname(uri.fsPath);
            const htmlWithImages = this.convertImagePaths(result.html, documentDir, panel.webview);

            panel.webview.postMessage({
                type: 'update',
                content: htmlWithImages
            });
        } catch (error) {
            panel.webview.postMessage({
                type: 'update',
                content: `<div style="color:red;padding:20px;">Error: ${escapeHtml((error as Error).message)}</div>`
            });
        }
    }

    /**
     * Convert relative image paths in HTML to webview URIs
     */
    private static convertImagePaths(
        html: string,
        documentDir: string,
        webview: vscode.Webview
    ): string {
        // Match img tags with src attribute containing relative paths
        // Also match markdown-style images that were converted to img tags
        return html.replace(
            /<img\s+([^>]*?)src=["']([^"']+)["']([^>]*?)>/gi,
            (match, before, src, after) => {
                // Skip if already an absolute URL or data URI
                if (src.startsWith('http://') ||
                    src.startsWith('https://') ||
                    src.startsWith('data:') ||
                    src.startsWith('vscode-webview-resource:')) {
                    return match;
                }

                // Convert relative path to absolute and then to webview URI
                const absolutePath = path.resolve(documentDir, src);
                const fileUri = vscode.Uri.file(absolutePath);
                const webviewUri = webview.asWebviewUri(fileUri);

                return `<img ${before}src="${webviewUri}"${after}>`;
            }
        );
    }

    /**
     * Register document watcher for auto-refresh
     */
    public static registerDocumentWatcher(): vscode.Disposable {
        const debounceDelay = 300;

        return vscode.workspace.onDidChangeTextDocument(e => {
            const uri = e.document.uri;
            const resourcePath = uri.toString();

            if (uri.scheme !== 'file' || !uri.fsPath.endsWith('.aimd')) {
                return;
            }

            const panel = this.previewPanels.get(resourcePath);
            if (!panel || !panel.visible) {
                return;
            }

            const existingTimeout = this.updateTimeouts.get(resourcePath);
            if (existingTimeout) {
                clearTimeout(existingTimeout);
            }

            const timeout = setTimeout(() => {
                this.sendContent(panel, uri);
                this.updateTimeouts.delete(resourcePath);
            }, debounceDelay);

            this.updateTimeouts.set(resourcePath, timeout);
        });
    }

    /**
     * Register save watcher
     */
    public static registerSaveWatcher(): vscode.Disposable {
        return vscode.workspace.onDidSaveTextDocument(document => {
            const uri = document.uri;
            const resourcePath = uri.toString();

            if (uri.scheme !== 'file' || !uri.fsPath.endsWith('.aimd')) {
                return;
            }

            const panel = this.previewPanels.get(resourcePath);
            if (panel) {
                const existingTimeout = this.updateTimeouts.get(resourcePath);
                if (existingTimeout) {
                    clearTimeout(existingTimeout);
                    this.updateTimeouts.delete(resourcePath);
                }
                this.sendContent(panel, uri);
            }
        });
    }

    // Throttle state for scroll watcher
    private static scrollThrottleActive = new Map<string, boolean>();

    /**
     * Register scroll watcher for sync scrolling from editor to preview
     * Uses throttle (not debounce) for smoother real-time sync
     */
    public static registerScrollWatcher(): vscode.Disposable {
        const THROTTLE_MS = 50; // Send at most every 50ms for smooth scrolling

        return vscode.window.onDidChangeTextEditorVisibleRanges(e => {
            const uri = e.textEditor.document.uri;

            // Only handle .aimd files
            if (uri.scheme !== 'file' || !uri.fsPath.endsWith('.aimd')) {
                return;
            }

            const resourcePath = uri.toString();
            const panel = this.previewPanels.get(resourcePath);

            // Only sync if panel exists and is visible
            if (!panel || !panel.visible) {
                return;
            }

            // Throttle: skip if we're still in cooldown
            if (this.scrollThrottleActive.get(resourcePath)) {
                return;
            }

            // Get the first visible line
            const visibleRanges = e.visibleRanges;
            if (visibleRanges.length === 0) return;

            const startLine = visibleRanges[0].start.line;

            // Send line number to webview (element-based mapping)
            panel.webview.postMessage({
                type: 'scroll',
                line: startLine
            });

            // Set throttle cooldown
            this.scrollThrottleActive.set(resourcePath, true);
            setTimeout(() => {
                this.scrollThrottleActive.set(resourcePath, false);
            }, THROTTLE_MS);
        });
    }

    /**
     * Register watcher for Python files (model.py, assigner.py)
     * When these files change, refresh all preview panels
     */
    public static registerPythonFileWatcher(): vscode.Disposable {
        // Create a file system watcher for Python files
        const modelWatcher = vscode.workspace.createFileSystemWatcher('**/model.py');
        const assignerWatcher = vscode.workspace.createFileSystemWatcher('**/assigner.py');

        const refreshOnChange = () => {
            console.log('[AIMD Debug] Python file changed, refreshing all previews...');
            this.refreshAll();
        };

        // Watch for changes (edit) and save
        const disposables = [
            modelWatcher.onDidChange(refreshOnChange),
            modelWatcher.onDidCreate(refreshOnChange),
            modelWatcher.onDidDelete(refreshOnChange),
            assignerWatcher.onDidChange(refreshOnChange),
            assignerWatcher.onDidCreate(refreshOnChange),
            assignerWatcher.onDidDelete(refreshOnChange),
            modelWatcher,
            assignerWatcher
        ];

        return {
            dispose: () => {
                disposables.forEach(d => d.dispose());
            }
        };
    }

    /**
     * Refresh all panels
     */
    public static refreshAll(): void {
        for (const [resourcePath, panel] of this.previewPanels.entries()) {
            const uri = vscode.Uri.parse(resourcePath);
            this.sendContent(panel, uri);
        }
    }

    /**
     * Dispose all panels
     */
    public static disposeAll(): void {
        for (const panel of this.previewPanels.values()) {
            panel.dispose();
        }
        this.previewPanels.clear();
        this.updateTimeouts.clear();
        this.scrollDebounceTimeouts.clear();
    }
}
