import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { OpenResourceRequest, FileSelectRequest, FileUploadRequest, VariableUpdateRequest, RecordSearchRequest } from '../../shared/messagebus';

// ... updateModelVariable ...

/**
 * Handle record search request
 */
export async function handleRecordSearch(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    payload: RecordSearchRequest,
    backend: import('../backend/backend').AimdBackend | null = null
): Promise<void> {
    const { query, fieldName } = payload;
    const projectDir = path.dirname(originUri.fsPath);
    const modelPath = path.join(projectDir, 'model.py');

    const results: any[] = [];

    // 1. Search in historical records from backend
    if (backend) {
        try {
            const records = await backend.listRecords();
            records.forEach(r => {
                if (!query || r.id.toLowerCase().includes(query.toLowerCase())) {
                    results.push({
                        id: r.id,
                        title: r.id,
                        description: `Historical Record (${r.created_at || 'unknown date'})`
                    });
                }
            });
        } catch (e) {
            console.error('Backend record search failed:', e);
        }
    }

    // 2. Mock Search: Scan model.py (backward compatibility/definitions)
    try {
        if (fs.existsSync(modelPath)) {
            const text = fs.readFileSync(modelPath, 'utf8');
            const regex = /(\w+)\s*=\s*Record\s*\(/g;
            let match;
            while ((match = regex.exec(text)) !== null) {
                const id = match[1];
                // Check if already added from backend
                if (results.some(r => r.id === id)) continue;

                if (!query || id.toLowerCase().includes(query.toLowerCase())) {
                    results.push({
                        id: id,
                        title: id,
                        description: 'Record definition in model.py'
                    });
                }
            }
        }
    } catch (e) {
        console.error('Search in model.py failed:', e);
    }

    // Send response
    panel.webview.postMessage({
        type: 'record:search:result',
        payload: {
            fieldName,
            results
        }
    });
}

// ... updateModelVariable ...

/**
 * Handle generic variable update request
 */
export async function handleVariableUpdate(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    payload: VariableUpdateRequest
): Promise<void> {
    const { fieldName, value } = payload;
    const projectDir = path.dirname(originUri.fsPath);
    await updateModelVariable(projectDir, fieldName, value);
}

/**
 * Update a variable definition in model.py using Regex
 * Attempts to find: name = "old_val" or name = FileIdPNG("old_val") etc.
 */
async function updateModelVariable(projectDir: string, varName: string, newValue: string): Promise<boolean> {
    const modelPath = path.join(projectDir, 'model.py');

    // Tolerate missing model.py - some AIMD files are standalone
    if (!fs.existsSync(modelPath)) {
        console.log('[AIMD] model.py not found, skipping variable update');
        return false;
    }

    try {
        const document = await vscode.workspace.openTextDocument(modelPath);
        const text = document.getText();

        // Regex to find variable assignment
        // Supports: var = "val", var = 'val', var = Type("val")
        // We look for `varName = ...`
        const regex = new RegExp(`^(\\s*)${varName}(\\s*=\\s*)(?:[a-zA-Z0-9_]+\\()?(['"])([^'"]*)\\3(\\)?)`, 'm');

        const match = text.match(regex);
        if (match) {
            const currentLine = text.substring(match.index!, match.index! + match[0].length);
            // Reconstruct line with new value
            // Group 1: indent
            // Group 2: = 
            // Group 3: quote
            // Group 4: old value
            // Group 5: optional closing paren

            // We preserve everything except Group 4
            const newline = currentLine.replace(regex, `$1${varName}$2$3${newValue}$3$5`);

            const edit = new vscode.WorkspaceEdit();
            const range = new vscode.Range(
                document.positionAt(match.index!),
                document.positionAt(match.index! + match[0].length)
            );
            edit.replace(document.uri, range, newline);
            return await vscode.workspace.applyEdit(edit) && await document.save();
        }
        return false;
    } catch (e) {
        console.error('Failed to update model.py:', e);
        return false;
    }
}

/**
 * Handle request to select a file
 */
export async function handleFileSelect(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    payload: FileSelectRequest
): Promise<void> {
    const { fieldName, accept } = payload;

    // Convert accept string (e.g. "image/png, .csv") to filters
    const filters: Record<string, string[]> = { 'Files': ['*'] }; // Simplified
    // TODO: proper parsing of accept types if needed

    const uris = await vscode.window.showOpenDialog({
        canSelectMany: false,
        openLabel: 'Select',
        filters
    });

    if (uris && uris.length > 0) {
        const selectedUri = uris[0];
        const projectDir = path.dirname(originUri.fsPath);
        const assetsDir = path.join(projectDir, 'assets');

        // Create assets dir if not exists
        if (!fs.existsSync(assetsDir)) {
            fs.mkdirSync(assetsDir, { recursive: true });
        }

        const filename = path.basename(selectedUri.fsPath);
        const targetPath = path.join(assetsDir, filename);

        // Copy file
        await vscode.workspace.fs.copy(selectedUri, vscode.Uri.file(targetPath), { overwrite: true });

        // Update variable
        const relativePath = `assets/${filename}`;
        await updateModelVariable(projectDir, fieldName, relativePath);

        // Note: We don't need to send explicit response because 
        // updating model.py triggers watcher -> refresh webview
    }
}

/**
 * Handle request to upload a file (drag & drop)
 */
export async function handleFileUpload(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    payload: FileUploadRequest
): Promise<void> {
    const { fieldName, sourceUri } = payload;

    if (!sourceUri) return;

    try {
        const projectDir = path.dirname(originUri.fsPath);
        const assetsDir = path.join(projectDir, 'assets');

        if (!fs.existsSync(assetsDir)) {
            fs.mkdirSync(assetsDir, { recursive: true });
        }

        let targetFilename = '';

        // Check if sourceUri is path or data uri
        if (sourceUri.startsWith('data:')) {
            // Write data uri to file
            // Need to guess extension
            const matches = sourceUri.match(/^data:([A-Za-z-+\/]+);base64,(.+)$/);
            if (matches && matches.length === 3) {
                const type = matches[1];
                const buffer = Buffer.from(matches[2], 'base64');
                const ext = type.split('/')[1] || 'bin';
                targetFilename = `${fieldName}_${Date.now()}.${ext}`;
                const targetPath = path.join(assetsDir, targetFilename);
                fs.writeFileSync(targetPath, buffer);
            }
        } else {
            // Copy from path
            // sourceUri might be a file path string
            const filename = path.basename(sourceUri);
            const targetPath = path.join(assetsDir, filename);
            // Copy
            fs.copyFileSync(sourceUri, targetPath);
            targetFilename = filename;
        }

        if (targetFilename) {
            const relativePath = `assets/${targetFilename}`;
            await updateModelVariable(projectDir, fieldName, relativePath);
        }

    } catch (e) {
        vscode.window.showErrorMessage(`Upload failed: ${(e as Error).message}`);
    }
}

/**
 * Handle request to open a resource in the native editor
 */
export async function handleOpenResource(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    payload: OpenResourceRequest
): Promise<void> {
    const { resourceId, contentType, content, language, filePath, viewColumn } = payload;

    try {
        if (filePath) {
            // Case 1: Open existing physical file
            const uri = vscode.Uri.file(filePath);
            const doc = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(doc, {
                viewColumn: viewColumn || vscode.ViewColumn.One,
                preview: false
            });
        } else if (content !== undefined) {
            // Case 2: Open virtual content in airalogy-fs
            const ext = language === 'python' ? 'py' :
                language === 'javascript' ? 'js' :
                    language === 'typescript' ? 'ts' :
                        contentType === 'markdown' ? 'md' : 'txt';

            const filename = `${resourceId}.${ext}`;
            const virtualUri = vscode.Uri.from({
                scheme: 'airalogy-fs',
                path: `/${filename}`
            });

            // Write content to virtual file system
            const encoder = new TextEncoder();
            await vscode.workspace.fs.writeFile(virtualUri, encoder.encode(content));

            // Open document
            const doc = await vscode.workspace.openTextDocument(virtualUri);
            await vscode.window.showTextDocument(doc, {
                viewColumn: viewColumn || vscode.ViewColumn.One,
                preview: false
            });
        }
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to open resource: ${(error as Error).message}`);
    }
}

// ... Session Handlers ...

/**
 * Handle session start
 */
export async function handleSessionStart(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    payload: { protocolId: string },
    backend: import('../backend/backend').AimdBackend | null
): Promise<void> {
    if (!backend) {
        vscode.window.showErrorMessage("Backend not available for Record Mode");
        return;
    }

    try {
        const result = await backend.startSession(payload.protocolId);
        panel.webview.postMessage({
            type: 'session:started',
            payload: result
        });
    } catch (e) {
        const errMsg = (e as Error).message || String(e);
        let userMessage = `Record Mode Error: ${errMsg}`;

        // Provide actionable hints based on error type
        if (errMsg.includes('Mock client not available') || errMsg.includes('Method not found')) {
            userMessage = `Record Mode unavailable: The Python backend's mock client failed to initialize. ` +
                `This may happen if your System Python is missing the 'airalogy' package. ` +
                `Try: pip install git+https://github.com/airalogy/airalogy`;
        }

        vscode.window.showErrorMessage(userMessage);
        panel.webview.postMessage({ type: 'session:error', error: errMsg });
    }
}

/**
 * Handle session end
 */
export async function handleSessionEnd(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    payload: { save: boolean },
    backend: import('../backend/backend').AimdBackend | null
): Promise<void> {
    if (!backend) return;

    try {
        const result = await backend.endSession(payload.save);
        panel.webview.postMessage({
            type: 'session:ended',
            payload: result
        });
    } catch (e) {
        vscode.window.showErrorMessage(`Failed to end session: ${(e as Error).message}`);
    }
}

/**
 * Handle session file upload
 */
export async function handleSessionUpload(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    payload: { varId: string; filePath?: string },
    backend: import('../backend/backend').AimdBackend | null
): Promise<void> {
    if (!backend) return;

    let filePath = payload.filePath;

    try {
        // If no filePath provided (e.g. from button click), open dialog
        if (!filePath) {
            const uris = await vscode.window.showOpenDialog({
                canSelectMany: false,
                openLabel: 'Upload to Session',
                filters: { 'Files': ['*'] }
            });

            if (uris && uris.length > 0) {
                filePath = uris[0].fsPath;
            } else {
                return; // User cancelled
            }
        }

        if (!filePath) return;

        const result = await backend.uploadToSession(payload.varId, filePath);

        // Read file for preview (as base64 data URL)
        let previewDataUrl = '';
        const ext = path.extname(filePath).toLowerCase();
        const mimeMap: Record<string, string> = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
        };
        const mimeType = mimeMap[ext];
        if (mimeType) {
            try {
                const fileData = fs.readFileSync(filePath);
                const base64 = fileData.toString('base64');
                previewDataUrl = `data:${mimeType};base64,${base64}`;
            } catch (e) {
                console.error('Failed to read file for preview:', e);
            }
        }

        // Notify UI of update
        panel.webview.postMessage({
            type: 'session:var-updated',
            payload: {
                varId: payload.varId,
                value: result.file_id,
                fileInfo: result,
                previewUrl: previewDataUrl
            }
        });

    } catch (e) {
        vscode.window.showErrorMessage(`Session upload failed: ${(e as Error).message}`);
    }
}

/**
 * Handle session variable update
 */
export async function handleSessionSetVar(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    payload: { varId: string; value: any },
    backend: import('../backend/backend').AimdBackend | null
): Promise<void> {
    if (!backend) return;

    try {
        await backend.setSessionVar(payload.varId, payload.value);
        // Echo back to webview so App.vue can store in sessionValues Map
        panel.webview.postMessage({
            type: 'session:var-updated',
            payload: {
                varId: payload.varId,
                value: payload.value
            }
        });
    } catch (e) {
        console.error('Failed to set session var:', e);
    }
}

/**
 * Handle session list records
 */
export async function handleSessionListRecords(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    backend: import('../backend/backend').AimdBackend | null
): Promise<void> {
    if (!backend) return;

    try {
        const records = await backend.listRecords();

        const items = records.map(r => ({
            label: r.alias || r.id,
            description: r.alias ? `(${r.id})` : (r.created_at || 'No date'),
            detail: `Protocol: ${r.protocol_id} (v${r.version})`,
            recordId: r.id,
            buttons: [
                { iconPath: new vscode.ThemeIcon('edit'), tooltip: 'Rename' },
                { iconPath: new vscode.ThemeIcon('trash'), tooltip: 'Delete' }
            ]
        }));

        const quickPick = vscode.window.createQuickPick();
        quickPick.items = items;
        quickPick.placeholder = 'Select a record to load, or use buttons to rename/delete';

        quickPick.onDidTriggerItemButton(async (e) => {
            const item = e.item as any;
            const tooltip = (e.button as any).tooltip;

            if (tooltip === 'Delete') {
                const confirm = await vscode.window.showWarningMessage(
                    `Delete record "${item.label}"?`,
                    { modal: true },
                    'Delete'
                );
                if (confirm === 'Delete') {
                    await backend.deleteRecord(item.recordId);
                    vscode.window.showInformationMessage('Record deleted');
                    quickPick.hide();
                    // Refresh list
                    handleSessionListRecords(panel, originUri, backend);
                }
            } else if (tooltip === 'Rename') {
                const newAlias = await vscode.window.showInputBox({
                    prompt: 'Enter new alias for this record',
                    value: item.label
                });
                if (newAlias !== undefined) {
                    await backend.renameRecord(item.recordId, newAlias);
                    vscode.window.showInformationMessage('Record renamed');
                    quickPick.hide();
                    // Refresh list
                    handleSessionListRecords(panel, originUri, backend);
                }
            }
        });

        quickPick.onDidAccept(() => {
            const selected = quickPick.selectedItems[0] as any;
            if (selected) {
                quickPick.hide();
                handleSessionLoadRecord(panel, originUri, { recordId: selected.recordId }, backend);
            }
        });

        quickPick.show();
    } catch (e: any) {
        panel.webview.postMessage({
            type: 'session:error',
            error: e.message
        });
    }
}

/**
 * Handle session load record
 */
export async function handleSessionLoadRecord(
    panel: vscode.WebviewPanel,
    originUri: vscode.Uri,
    payload: { recordId: string },
    backend: import('../backend/backend').AimdBackend | null
): Promise<void> {
    if (!backend) return;

    try {
        const result = await backend.loadSession(payload.recordId);
        if (result.success) {
            panel.webview.postMessage({
                type: 'session:started',
                payload: {
                    record_id: result.record_id,
                    protocol_id: result.protocol_id,
                    data: result.data
                }
            });
        }
    } catch (e: any) {
        panel.webview.postMessage({
            type: 'session:error',
            error: e.message
        });
    }
}

