/**
 * MDX Compiler Module
 * 
 * Compiles AIMD markdown content to HTML using MDX with custom plugins.
 * This bridges the gap between MDX and Vue by outputting HTML that Vue can render.
 */

import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import remarkRehype from 'remark-rehype';
import rehypeStringify from 'rehype-stringify';
import rehypeRaw from 'rehype-raw';
import { getComponentForType, getLanguageForCodeType } from '../../shared/messagebus';
import { HighlighterService } from '../services/HighlighterService';
import { marked } from 'marked';

// Regex patterns for matching AIMD syntax
const VARIABLE_REGEX = /\{\{\s*(var(?:_table)?)\s*\|\s*([^}]+)\}\}/g;
const STEP_REGEX = /\{\{\s*step\s*\|\s*([^}]+)\}\}/g;
const CHECK_REGEX = /\{\{\s*check\s*\|\s*([^}]+)\}\}/g;
const REF_STEP_REGEX = /\{\{\s*ref_step\s*\|\s*([^}]+)\}\}/g;
const REF_VAR_REGEX = /\{\{\s*ref_var\s*\|\s*([^}]+)\}\}/g;

// Placeholder for pipes inside variables (to avoid table parsing issues)
const PIPE_PLACEHOLDER = '\uFF5C';
// Placeholder for protected code blocks
const PROTECT_PLACEHOLDER = '___PROTECTED_CODE_BLOCK_';

/**
 * Preprocess AIMD content before MDX compilation
 */
function preprocessContent(content: string): string {
    let processed = content;

    // Collapse multi-line variable definitions
    processed = collapseMultiLineVariables(processed);

    // Escape pipes inside variables
    processed = processed.replace(/\{\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\}/g, (match) => {
        return match.replace(/\|/g, PIPE_PLACEHOLDER);
    });

    return processed;
}

/**
 * Collapse multi-line variable definitions into single lines
 */
function collapseMultiLineVariables(content: string): string {
    let result = '';
    let i = 0;

    while (i < content.length) {
        if (content[i] === '{' && content[i + 1] === '{') {
            const start = i;
            i += 2;
            let depth = 1;

            while (i < content.length && depth > 0) {
                if (content[i] === '{' && content[i + 1] === '{') {
                    depth++;
                    i += 2;
                } else if (content[i] === '}' && content[i + 1] === '}') {
                    depth--;
                    if (depth === 0) {
                        i += 2;
                        break;
                    }
                    i += 2;
                } else {
                    i++;
                }
            }

            let varBlock = content.slice(start, i);
            varBlock = varBlock.replace(/\s+/g, ' ');
            result += varBlock;
        } else {
            result += content[i];
            i++;
        }
    }

    return result;
}

/**
 * Convert AIMD variables to custom element syntax
 */
/**
 * Convert AIMD variables to custom element syntax (Async with Highlighting)
 */
/**
 * Helper to process a single variable match
 */
function processVariableMatch(
    match: RegExpMatchArray,
    variablesMetadata?: Record<string, any>,
    calculatedFields?: Record<string, any>,
    assignersMetadata?: Record<string, any>
) {
    const tagType = match[1];
    const paramsMatch = match[2];

    // Parse parameters using robust parser
    const attributes = parseTypedParams(paramsMatch || '');

    // Determine component name
    const varName = attributes.name || '';

    // Supplement with backend metadata if available
    const meta = variablesMetadata ? variablesMetadata[varName] : null;
    if (meta) {
        attributes.title = meta.title || attributes.title;
        attributes.description = meta.description || attributes.description;
        attributes.type = attributes.type || meta.type;
        attributes.default = (meta.default !== undefined && meta.default !== null) ? String(meta.default) : attributes.default;

        // Merge constraints
        if (meta.constraints) {
            Object.assign(attributes, meta.constraints);
        }
    }

    // Check if this is a table variable
    const isTable = tagType === 'var_table' || attributes.subvars !== undefined;

    return {
        tagType,
        attributes,
        varName,
        meta,
        isTable,
        calculatedFields,
        assignersMetadata
    };
}

/**
 * Generate HTML for a variable component (Common Logic)
 */
function generateVariableHtml(
    data: ReturnType<typeof processVariableMatch>,
    highlightedHtml: string = ''
): string {
    const { attributes, varName, meta, isTable, calculatedFields, assignersMetadata } = data;

    if (isTable) {
        // Process subvars into columns
        let columnsJson = '[]';
        if (attributes.subvars) {
            const columns = parseSubvars(attributes.subvars);
            columnsJson = JSON.stringify(columns);
        }

        // Get initial rows from backend metadata if available
        let initialRowsJson = '';
        if (meta && meta.default_value && Array.isArray(meta.default_value)) {
            initialRowsJson = JSON.stringify(meta.default_value);
        }

        // Check if there's a calculated value for this table
        const calcValue = calculatedFields ? calculatedFields[varName] : null;
        if (calcValue && Array.isArray(calcValue)) {
            initialRowsJson = JSON.stringify(calcValue);
        }

        // Get assigner info for this field
        const assignerInfo = assignersMetadata ? assignersMetadata[varName] : null;
        const assignerMode = assignerInfo?.mode || '';
        const isReadonly = assignerInfo?.readonly || false;
        const dependentFields = assignerInfo?.dependent_fields || [];
        const depsJson = dependentFields.length > 0 ? JSON.stringify(dependentFields) : '';

        // Generate var-table element
        const tableAttrs = [
            `name="${escapeAttr(String(varName))}"`,
            attributes.title ? `title="${escapeAttr(String(attributes.title))}"` : '',
            `columns="${escapeAttr(columnsJson)}"`,
            initialRowsJson ? `initial-rows="${escapeAttr(initialRowsJson)}"` : '',
            calcValue ? 'is-calculated="true"' : '',
            assignerMode ? `assigner-mode="${escapeAttr(assignerMode)}"` : '',
            isReadonly ? 'assigner-readonly="true"' : '',
            depsJson ? `assigner-deps="${escapeAttr(depsJson)}"` : ''
        ].filter(Boolean).join(' ');

        return `<var-table ${tableAttrs}></var-table>`;
    } else {
        // Check if there's a calculated value for this variable
        const calcValue = calculatedFields ? calculatedFields[varName] : null;
        let calculatedValue = '';
        if (calcValue !== undefined && calcValue !== null) {
            if (typeof calcValue === 'object' && calcValue.checked !== undefined) {
                // It's a CheckValue - format for display
                calculatedValue = calcValue.annotation || (calcValue.checked ? '✓' : '✗');
            } else if (typeof calcValue === 'object') {
                calculatedValue = JSON.stringify(calcValue);
            } else {
                calculatedValue = String(calcValue);
            }
        }

        // Get assigner info for this field
        const assignerInfo = assignersMetadata ? assignersMetadata[varName] : null;
        const assignerMode = assignerInfo?.mode || '';
        const isReadonly = assignerInfo?.readonly || false;
        const dependentFields = assignerInfo?.dependent_fields || [];
        const depsJson = dependentFields.length > 0 ? JSON.stringify(dependentFields) : '';

        // Try to resolve type from metadata if not in attributes
        // Metadata keys might come from Python backend (pydantic)
        const varMeta = meta;
        // Check potential keys for type - prioritize varType for custom components
        // Backend 'varType' is the specific semantic type (e.g. 'FileIdPNG', 'AiralogyMarkdown')
        // 'attributes.type' might be the generic JSON schema type (e.g. 'string', 'any') or user input
        const backendVarType = varMeta?.varType || varMeta?.var_type;

        let type = attributes.type || 'str';

        if (backendVarType) {
            // Always prefer the specific backend type if available
            // This ensures 'FileIdPNG' is used instead of 'string', etc.
            type = backendVarType;
        } else if (varMeta?.type) {
            // Fallback to generic meta type if no specific varType
            // But only if we didn't have a type from attributes (which we might have handled in processVariableMatch)
            // Actually processVariableMatch merges meta.type into attributes.type already.
            // So 'type' variable here already holds that.
        }

        const typeStr = String(type);

        // Determine component to use based on type
        const componentTag = getComponentForType(typeStr);
        const language = getLanguageForCodeType(typeStr);

        // Generate component element
        const inputAttrs = [
            `name="${escapeAttr(String(varName))}"`,
            `var-type="${escapeAttr(typeStr)}"`,
            attributes.title ? `title="${escapeAttr(String(attributes.title))}"` : '',
            attributes.default ? `default-value="${escapeAttr(String(attributes.default))}"` : '',
            attributes.description ? `description="${escapeAttr(String(attributes.description))}"` : '',
            calculatedValue ? `calculated-value="${escapeAttr(calculatedValue)}"` : '',
            assignerMode ? `assigner-mode="${escapeAttr(assignerMode)}"` : '',
            isReadonly ? 'assigner-readonly="true"' : '',
            depsJson ? `assigner-deps="${escapeAttr(depsJson)}"` : '',
            attributes.min ? `min="${escapeAttr(String(attributes.min))}"` : '',
            attributes.max ? `max="${escapeAttr(String(attributes.max))}"` : '',
            attributes.ge ? `ge="${escapeAttr(String(attributes.ge))}"` : '',
            attributes.le ? `le="${escapeAttr(String(attributes.le))}"` : '',
            attributes.gt ? `gt="${escapeAttr(String(attributes.gt))}"` : '',
            attributes.lt ? `lt="${escapeAttr(String(attributes.lt))}"` : '',
            // Add language attribute for code blocks
            language !== 'plaintext' ? `language="${escapeAttr(language)}"` : '',
            // Add highlighted/rendered HTML (for code or markdown)
            highlightedHtml ? `rendered-html="${escapeAttr(highlightedHtml)}"` : ''
        ].filter(Boolean).join(' ');

        return `<${componentTag} ${inputAttrs}></${componentTag}>`;
    }
}

/**
 * Convert AIMD variables to custom element syntax (Async with Highlighting)
 */
async function convertVariablesToComponents(
    html: string,
    variablesMetadata?: Record<string, any>,
    calculatedFields?: Record<string, any>,
    assignersMetadata?: Record<string, any>
): Promise<string> {
    const matches = [...html.matchAll(VARIABLE_REGEX)];
    if (matches.length === 0) return html;

    const replacements = await Promise.all(matches.map(async (match) => {
        const data = processVariableMatch(match, variablesMetadata, calculatedFields, assignersMetadata);

        let highlightedHtml = '';
        if (!data.isTable) {
            // Determine content to highlight/render
            // Priority: calculatedValue > default value
            // We need to re-calculate 'calculatedValue' logic briefly or extract it. 
            // For simplicity, we just use the raw attribute default for now if not calculated
            // Actually, let's just peek at the data logic again or assume we can pass the content.

            // Re-deriving contentToProcess for highlighting:
            const calcValue = data.calculatedFields ? data.calculatedFields[data.varName] : null;
            let val = '';
            if (calcValue !== undefined && calcValue !== null) {
                if (typeof calcValue === 'object') val = JSON.stringify(calcValue); // simplified
                else val = String(calcValue);
            } else {
                val = String(data.attributes.default || '');
            }

            const type = String(data.attributes.type || (data.meta?.type) || 'str');
            const language = getLanguageForCodeType(type);

            if (val) {
                if (language !== 'plaintext') {
                    highlightedHtml = await HighlighterService.getInstance().highlight(val, language);
                } else if (type === 'AiralogyMarkdown') {
                    try {
                        let markdownContent = val;
                        markdownContent = markdownContent.replace(
                            /\[\[([^\]]+)\]\]/g,
                            '<a href="#" class="record-link" data-record-id="$1">$1</a>'
                        );
                        const parsed = marked.parse(markdownContent, { async: false });
                        highlightedHtml = typeof parsed === 'string' ? parsed : await parsed;
                    } catch (e) {
                        console.warn('Markdown rendering failed:', e);
                        highlightedHtml = `<p>Error rendering Markdown: ${e}</p>`;
                    }
                }
            }
        }

        return generateVariableHtml(data, highlightedHtml);
    }));

    // Reconstruct string
    let result = '';
    let lastIndex = 0;
    matches.forEach((match, i) => {
        result += html.substring(lastIndex, match.index!);
        result += replacements[i];
        lastIndex = match.index! + match[0].length;
    });
    result += html.substring(lastIndex);

    return result;
}

/**
 * Convert AIMD variables to custom element syntax (Sync - No Highlighting)
 */
function convertVariablesToComponentsSync(
    html: string
): string {
    const matches = [...html.matchAll(VARIABLE_REGEX)];
    if (matches.length === 0) return html;

    let result = '';
    let lastIndex = 0;

    matches.forEach((match) => {
        const data = processVariableMatch(match);
        const replacement = generateVariableHtml(data, ''); // No highlighting

        result += html.substring(lastIndex, match.index!);
        result += replacement;
        lastIndex = match.index! + match[0].length;
    });

    result += html.substring(lastIndex);
    return result;
}

/**
 * Robustly parse parameters string (e.g., "name: type = val, key=val")
 * Resembles the logic from legacy code.
 */
function parseTypedParams(params: string): Record<string, any> {
    const attributes: Record<string, any> = {};

    // 1. Split top-level commas, respecting quotes and brackets
    const parts: string[] = [];
    let currentPart = '';
    let parenLevel = 0;
    let bracketLevel = 0;
    let braceLevel = 0;
    let inQ: string | null = null;

    for (let i = 0; i < params.length; i++) {
        const char = params[i];
        if (char === '"' || char === "'") {
            if (inQ === char) inQ = null;
            else if (!inQ) inQ = char;
        }

        if (!inQ) {
            if (char === '(') parenLevel++;
            else if (char === ')') parenLevel--;
            else if (char === '[') bracketLevel++;
            else if (char === ']') bracketLevel--;
            else if (char === '{') braceLevel++;
            else if (char === '}') braceLevel--;
        }

        if (char === ',' && parenLevel === 0 && bracketLevel === 0 && braceLevel === 0 && !inQ) {
            parts.push(currentPart.trim());
            currentPart = '';
        } else {
            currentPart += char;
        }
    }
    if (currentPart.trim()) parts.push(currentPart.trim());

    // 2. Process first part (potential name:type=default syntax)
    if (parts.length > 0) {
        const firstPart = parts[0];
        // Check if it's a key=value pair or position argument
        if (firstPart.includes('=') && !firstPart.includes(':') && /^[a-zA-Z0-9_]+\s*=/.test(firstPart)) {
            // It's a named param like title="foo", handle in loop
        } else {
            // It's name[:type][=default]
            // We remove it from parts list and handle explicitly
            parts.shift();

            const mainMatch = firstPart.match(/^([a-zA-Z0-9_.-]+)(?:\s*:\s*([a-zA-Z0-9_\[\]]+))?(?:\s*=\s*(.+))?$/);
            if (mainMatch) {
                attributes.name = mainMatch[1];
                if (mainMatch[2]) attributes.type = mainMatch[2];
                if (mainMatch[3]) {
                    let val = mainMatch[3].trim();
                    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
                        val = val.slice(1, -1);
                    }
                    attributes.default = val;
                }
            } else {
                attributes.name = firstPart;
            }
        }
    }

    // 3. Process remaining parts (key=value)
    // We iterate over the original 'parts' array or what remains
    // Note: If we shifted above, we iterate over the rest. If we didn't shift (because first part was key=value), we iterate all.
    // Wait, the logic above is slightly flawed if I shift. I should just iterate parts.

    // Let's restart logic slightly for safety:
    // Process ALL parts. If a part looks like key=value, add to map. 
    // If it's the FIRST part and DOESN'T look like key=value (or looks like name:type), treat as name.

    // We already handled the "Shift" case. So now process 'parts' (which might be empty or contain only named args)

    // However, we missed one case: if the loop above shifted, 'parts' is modified. 
    // If it didn't shift, we still have the first part in 'parts' and it needs to be processed as key=value? 
    // Actually the check `if (firstPart.includes('=') ...)` covers the standard key=value case. 
    // So if we didn't shift, it means the first part IS a key=value pair (or invalid).

    for (const part of parts) {
        const eqIdx = part.indexOf('=');
        if (eqIdx > 0) {
            // Standard key=value
            const key = part.substring(0, eqIdx).trim();
            let val = part.substring(eqIdx + 1).trim();

            // Remove quotes
            if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
                val = val.slice(1, -1);
            }
            attributes[key] = val;
        } else {
            // boolean flag? e.g. "check"
            attributes[part] = true;
        }
    }

    return attributes;
}

/**
 * Parse subvars string into column definitions
 */
function parseSubvars(subvarsStr: string): any[] {
    const columns: any[] = [];

    // Robust split of subvars by comma
    const subvarParts: string[] = [];
    let currentPart = '';
    let parenLevel = 0;
    let bracketLevel = 0;
    let inQ: string | null = null;

    // Remove outer brackets if present [ ... ]
    let cleanStr = subvarsStr.trim();
    if (cleanStr.startsWith('[') && cleanStr.endsWith(']')) {
        cleanStr = cleanStr.slice(1, -1);
    }

    for (let i = 0; i < cleanStr.length; i++) {
        const char = cleanStr[i];
        if (char === '"' || char === "'") {
            if (inQ === char) inQ = null;
            else if (!inQ) inQ = char;
        }
        if (!inQ) {
            if (char === '(') parenLevel++;
            else if (char === ')') parenLevel--;
            else if (char === '[') bracketLevel++;
            else if (char === ']') bracketLevel--;
        }
        if (char === ',' && parenLevel === 0 && bracketLevel === 0 && !inQ) {
            subvarParts.push(currentPart.trim());
            currentPart = '';
        } else {
            currentPart += char;
        }
    }
    if (currentPart.trim()) subvarParts.push(currentPart.trim());

    // Process each part
    for (const part of subvarParts) {
        // Check if it's "var(...)"
        const varMatch = part.match(/^var\s*\(([\s\S]*)\)$/);
        if (varMatch) {
            const innerParams = parseTypedParams(varMatch[1]);
            // name is usually stored in 'name' by parseTypedParams if it was the first arg
            const id = innerParams.name || 'unknown';
            columns.push({
                id: id,
                title: innerParams.title || formatVariableName(id),
                type: innerParams.type || 'str',
                default: innerParams.default !== undefined ? String(innerParams.default) : '',
                description: innerParams.description || ''
            });
        } else {
            // Fallback for simple "name: type = default" string in the array
            // e.g. subvars=[col1: float, col2: str] (less common but possible in simple syntax)
            const innerParams = parseTypedParams(part);
            const id = innerParams.name || 'unknown';
            columns.push({
                id: id,
                title: innerParams.title || formatVariableName(id),
                type: innerParams.type || 'str',
                default: innerParams.default !== undefined ? String(innerParams.default) : '',
                description: ''
            });
        }
    }

    return columns;
}

/**
 * Helper to format variable name (snake_case to Title Case)
 */
function formatVariableName(name: string): string {
    return name
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}


/**
 * Escape attribute values for HTML
 */
function escapeAttr(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

/**
 * Convert GitHub-style callouts to custom elements
 */
function convertCallouts(html: string): string {
    // Match blockquotes with alert syntax and wrap in callout-block
    // Pattern: <blockquote> ... [!TYPE] ... content ... </blockquote>
    const blockquotePattern = /<blockquote>\s*<p>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION|EXAMPLE|ABSTRACT|INFO|SUCCESS|DANGER|BUG|QUOTE)\]([\s\S]*?)<\/p>([\s\S]*?)<\/blockquote>/gi;

    return html.replace(blockquotePattern, (match, type, firstContent, restContent) => {
        const calloutType = type.toLowerCase();
        const content = firstContent + restContent;
        return `<callout-block type="${calloutType}">${content.trim()}</callout-block>`;
    });
}

/**
 * Wrap content following steps and checks into step-card components
 */
/**
 * Wrap content following steps and checks into step-card components
 * UPDATED: Splits step content at Headers (h1-h6) or Dividers (hr)
 */
/**
 * Wrap content following steps and checks into step-card components
 * UPDATED: 
 * 1. Splits step content at Headers (h1-h6) or Dividers (hr).
 * 2. Adopts Headers immediately preceding a step into that step.
 * 3. Cleans up orphaned <p> tags to ensure lists/content stay inside cards.
 */
/**
 * Wrap content following steps and checks into step-card components
 * UPDATED: 
 * 1. Splits step content at Headers (h1-h6) or Dividers (hr).
 * 2. PROMOTES Headers immediately preceding a step to be the Step Title.
 * 3. Cleans up orphaned <p> tags and <br> tags.
 */
function wrapContentInSteps(html: string): string {
    const splitRegex = /(\{\{\s*step\s*\|\s*[^}]+\}\})/g;
    const parts = html.split(splitRegex);

    if (parts.length <= 1) return html;

    let stepCounter = 1;
    let result = '';

    // State to pass content from previous block to next
    let pendingHeader = ''; // Content of the header tag (used for final leftover)
    let pendingHeaderText = ''; // Text content of the header (for promotion)
    let pendingPTag = false;

    // Helper to process a block of content
    const processBlock = (block: string, isPreamble: boolean): string => {
        let content = block;

        // 1. Check for trailing <p> (orphaned open tag)
        // Also handle <br> or whitespace after <p>
        if (content.match(/<p>(\s|<br\s*\/?>)*$/)) {
            content = content.replace(/<p>(\s|<br\s*\/?>)*$/, '');
            pendingPTag = true;
        }

        // 2. Check for trailing Header (Header Promotion)
        // Match Header followed by optional <br>, whitespace, or empty P tags
        const trailingHRegex = /(<h[1-6]\b[^>]*>(.*?)<\/h[1-6]>)(?:\s|<br\s*\/?>|<p>\s*<\/p>)*$/i;
        const trailingHMatch = content.match(trailingHRegex);

        if (trailingHMatch) {
            // We capture the header BUT we want to PROMOTE it
            pendingHeader = trailingHMatch[1];
            // Naive text extraction (strip tags from inner HTML)
            pendingHeaderText = trailingHMatch[2].replace(/<[^>]+>/g, '').trim();

            // Remove the header from the current block's content
            content = content.substring(0, trailingHMatch.index);
        }

        return content;
    };

    // --- Process Preamble ---
    let preamble = processBlock(parts[0], true);
    if (preamble && preamble.trim()) {
        result += `<div class="aimd-text-card preamble">${preamble}</div>`;
    }

    // --- Process Steps ---
    for (let i = 1; i < parts.length; i += 2) {
        const marker = parts[i];
        let rawContent = parts[i + 1] || '';

        // 1. Determine Title from Promotion
        let promotedTitle = '';
        if (pendingHeaderText) {
            promotedTitle = pendingHeaderText;
            pendingHeader = '';
            pendingHeaderText = '';
        } else if (pendingHeader) {
            pendingHeader = '';
        }

        // 2. Handle Orphaned P Tags (Restore context)
        let contentPrefix = '';
        if (pendingPTag) {
            contentPrefix += '<p>';
            pendingPTag = false;
        }

        let content = contentPrefix + rawContent;

        // 3. Clean up leading </p> or <br> artifacts
        if (!contentPrefix.endsWith('<p>') && content.match(/^\s*<\/p>/)) {
            content = content.replace(/^\s*<\/p>/, '');
        }
        content = content.replace(/^(\s|<br\s*\/?>)+/, '');

        // 4. Extract Title (Fallback if no Promoted Title)
        let extractedTitle = '';
        if (!promotedTitle) {
            const titleMatch = content.match(/^[ \t]*(?:<p>)?([ \t]*[^<\n\r]{1,100})/);
            if (titleMatch && titleMatch[1].trim()) {
                if (!titleMatch[1].trim().startsWith('<')) {
                    extractedTitle = titleMatch[1].trim();
                    const firstIndex = content.indexOf(extractedTitle);
                    if (firstIndex !== -1) {
                        content = content.substring(0, firstIndex) + content.substring(firstIndex + extractedTitle.length);
                    }
                }
            }
        }

        const effectiveTitle = promotedTitle || extractedTitle;

        // 5. Check for Next Padding (Prepare for next loop)
        content = processBlock(content, false);

        // 6. Split content at Internal Header/Divider (Interruption logic)
        const interruptionRegex = /(<h[1-6]|<hr)/i;
        const match = content.match(interruptionRegex);

        let stepBody = content;
        let textCardContent = '';

        if (match && match.index !== undefined) {
            stepBody = content.substring(0, match.index);
            textCardContent = content.substring(match.index);
        }

        // 7. Generate Step Card
        let componentTag = convertStepMarker(marker, stepCounter++, effectiveTitle);
        result += componentTag.replace('></step-card>', `><div>${stepBody}</div></step-card>`);

        // 8. Append Text Card
        if (textCardContent.trim()) {
            result += `<div class="aimd-text-card">${textCardContent}</div>`;
        }
    }

    // Capture final leftover if any
    if (pendingHeader) {
        result += `<div class="aimd-text-card">${pendingHeader}</div>`;
    }

    return result;
}

/**
 * Convert check markers to check-pill components
 */
function convertChecksToComponents(html: string, calculatedFields?: Record<string, any>, assignersMetadata?: Record<string, any>): string {
    // Regex to match {{check|...}} and potentially leading <p> and trailing text
    // Handles cases like <p>{{check|id}} Title text</p>
    const checkRegex = /(<p>)?\s*\{\{\s*check\s*\|\s*([^}]+)\}\}([ \t]*[^<\n\r]+)?/g;

    return html.replace(checkRegex, (match, pTag, params, trailingText) => {
        const parts = params.replace(new RegExp(PIPE_PLACEHOLDER, 'g'), '|').split(',').map((p: string) => p.trim());
        const checkId = parts[0];
        let checkedMessage = '';
        let title = (trailingText || '').trim();

        // Parse parameters
        for (let j = 1; j < parts.length; j++) {
            const part = parts[j];
            if (part.includes('checked_message=')) {
                const m = part.match(/checked_message=(["'])(.+?)\1/);
                if (m) checkedMessage = m[2];
            } else if (part.includes('title=')) {
                const m = part.match(/title=(["'])(.+?)\1/);
                if (m) title = m[2];
            }
        }

        if (!title) title = checkId;

        // Check if there's a calculated CheckValue for this check
        let autoChecked = '';
        let autoAnnotation = '';
        if (calculatedFields && calculatedFields[checkId]) {
            const calcValue = calculatedFields[checkId];
            if (typeof calcValue === 'object' && calcValue.checked !== undefined) {
                autoChecked = calcValue.checked ? 'true' : 'false';
                autoAnnotation = calcValue.annotation || '';
            }
        }

        const attrs = [
            `name="${escapeAttr(checkId)}"`,
            `title="${escapeAttr(title)}"`,
            checkedMessage ? `checked-message="${escapeAttr(checkedMessage)}"` : '',
            autoChecked ? `auto-checked="${autoChecked}"` : '',
            autoAnnotation ? `auto-annotation="${escapeAttr(autoAnnotation)}"` : ''
        ].filter(Boolean).join(' ');

        const pill = `<check-pill ${attrs}></check-pill>`;
        return pTag ? `<p>${pill}` : pill;
    });
}

function convertStepMarker(marker: string, ordinal: number, extractedTitle: string): string {
    const paramsMatch = marker.match(/\{\{\s*step\s*\|\s*([^}]+)\}\}/);
    if (!paramsMatch) return marker;

    const params = paramsMatch[1].replace(new RegExp(PIPE_PLACEHOLDER, 'g'), '|');
    const parts = params.split(',').map((p: string) => p.trim());

    const stepId = parts[0];
    let level = 1;
    let hasCheck = false;
    let checkedMessage = '';

    // Parse parameters
    for (let j = 1; j < parts.length; j++) {
        const part = parts[j];
        if (/^\d+$/.test(part)) {
            level = parseInt(part, 10);
        } else if (part.includes('check=')) {
            hasCheck = part.includes('true') || part.includes('True');
        } else if (part.includes('checked_message=')) {
            const m = part.match(/checked_message=(["'])(.+?)\1/);
            if (m) checkedMessage = m[2];
        }
    }

    const title = extractedTitle || stepId;

    const attrs = [
        `step-id="${escapeAttr(stepId)}"`,
        `step-number="${ordinal}"`,
        `title="${escapeAttr(title)}"`,
        `level="${level}"`,
        hasCheck ? `has-check="true"` : '',
        checkedMessage ? `checked-message="${escapeAttr(checkedMessage)}"` : ''
    ].filter(Boolean).join(' ');

    return `<step-card ${attrs}></step-card>`;
}


/**
 * Convert AIMD reference tags to custom elements  
 */
function convertReferences(html: string): string {
    // Convert step references
    html = html.replace(REF_STEP_REGEX, (match, stepId) => {
        const cleaned = stepId.trim();
        return `<ref-tag type="step" target="${escapeAttr(cleaned)}"></ref-tag>`;
    });

    // Convert variable references
    html = html.replace(REF_VAR_REGEX, (match, varId) => {
        const cleaned = varId.trim();
        return `<ref-tag type="var" target="${escapeAttr(cleaned)}"></ref-tag>`;
    });

    return html;
}

/**
 * Build a mapping of content signatures to source line numbers
 * This is done BEFORE preprocessing to capture original line positions
 */
function buildLineMapping(content: string): Map<string, number> {
    const lineMap = new Map<string, number>();
    const lines = content.split('\n');

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        if (trimmed.length === 0) continue;

        // Create content signature (first 50 chars, normalized)
        // This will be used to match against HTML content later
        let signature = trimmed.substring(0, 50).toLowerCase();

        // Special handling for different block types
        if (/^#{1,6}\s/.test(trimmed)) {
            // Header: use header text as signature
            signature = 'h:' + trimmed.replace(/^#{1,6}\s+/, '').substring(0, 40).toLowerCase();
        } else if (/^\{\{\s*step\s*\|/.test(trimmed)) {
            // Step: extract step ID
            const match = trimmed.match(/\{\{\s*step\s*\|\s*([^,}]+)/);
            if (match) signature = 'step:' + match[1].trim().toLowerCase();
        } else if (/^\{\{\s*check\s*\|/.test(trimmed)) {
            // Check: extract check ID
            const match = trimmed.match(/\{\{\s*check\s*\|\s*([^,}]+)/);
            if (match) signature = 'check:' + match[1].trim().toLowerCase();
        } else if (/^\{\{\s*var/.test(trimmed)) {
            // Variable: extract var name
            const match = trimmed.match(/\{\{\s*var[^|]*\|\s*([^:,}]+)/);
            if (match) signature = 'var:' + match[1].trim().toLowerCase();
        } else if (/^>\s*\[!/.test(trimmed)) {
            // Callout: use callout type
            const match = trimmed.match(/\[!(\w+)\]/);
            if (match) signature = 'callout:' + match[1].toLowerCase() + ':' + i;
        } else if (/^[-*]\s/.test(trimmed)) {
            // List item: use first words
            signature = 'li:' + trimmed.substring(2, 30).toLowerCase() + ':' + i;
        } else {
            // Paragraph: use first words with line number for uniqueness
            signature = 'p:' + signature + ':' + i;
        }

        // Store the mapping (don't overwrite if already exists)
        if (!lineMap.has(signature)) {
            lineMap.set(signature, i);
        }
    }

    return lineMap;
}

/**
 * Add data-source-line attributes using content-based matching
 */
function addSourceLineAttributesWithMapping(html: string, lineMap: Map<string, number>): string {
    // For each mappable element type, try to match and inject line numbers
    let result = html;

    // 1. Headers: match by header text
    result = result.replace(/<(h[1-6])([^>]*)>([^<]+)</gi, (match, tag, attrs, text) => {
        if (attrs.includes('data-source-line')) return match;

        const signature = 'h:' + text.trim().substring(0, 40).toLowerCase();
        const line = lineMap.get(signature);

        if (line !== undefined) {
            return `<${tag}${attrs} data-source-line="${line}">${text}<`;
        }
        return match;
    });

    // 2. Step cards: match by step-id attribute
    result = result.replace(/<step-card([^>]*step-id="([^"]+)"[^>]*)>/gi, (match, attrs, stepId) => {
        if (attrs.includes('data-source-line')) return match;

        const signature = 'step:' + stepId.toLowerCase();
        const line = lineMap.get(signature);

        if (line !== undefined) {
            return `<step-card${attrs} data-source-line="${line}">`;
        }
        return match;
    });

    // 3. Check pills: match by name attribute
    result = result.replace(/<check-pill([^>]*name="([^"]+)"[^>]*)>/gi, (match, attrs, name) => {
        if (attrs.includes('data-source-line')) return match;

        const signature = 'check:' + name.toLowerCase();
        const line = lineMap.get(signature);

        if (line !== undefined) {
            return `<check-pill${attrs} data-source-line="${line}">`;
        }
        return match;
    });

    // 4. Variable inputs: match by name attribute
    result = result.replace(/<var-input([^>]*name="([^"]+)"[^>]*)>/gi, (match, attrs, name) => {
        if (attrs.includes('data-source-line')) return match;

        const signature = 'var:' + name.toLowerCase();
        const line = lineMap.get(signature);

        if (line !== undefined) {
            return `<var-input${attrs} data-source-line="${line}">`;
        }
        return match;
    });

    // 5. Variable tables: match by name attribute
    result = result.replace(/<var-table([^>]*name="([^"]+)"[^>]*)>/gi, (match, attrs, name) => {
        if (attrs.includes('data-source-line')) return match;

        const signature = 'var:' + name.toLowerCase();
        const line = lineMap.get(signature);

        if (line !== undefined) {
            return `<var-table${attrs} data-source-line="${line}">`;
        }
        return match;
    });

    // 6. Callout blocks: match by type attribute (with fallback sequential)
    let calloutIndex = 0;
    result = result.replace(/<callout-block([^>]*type="([^"]+)"[^>]*)>/gi, (match, attrs, type) => {
        if (attrs.includes('data-source-line')) return match;

        // Try to find matching callout in line map
        for (const [sig, line] of lineMap.entries()) {
            if (sig.startsWith('callout:' + type.toLowerCase())) {
                // Found a match, use it and remove from map to avoid reuse
                lineMap.delete(sig);
                return `<callout-block${attrs} data-source-line="${line}">`;
            }
        }
        return match;
    });

    // 7. Paragraphs: Add sequential fallback for remaining <p> tags
    let pIndex = 0;
    const pLines: number[] = [];
    for (const [sig, line] of lineMap.entries()) {
        if (sig.startsWith('p:')) {
            pLines.push(line);
        }
    }
    pLines.sort((a, b) => a - b);

    result = result.replace(/<p([^>]*)>/gi, (match, attrs) => {
        if (attrs.includes('data-source-line')) return match;

        if (pIndex < pLines.length) {
            const line = pLines[pIndex++];
            return `<p${attrs} data-source-line="${line}">`;
        }
        return match;
    });

    return result;
}

export interface MdxCompileResult {
    html: string;
    error?: string;
}

/**
 * Compile AIMD content to HTML using MDX
 */
export async function compileAimdToHtml(
    content: string,
    variablesMetadata?: Record<string, any>,
    calculatedFields?: Record<string, any>,
    assignersMetadata?: Record<string, any>
): Promise<MdxCompileResult> {
    try {
        // Build line mapping BEFORE any preprocessing
        const lineMap = buildLineMapping(content);

        // Preprocess
        const preprocessed = preprocessContent(content);

        // Compile with Unified pipeline (Remark -> Rehype -> HTML)
        const file = await unified()
            .use(remarkParse)
            .use(remarkGfm)
            .use(remarkBreaks)
            .use(remarkRehype, { allowDangerousHtml: true })
            .use(rehypeRaw)
            .use(rehypeStringify)
            .process(preprocessed);

        let html = String(file);

        // 1. Protect code blocks
        const protectedBlocks: string[] = [];
        html = html.replace(/<(code|pre)[^>]*>[\s\S]*?<\/\1>/gi, (match) => {
            const id = protectedBlocks.length;
            protectedBlocks.push(match);
            return `${PROTECT_PLACEHOLDER}${id}__`;
        });

        // 2. Restore pipes before processing custom tags
        html = html.replace(new RegExp(PIPE_PLACEHOLDER, 'g'), '|');

        // 3. Convert all AIMD syntax to components
        // Note: convertSteps and convertChecks are replaced by wrapContentInSteps
        html = wrapContentInSteps(html);
        html = convertChecksToComponents(html, calculatedFields, assignersMetadata);
        html = await convertVariablesToComponents(html, variablesMetadata, calculatedFields, assignersMetadata);
        html = convertCallouts(html);
        html = convertReferences(html);

        // 4. Restore code blocks
        protectedBlocks.forEach((block, i) => {
            html = html.replace(`${PROTECT_PLACEHOLDER}${i}__`, block);
        });

        // 5. Add data-source-line attributes using content-based matching
        html = addSourceLineAttributesWithMapping(html, lineMap);

        return { html };
    } catch (error) {
        return {
            html: '',
            error: (error as Error).message
        };
    }
}

/**
 * Simple synchronous HTML compilation (fallback)
 * Uses the existing unified pipeline for now
 */
export function compileAimdToHtmlSync(content: string): string {
    // For the transition period, we'll use the existing renderer
    // This will be replaced with proper MDX compilation
    const preprocessed = preprocessContent(content);
    let html = preprocessed;

    // Convert variables
    html = convertVariablesToComponentsSync(html);

    return html;
}
