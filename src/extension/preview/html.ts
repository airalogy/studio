import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { getNonce } from '../../shared/utils';

/**
 * Generate HTML for Vue-based Webview
 * 
 * This loads the Vite-built Vue bundle into the webview.
 */
export function getVueWebviewHtml(
    webview: vscode.Webview,
    extensionUri: vscode.Uri
): string {
    const nonce = getNonce();

    // Get URIs for webview resources
    const webviewDistPath = vscode.Uri.joinPath(extensionUri, 'out', 'webview');

    const scriptUri = webview.asWebviewUri(
        vscode.Uri.joinPath(webviewDistPath, 'webview.js')
    );

    const styleUri = webview.asWebviewUri(
        vscode.Uri.joinPath(webviewDistPath, 'webview.css')
    );

    // Read any inline styles we still need (fonts, etc.)
    const fontsLink = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap';

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="
        default-src 'none';
        connect-src ${webview.cspSource} https: http: data: ws: wss:;
        img-src ${webview.cspSource} https: data:;
        style-src ${webview.cspSource} 'unsafe-inline' https://fonts.googleapis.com;
        font-src https://fonts.gstatic.com;
        script-src 'nonce-${nonce}';
    ">
    <title>AIMD Preview</title>
    <link href="${fontsLink}" rel="stylesheet">
    <link href="${styleUri}" rel="stylesheet">
    <style>
        /* Base styles for VS Code integration */
        :root {
            --aimd-bg: var(--vscode-editor-background);
            --aimd-text: var(--vscode-editor-foreground);
            --aimd-border: var(--vscode-panel-border);
            --aimd-primary: var(--vscode-textLink-foreground);
            
            /* Legacy Palette for Table/UI Components */
            --aimd-bg-primary: var(--vscode-editor-background);
            --aimd-bg-secondary: var(--vscode-sideBar-background);
            --aimd-bg-tertiary: var(--vscode-editorGroupHeader-tabsBackground);
            --aimd-border-light: var(--vscode-panel-border);
            --aimd-border-subtle: var(--vscode-input-border);
            
            --aimd-text-primary: var(--vscode-editor-foreground);
            --aimd-text-secondary: var(--vscode-descriptionForeground);
            --aimd-text-tertiary: var(--vscode-disabledForeground);

            --aimd-slate-50: #f8fafc;
            --aimd-slate-100: #f1f5f9;
            --aimd-slate-200: #e2e8f0;
            --aimd-slate-400: #94a3b8;
            --aimd-teal-50: #f0fdfa;
            --aimd-teal-600: #0d9488;
            --aimd-teal-700: #0f766e;
            
            /* AIMD Green Palette */
            --aimd-green-50: #f0fdf4;
            --aimd-green-100: #dcfce7;
            --aimd-green-200: #bbf7d0;
            --aimd-green-300: #86efac;
            --aimd-green-400: #4ade80;
            --aimd-green-500: #22c55e;
            --aimd-green-600: #16a34a;
            --aimd-green-700: #15803d;
            --aimd-green-800: #166534;
            --aimd-green-900: #14532d;
        }
        
        body {
            margin: 0;
            padding: 0;
            background-color: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
        }
        
        #app {
            min-height: 100vh;
        }

        /* Text Card Spacing - for content outside steps */
        .aimd-text-card {
            margin-bottom: 24px;
            padding: 4px 8px;
        }
        
        .aimd-text-card.preamble {
            margin-bottom: 24px;
        }

        /* Ensure smooth flow between broken steps */
        step-card + .aimd-text-card {
            margin-top: 12px;
        }

        .aimd-text-card + step-card {
            margin-top: 12px;
        }
    </style>
</head>
<body class="vscode-body">
    <div id="app"></div>
    <!-- Polyfill for Node.js process object used by Vue in development mode -->
    <script nonce="${nonce}">
        window.process = { env: { NODE_ENV: 'production' } };
    </script>
    <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
}
