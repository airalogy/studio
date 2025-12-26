# Airalogy Markdown Studio

[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/yonghe.airalogy-markdown-studio?label=VS%20Code%20Marketplace&logo=visualstudiocode&logoColor=white)](https://marketplace.visualstudio.com/items?itemName=yonghe.airalogy-markdown-studio)
[![Installs](https://img.shields.io/visual-studio-marketplace/i/yonghe.airalogy-markdown-studio?label=Installs&logo=visualstudiocode)](https://marketplace.visualstudio.com/items?itemName=yonghe.airalogy-markdown-studio)
[![Open VSX](https://img.shields.io/open-vsx/v/yonghe/airalogy-markdown-studio?label=Open%20VSX&logo=eclipse)](https://open-vsx.org/extension/yonghe/airalogy-markdown-studio)
[![GitHub](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/airalogy/studio/blob/main/LICENSE)

Airalogy Markdown Studio is a professional VS Code extension designed for editing and previewing AIMD (Airalogy Markdown) protocol files — an extended Markdown format for defining experimental protocols with interactive templates like variables, steps, and checkpoints. It provides a modern, "Scientific Minimalist" preview interface to help scientists and researchers visualize their experimental workflows.

## Features

- **Interactive Timeline Preview**: Visualize your protocol as a sleek, card-based timeline.
- **Scientific Minimalist Design**: High-fidelity UI inspired by professional lab design tools, offering high contrast and reduced visual clutter.
- **Unified Rendering Engine**: Powered by Remark/Rehype and Vue.js for robust and extensible document parsing.
- **Python Backend Integration**: Binary sidecar architecture for advanced features like AI assistance and data export.
- **Real-time Synchronization**: The preview updates instantly as you edit your `.aimd` files.
- **Smart Variable Highlighting**: Easily identify and interact with protocol variables.
- **Theme Support**: Choose between Modern, Journal, Clinical, and Westlake themes with full dark mode support.
- **Status Bar Integration**: Quick access to preview commands directly from the status bar.

## Usage

1. Open any file with the `.aimd` extension.
2. Click the **AIMD Preview** button in the status bar (bottom right).
3. Alternatively, use the preview icon in the editor title bar or the context menu.

## Extension Settings

This extension contributes the following settings:

* `aimd.preview.buttonText`: Customize the status bar button text.
* `aimd.preview.buttonIcon`: Change the status bar icon (uses VS Code Codicons).
* `aimd.preview.buttonPriority`: Adjust the position of the status bar button.
* `aimd.pythonMode`: Switch between **bundled** (pre-compiled) and **system** Python environments.
* `aimd.systemPythonPath`: Path to the system Python executable (auto-synced with Python extension).

## Requirements

* VS Code version 1.74.0 or higher.
* Python 3.8+ (Optional: The extension bundles pre-compiled binaries for Win/Mac/Linux, but a local Python installation can be used for development).

## Release Notes

### 0.4.5

Smart dependency management:
- **Intelligent Error Handling**: Assigner failures with missing packages now show one-click install buttons.
- **uv First**: All installations default to `uv` package manager for speed and reliability.
- **Python Version Check**: Warns if Python < 3.13 (required by Airalogy SDK) with actionable options.
- **Homebrew Detection**: Recognizes macOS Homebrew Python and guides users to proper installation methods.

### 0.4.4

Project structure improvements:
- **New Logo**: Updated extension icon with refreshed branding.
- **Consolidated Backend**: Merged `airalogy_mock` and `aimd_studio` modules into `python/` directory for cleaner project structure.
- **Migrated to Organization**: Source code now hosted at [github.com/airalogy/studio](https://github.com/airalogy/studio).

### 0.4.3

**Critical Fix**:
- **Missing Module in Package**: Included `airalogy_mock` directory in the extension package. This resolves the backend crash when switching to System Python ("airalogy_mock not found" / "NoneType object is not callable").

### 0.4.2

Features and improvements:
- **Environment Management**: Seamless switching between Bundled and System Python.
- **Dependency Handling**: Automatic check and install prompts for `airalogy` package.
- **Session Persistence**: Active sessions now survive backend restarts and environment switches.

### 0.4.1

Bug fixes for Windows binary:
- **airalogy SDK**: Fixed missing SDK in compiled binaries causing Record mode errors.
- **Version Endpoint**: Added backend version info for debugging.

### 0.3.2

Bug fixes and packaging improvements:
- **Dependency Bundling**: Fixed missing runtime dependencies (e.g., `unified`) in packaged extension using `esbuild`.
- **Improved Reliability**: Resolved "Cannot find module" errors on fresh installations.

### 0.3.1

CI/CD automation and build pipeline:
- **Multi-Platform Binaries**: Automated PyInstaller builds for Win/Mac/Linux.
- **Auto Publishing**: GitHub Actions for automatic marketplace releases.

### 0.3.0

Python backend integration:
- **Binary Sidecar Pattern**: Python backend via JSON-RPC over stdio.
- **Backend Bridge**: Seamless TypeScript-Python communication.

### 0.2.0

Major update focusing on UI refinement and architecture modernization:
- **Scientific Minimalist Redesign**: A cleaner, more professional look.
- **Unified Renderer**: Robust parsing using the Unified ecosystem.
- **Vue.js Integration**: Completely rewritten preview interface using Vue.
- **Enhanced Reliability**: Fixed numerous parsing and display bugs.

### 0.1.0

Initial release of AIMD Studio:
- Basic syntax highlighting for `.aimd` files.
- Advanced Timeline Preview with card-based layout.
- Experimental ProFlow-style rendering.
- Status bar and editor title integration.

---

**Happy Experimenting!**
