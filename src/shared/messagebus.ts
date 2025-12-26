/**
 * MessageBus - Unified communication layer between Webview and Extension Host
 * 
 * This module defines the message types and provides utilities for
 * type-safe communication across the Webview boundary.
 */

// ============================================================
// Message Type Definitions
// ============================================================

export type MessageType =
    // Navigation operations (Native Bridge)
    | 'nav:open-resource'    // Open resource in native editor
    | 'nav:reveal-record'    // Reveal record in side bar/explorer

    // File operations
    | 'file:select'          // Request file picker dialog
    | 'file:upload'          // Upload file to assets directory

    // Record operations
    | 'record:search'        // Search for records (fuzzy)
    | 'record:search:result' // Search results

    // Assigner operations
    | 'assigner:trigger'     // Trigger manual assigner

    // Content operations
    | 'content:update'       // Update preview content
    | 'content:refresh'      // Refresh preview
    | 'variable:update'      // Update variable value in backend

    // Scroll sync
    | 'scroll:toLine'        // Scroll to source line
    | 'scroll:sync'          // Sync scroll position
    ;

// ============================================================
// Message Payload Interfaces
// ============================================================

export interface OpenResourceRequest {
    resourceId: string;     // Variable name or unique ID
    contentType: 'code' | 'markdown' | 'file';
    content?: string;       // Current content (if not file)
    language?: string;      // Language ID for code
    filePath?: string;      // Absolute path for existing files
    viewColumn?: number;    // Optional view column
}

export interface RevealRecordRequest {
    recordId: string;
}

export interface FileSelectRequest {
    fieldName: string;
    accept: string;  // e.g., "image/png,image/jpeg"
    multiple?: boolean;
}

export interface FileSelectResponse {
    fieldName: string;
    files: Array<{
        name: string;
        relativePath: string;  // Path relative to project root
        size: number;
        mimeType: string;
    }>;
}

export interface FileUploadRequest {
    fieldName: string;
    sourceUri: string;  // Absolute path or data URI
    targetDir?: string; // Default: 'assets'
}

export interface FileUploadResponse {
    fieldName: string;
    success: boolean;
    relativePath?: string;
    error?: string;
}

export interface RecordSearchRequest {
    query: string;
    fieldName: string;
    limit?: number;  // Default: 20
}

export interface RecordSearchResponse {
    fieldName: string;
    results: Array<{
        id: string;
        title: string;
        description?: string;
        tags?: string[];
        icon?: string;
        createdBy?: string;
        createdAt?: string;
    }>;
}

export interface AssignerTriggerRequest {
    fieldName: string;
}

export interface AssignerTriggerResponse {
    fieldName: string;
    success: boolean;
    calculatedFields?: Record<string, unknown>;
    error?: string;
}

export interface VariableUpdateRequest {
    fieldName: string;
    value: string;
}

// ============================================================
// Generic Message Wrapper
// ============================================================

export interface WebviewMessage<T = unknown> {
    type: MessageType;
    requestId?: string;  // For request-response correlation
    payload: T;
}

// ============================================================
// Airalogy Type to Component Mapping
// ============================================================

export const AIRALOGY_TYPE_COMPONENT_MAP: Record<string, string> = {
    // Image file types
    'FileIdPNG': 'var-file-card',
    'FileIdJPG': 'var-file-card',
    'FileIdJPEG': 'var-file-card',
    'FileIdTIFF': 'var-file-card',
    'FileIdSVG': 'var-file-card',
    'FileIdWEBP': 'var-file-card',

    // Video/Audio file types
    'FileIdMP4': 'var-file-card',
    'FileIdMP3': 'var-file-card',

    // Document file types
    'FileIdPDF': 'var-file-card',
    'FileIdDOCX': 'var-file-card',
    'FileIdXLSX': 'var-file-card',
    'FileIdPPTX': 'var-file-card',

    // Data/Text file types
    'FileIdCSV': 'var-file-card',
    'FileIdJSON': 'var-file-card',
    'FileIdMD': 'var-file-card',
    'FileIdTXT': 'var-file-card',
    'FileIdAIMD': 'var-file-card',

    // Code editor types (managed by VarCodeBlock)
    'PyStr': 'var-code-block',
    'JsStr': 'var-code-block',
    'TsStr': 'var-code-block',

    // Markdown editor (managed by VarMarkdownPreview)
    'AiralogyMarkdown': 'var-markdown-preview',

    // Record selector
    'RecordId': 'var-record-selector',

    // Special types
    'IgnoreStr': 'var-input',
    'UserName': 'var-input',
    'CurrentTime': 'var-input',
    'Recommended': 'var-input',
};

/**
 * Get the appropriate component tag for a given Airalogy type
 */
export function getComponentForType(varType: string): string {
    return AIRALOGY_TYPE_COMPONENT_MAP[varType] || 'var-input';
}

/**
 * Get file accept string for a given FileId type
 */
export function getAcceptForFileType(varType: string): string {
    const acceptMap: Record<string, string> = {
        // Images
        'FileIdPNG': 'image/png',
        'FileIdJPG': 'image/jpeg',
        'FileIdJPEG': 'image/jpeg',
        'FileIdTIFF': 'image/tiff',
        'FileIdSVG': 'image/svg+xml',
        'FileIdWEBP': 'image/webp',
        // Video/Audio
        'FileIdMP4': 'video/mp4',
        'FileIdMP3': 'audio/mpeg',
        // Documents
        'FileIdPDF': 'application/pdf',
        'FileIdDOCX': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx',
        'FileIdXLSX': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,.xlsx',
        'FileIdPPTX': 'application/vnd.openxmlformats-officedocument.presentationml.presentation,.pptx',
        // Data/Text
        'FileIdCSV': 'text/csv,.csv',
        'FileIdJSON': 'application/json,.json',
        'FileIdMD': 'text/markdown,.md',
        'FileIdTXT': 'text/plain,.txt',
        'FileIdAIMD': '.aimd',
    };
    return acceptMap[varType] || '*/*';
}

/**
 * Get language for code editor
 */
export function getLanguageForCodeType(varType: string): string {
    const langMap: Record<string, string> = {
        'PyStr': 'python',
        'JsStr': 'javascript',
        'TsStr': 'typescript',
    };
    return langMap[varType] || 'plaintext';
}

/**
 * Check if a type is a file upload type
 */
export function isFileUploadType(varType: string): boolean {
    return varType.startsWith('FileId');
}

/**
 * Check if a type is a code editor type
 */
export function isCodeEditorType(varType: string): boolean {
    return ['PyStr', 'JsStr', 'TsStr'].includes(varType);
}

/**
 * Generate a unique request ID
 */
export function generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}
