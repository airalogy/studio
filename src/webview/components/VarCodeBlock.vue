<template>
  <div class="var-code-block" :class="{ 'has-content': hasContent }">
    <div class="code-header">
      <span class="lang-tag">{{ language }}</span>
      <div class="actions">
        <button class="action-btn" @click="handleEdit" title="Open in Editor">
          <i class="codicon codicon-edit"></i>
          Edit
        </button>
      </div>
    </div>
    
    <div class="code-content">
      <div v-if="renderedHtml" v-html="renderedHtml" class="shiki-container"></div>
      <pre v-else><code>{{ displayContent }}</code></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  name: string;
  varType: string;
  language: string;
  // Content props
  defaultValue?: string;
  calculatedValue?: string;
  renderedHtml?: string;
}>();

const vscode = (window as any).vscode;

const displayContent = computed(() => {
  return props.calculatedValue || props.defaultValue || '';
});

const hasContent = computed(() => {
  return !!displayContent.value;
});

const handleEdit = () => {
  vscode.postMessage({
    type: 'nav:open-resource',
    payload: {
      resourceId: props.name,
      contentType: 'code',
      content: displayContent.value,
      language: props.language
    }
  });
};
</script>

<style scoped>
.var-code-block {
  margin: 8px 0;
  border: 1px solid var(--vscode-widget-border);
  border-radius: 6px;
  background: var(--vscode-editor-background);
  overflow: hidden;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: var(--vscode-editor-lineHighlightBackground);
  border-bottom: 1px solid var(--vscode-widget-border);
  font-size: 11px;
}

.lang-tag {
  color: var(--vscode-descriptionForeground);
  text-transform: uppercase;
  font-weight: 600;
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

.code-content {
  padding: 8px;
  overflow-x: auto;
  font-family: var(--vscode-editor-font-family);
  font-size: var(--vscode-editor-font-size);
  line-height: var(--vscode-editor-line-height);
}

.shiki-container :deep(pre) {
  margin: 0;
  background: transparent !important; /* Shiki hardcodes bg, rely on container */
  padding: 0;
}
</style>
