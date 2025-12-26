<template>
  <div class="var-markdown-preview" @click="handleClick">
    <div class="markdown-header">
      <span class="header-label">MARKDOWN</span>
      <div class="header-actions">
        <!-- Manual Assigner Trigger Button -->
        <button 
          v-if="hasManualAssigner" 
          class="action-btn trigger-btn" 
          @click.stop="handleTrigger" 
          :title="`手动计算${parsedDeps.length > 0 ? ' (依赖: ' + parsedDeps.join(', ') + ')' : ''}`"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
            <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <button class="action-btn" @click="handleEditSource" title="Edit Source">
          <i class="codicon codicon-edit"></i>
          Source
        </button>
      </div>
    </div>
    
    <div class="markdown-body" v-if="displayHtml" v-html="displayHtml"></div>
    <div class="markdown-body empty" v-else>
      <em>No content</em>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { marked } from 'marked';

const props = defineProps<{
  name: string;
  varType: string;
  // Content props
  defaultValue?: string;
  calculatedValue?: string;
  renderedHtml?: string;
  // Assigner support
  assignerMode?: string;
  assignerReadonly?: string;
  assignerDeps?: string; // JSON array of dependent field names
}>();

const vscode = (window as any).vscode;

const sourceContent = computed(() => {
  return props.calculatedValue || props.defaultValue || '';
});

// Render markdown on client if server didn't provide it
const displayHtml = computed(() => {
  if (props.renderedHtml) return props.renderedHtml;
  if (!sourceContent.value) return '';
  try {
    return marked.parse(sourceContent.value);
  } catch (e) {
    console.error('Markdown parse error:', e);
    return sourceContent.value;
  }
});

const handleEditSource = () => {
  vscode.postMessage({
    type: 'nav:open-resource',
    payload: {
      resourceId: props.name,
      contentType: 'markdown',
      content: sourceContent.value
    }
  });
};

const handleClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  // Check if clicked element is a Magic Link
  if (target.matches('a.record-link') || target.closest('a.record-link')) {
    const link = target.matches('a.record-link') ? target : target.closest('a.record-link') as HTMLElement;
    const recordId = link.getAttribute('data-record-id');
    
    if (recordId) {
      e.preventDefault();
      vscode.postMessage({
        type: 'nav:reveal-record',
        payload: {
          recordId: recordId
        }
      });
    }
  }
};

// Check if this field has a manual assigner mode
const hasManualAssigner = computed(() => {
  return props.assignerMode === 'manual' || 
         props.assignerMode === 'auto_first' || 
         props.assignerMode === 'manual_readonly';
});

// Parse dependent fields from JSON prop
const parsedDeps = computed(() => {
  if (!props.assignerDeps) return [];
  try {
    const result = JSON.parse(props.assignerDeps);
    return Array.isArray(result) ? result : [];
  } catch {
    return [];
  }
});

// Handle manual trigger - dispatch CustomEvent for parent to catch
function handleTrigger() {
  const event = new CustomEvent('trigger-assigner', {
    bubbles: true,
    composed: true,
    detail: { fieldName: props.name }
  });
  const hostElement = document.querySelector(`var-markdown-preview[name="${props.name}"]`);
  if (hostElement) {
    hostElement.dispatchEvent(event);
  }
}
</script>

<style scoped>
.var-markdown-preview {
  margin: 12px 0;
  border: 1px solid var(--vscode-widget-border);
  border-radius: 6px;
  background: var(--vscode-editor-background);
  overflow: hidden;
}

.markdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  border-bottom: 1px solid var(--vscode-widget-border);
  background: var(--vscode-editor-lineHighlightBackground);
}

.header-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.trigger-btn {
  background: none;
  border: 1px solid var(--vscode-textLink-foreground);
  color: var(--vscode-textLink-foreground);
  padding: 2px 6px;
}

.trigger-btn:hover {
  background: var(--vscode-textLink-foreground);
  color: var(--vscode-button-foreground);
}

.header-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--vscode-descriptionForeground);
  letter-spacing: 0.5px;
}

.action-btn {
  background: none;
  border: none;
  color: var(--vscode-button-foreground);
  background-color: var(--vscode-button-background);
  padding: 2px 8px;
  border-radius: 3px;
  cursor: pointer;
  display: flex;
  gap: 4px;
  align-items: center;
  font-size: 11px;
}

.action-btn:hover {
  background-color: var(--vscode-button-hoverBackground);
}

.markdown-body {
  padding: 16px;
  font-family: var(--vscode-font-family);
  font-size: var(--vscode-font-size);
  color: var(--vscode-editor-foreground);
  line-height: 1.6;
}

.markdown-body.empty {
  color: var(--vscode-disabledForeground);
  font-style: italic;
  padding: 8px;
}

/* Basic Markdown Styles matching VS Code */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  border-bottom: 1px solid var(--vscode-widget-border);
  padding-bottom: 0.3em;
  margin-top: 1.5em;
  margin-bottom: 16px;
}

.markdown-body :deep(a) {
  color: var(--vscode-textLink-foreground);
  text-decoration: none;
}

.markdown-body :deep(a):hover {
  text-decoration: underline;
}

.markdown-body :deep(code) {
  font-family: var(--vscode-editor-font-family);
  background-color: var(--vscode-textCodeBlock-background);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 85%;
}

.markdown-body :deep(pre) {
  background-color: var(--vscode-textCodeBlock-background);
  padding: 16px;
  overflow: auto;
  border-radius: 6px;
}

.markdown-body :deep(blockquote) {
  margin: 0;
  padding: 0 1em;
  color: var(--vscode-descriptionForeground);
  border-left: 0.25em solid var(--vscode-widget-border);
}

.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 4px;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
}

.markdown-body :deep(th), 
.markdown-body :deep(td) {
  border: 1px solid var(--vscode-widget-border);
  padding: 6px 13px;
}
</style>
