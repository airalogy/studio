<template>
  <div :class="['aimd-callout', `aimd-callout-${type}`]">
    <div class="callout-header">
      <span class="callout-icon">{{ iconMap[type] || '📌' }}</span>
      <span class="callout-title">{{ titleMap[type] || type.toUpperCase() }}</span>
    </div>
    <div class="callout-body">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  type?: 'note' | 'tip' | 'warning' | 'caution' | 'important' | 'example' | 'abstract' | 'info' | 'success' | 'danger' | 'bug' | 'quote';
}

withDefaults(defineProps<Props>(), {
  type: 'note'
});

const iconMap: Record<string, string> = {
  note: '📝',
  tip: '💡',
  warning: '⚠️',
  caution: '🛑',
  important: '❗',
  example: '🔬',
  abstract: '📋',
  info: 'ℹ️',
  success: '✅',
  danger: '⚡',
  bug: '🐛',
  quote: '💬'
};

const titleMap: Record<string, string> = {
  note: 'Note',
  tip: 'Tip',
  warning: 'Warning',
  caution: 'Caution',
  important: 'Important',
  example: 'Example',
  abstract: 'Abstract',
  info: 'Info',
  success: 'Success',
  danger: 'Danger',
  bug: 'Known Issue',
  quote: 'Quote'
};
</script>

<style scoped>
.aimd-callout {
  margin: 1.5em 0;
  position: relative;
  font-size: 0.9em;
  line-height: 1.6;
}

.callout-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.callout-icon {
  font-size: 1.1em;
  line-height: 1;
}

.callout-title {
  font-weight: 600;
  font-size: 0.9em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.callout-body :deep(p) { margin: 0.5em 0; }
.callout-body :deep(p:first-child) { margin-top: 0; }
.callout-body :deep(p:last-child) { margin-bottom: 0; }

/* ==========================================================================
   THEME: MODERN (Modern LIMS) - Default
   Soft, rounded, desaturated colors, Notion-like
   ========================================================================== */
:host([data-design-theme="modern"]) .aimd-callout {
  padding: 12px 16px;
  border-radius: 6px;
  border: 1px solid;
}

:host([data-design-theme="modern"]) .aimd-callout-note {
  background-color: var(--aimd-bg-secondary); border-color: var(--aimd-border-light); border-left: 4px solid var(--aimd-text-secondary); color: var(--aimd-text-secondary);
}
:host([data-design-theme="modern"]) .aimd-callout-tip {
  background-color: var(--aimd-status-success-bg); border-color: var(--aimd-status-success-border); border-left: 4px solid var(--aimd-status-success-icon); color: var(--aimd-status-success-text);
}
:host([data-design-theme="modern"]) .aimd-callout-warning {
  background-color: var(--aimd-status-warning-bg); border-color: var(--aimd-status-warning-border); border-left: 4px solid var(--aimd-status-warning-icon); color: var(--aimd-status-warning-text);
}
:host([data-design-theme="modern"]) .aimd-callout-danger {
  background-color: var(--aimd-status-error-bg); border-color: var(--aimd-status-error-border); border-left: 4px solid var(--aimd-status-error-icon); color: var(--aimd-status-error-text);
}
:host([data-design-theme="modern"]) .aimd-callout-example {
  background-color: var(--aimd-status-info-bg); border-color: var(--aimd-status-info-border); border-left: 4px solid var(--aimd-status-info-icon); color: var(--aimd-status-info-text);
}
:host([data-design-theme="modern"]) .aimd-callout-abstract {
  background-color: var(--aimd-status-info-bg); border-color: var(--aimd-status-info-border); border-left: 4px solid var(--aimd-status-info-icon); color: var(--aimd-status-info-text);
}

/* ==========================================================================
   THEME: ELSEVIER (Journal Style)
   Minimal ink, serif fonts, professional, borders
   ========================================================================== */
:host([data-design-theme="elsevier"]) .aimd-callout {
  padding: 16px 0;
  border-top: 1px solid var(--aimd-border-light);
  border-bottom: 1px solid var(--aimd-border-light);
  border-radius: 0;
  margin: 2em 0;
}

:host([data-design-theme="elsevier"]) .callout-header {
  font-family: "Georgia", serif;
  margin-bottom: 4px;
}

:host([data-design-theme="elsevier"]) .callout-icon {
  display: none; /* Icons hidden in journal style */
}

:host([data-design-theme="elsevier"]) .callout-title {
  color: var(--aimd-text-primary);
  font-size: 1em;
  text-transform: none; /* Use regular capitalization */
  font-style: italic;
}

/* Abstract Special Case */
:host([data-design-theme="elsevier"]) .aimd-callout-abstract {
  background-color: var(--aimd-bg-secondary);
  border: none;
  padding: 24px;
  font-family: "Georgia", serif;
  font-style: italic;
  color: var(--aimd-text-secondary);
}

/* Other types: Simple left borders */
:host([data-design-theme="elsevier"]) .aimd-callout-note,
:host([data-design-theme="elsevier"]) .aimd-callout-example,
:host([data-design-theme="elsevier"]) .aimd-callout-tip {
  border-top: 0;
  border-bottom: 0;
  border-left: 4px solid var(--aimd-border-medium);
  padding-left: 16px;
  padding-top: 0;
  padding-bottom: 0;
  color: var(--aimd-text-secondary);
}

:host([data-design-theme="elsevier"]) .aimd-callout-warning {
  border-top: 0;
  border-bottom: 0;
  border-left: 4px solid var(--aimd-status-warning-icon);
  padding-left: 16px;
  color: var(--aimd-text-secondary);
}

:host([data-design-theme="elsevier"]) .aimd-callout-danger {
  border: 2px solid var(--aimd-status-error-border);
  background-color: var(--aimd-status-error-bg);
  padding: 16px;
  color: var(--aimd-status-error-text);
}

/* ==========================================================================
   THEME: CLINICAL (Clinical Clean)
   High contrast, sterile, thick status stripes
   ========================================================================== */
:host([data-design-theme="clinical"]) .aimd-callout {
  padding: 12px 16px;
  background-color: var(--aimd-bg-primary);
  border: 1px solid var(--aimd-border-medium);
  border-left-width: 6px; /* Thick status stripe */
  border-radius: 0;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  color: var(--aimd-text-secondary);
}

:host([data-design-theme="clinical"]) .callout-title {
  color: var(--aimd-text-primary);
  font-weight: 700;
}

:host([data-design-theme="clinical"]) .aimd-callout-note { border-left-color: var(--aimd-border-strong); }
:host([data-design-theme="clinical"]) .aimd-callout-tip { border-left-color: var(--aimd-status-success-icon); }
:host([data-design-theme="clinical"]) .aimd-callout-warning { border-left-color: var(--aimd-status-warning-icon); }
:host([data-design-theme="clinical"]) .aimd-callout-example { border-left-color: var(--aimd-border-strong); }
:host([data-design-theme="clinical"]) .aimd-callout-abstract { border-left-color: var(--aimd-text-primary); }

/* Danger gets full red border */
:host([data-design-theme="clinical"]) .aimd-callout-danger {
  border: 2px solid var(--aimd-status-error-icon);
  color: var(--aimd-status-error-text);
}
:host([data-design-theme="clinical"]) .aimd-callout-danger .callout-title {
  color: var(--aimd-status-error-text);
  text-decoration: underline;
}

/* ==========================================================================
   THEME: WESTLAKE (Swedish Minimalism)
   Clean, elegant, restrained
   ========================================================================== */
:host([data-design-theme="westlake"]) .aimd-callout {
  padding: 16px 20px;
  background: transparent;
  border: none;
  border-left: 3px solid var(--aimd-westlake-primary, #00498F);
  border-radius: 0;
  margin: 1.5em 0;
}

:host([data-design-theme="westlake"]) .callout-header {
  margin-bottom: 10px;
}

:host([data-design-theme="westlake"]) .callout-icon {
  display: none; /* Icons hidden in minimal style */
}

:host([data-design-theme="westlake"]) .callout-title {
  color: var(--aimd-westlake-primary, #00498F);
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 0.85em;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

:host([data-design-theme="westlake"]) .aimd-callout-note,
:host([data-design-theme="westlake"]) .aimd-callout-tip,
:host([data-design-theme="westlake"]) .aimd-callout-example {
  border-left-color: var(--aimd-westlake-primary, #00498F);
  color: var(--aimd-text-secondary);
}

:host([data-design-theme="westlake"]) .aimd-callout-warning {
  border-left-color: var(--aimd-westlake-accent, #F18B1C);
}

:host([data-design-theme="westlake"]) .aimd-callout-warning .callout-title {
  color: var(--aimd-westlake-accent, #F18B1C);
}

:host([data-design-theme="westlake"]) .aimd-callout-danger {
  border-left-color: var(--aimd-status-error-icon);
  background-color: var(--aimd-status-error-bg);
}

:host([data-design-theme="westlake"]) .aimd-callout-danger .callout-title {
  color: var(--aimd-status-error-text);
}

:host([data-design-theme="westlake"]) .aimd-callout-abstract {
  background-color: rgba(0, 73, 143, 0.03);
  padding: 20px 24px;
  font-style: italic;
  color: var(--aimd-text-secondary);
}
</style>

