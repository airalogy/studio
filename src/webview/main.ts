import { createApp } from 'vue';
import App from './App.vue';
import { registerCustomElements } from './custom-elements';
import './styles/theme.css';

// Initialize VS Code API
// This must be called only once
const vscode = (window as any).acquireVsCodeApi ? (window as any).acquireVsCodeApi() : null;
(window as any).vscode = vscode;

// Register Vue components as custom elements first
registerCustomElements();

// Mount the Vue application
const app = createApp(App);

// Mount to #app container (will be created in webview HTML)
const container = document.getElementById('app');
if (container) {
    app.mount(container);
} else {
    // Create container if not exists
    const div = document.createElement('div');
    div.id = 'app';
    document.body.appendChild(div);
    app.mount(div);
}
