import * as vscode from 'vscode';
import { TextEncoder, TextDecoder } from 'util';

export class MemFS implements vscode.FileSystemProvider {
    private _emitter = new vscode.EventEmitter<vscode.FileChangeEvent[]>();
    readonly onDidChangeFile: vscode.Event<vscode.FileChangeEvent[]> = this._emitter.event;

    private _files = new Map<string, Uint8Array>();

    watch(uri: vscode.Uri): vscode.Disposable {
        // ignore, fires for all changes...
        return new vscode.Disposable(() => { });
    }

    stat(uri: vscode.Uri): vscode.FileStat {
        const path = uri.path;
        if (this._files.has(path)) {
            const content = this._files.get(path)!;
            return {
                type: vscode.FileType.File,
                ctime: Date.now(),
                mtime: Date.now(),
                size: content.length
            };
        }
        if (path === '/') {
            return {
                type: vscode.FileType.Directory,
                ctime: Date.now(),
                mtime: Date.now(),
                size: 0
            };
        }
        throw vscode.FileSystemError.FileNotFound();
    }

    readDirectory(uri: vscode.Uri): [string, vscode.FileType][] {
        return [];
    }

    createDirectory(uri: vscode.Uri): void {
        // In-memory provider doesn't strictly track directories for this simple use case
        // But we must implement the method to satisfy the interface.
    }

    readFile(uri: vscode.Uri): Uint8Array {
        const content = this._files.get(uri.path);
        if (content) {
            return content;
        }
        throw vscode.FileSystemError.FileNotFound();
    }

    writeFile(uri: vscode.Uri, content: Uint8Array, options: { create: boolean, overwrite: boolean }): void {
        const path = uri.path;
        const exists = this._files.has(path);
        if (!exists && !options.create) {
            throw vscode.FileSystemError.FileNotFound();
        }
        if (exists && !options.overwrite) {
            throw vscode.FileSystemError.FileExists();
        }

        this._files.set(path, content);
        this._emitter.fire([{ type: vscode.FileChangeType.Changed, uri }]);
    }

    delete(uri: vscode.Uri, options: { recursive: boolean }): void {
        const path = uri.path;
        if (!this._files.has(path)) {
            throw vscode.FileSystemError.FileNotFound();
        }
        this._files.delete(path);
        this._emitter.fire([{ type: vscode.FileChangeType.Deleted, uri }]);
    }

    rename(oldUri: vscode.Uri, newUri: vscode.Uri, options: { overwrite: boolean }): void {
        const content = this.readFile(oldUri);
        this.writeFile(newUri, content, { create: true, overwrite: options.overwrite });
        this.delete(oldUri, { recursive: false });
    }

    // Helper to write string content
    writeFileString(uri: vscode.Uri, content: string): void {
        this.writeFile(uri, new TextEncoder().encode(content), { create: true, overwrite: true });
    }
}
