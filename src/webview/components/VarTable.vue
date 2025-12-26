<template>
  <div 
    class="aimd-var-table-wrapper"
    :data-variable-name="name"
    :data-column-count="parsedColumns.length"
    :data-density="density"
  >
    <!-- Header Bar -->
    <div class="aimd-table-header-bar" :class="{ 'is-readonly': assignerReadonly === 'true' }">
      <div class="aimd-table-title">
        <span class="codicon codicon-table"></span>
        <span>{{ displayName }}</span>
        <span v-if="assignerReadonly === 'true'" class="aimd-table-lock" title="只读（由 Assigner 计算）">🔒</span>
      </div>
      <div class="aimd-table-header-right">
        <span v-if="assignerMode" class="aimd-table-mode">{{ modeLabel }}</span>
        <span v-if="hasManualAssigner" class="aimd-table-trigger-wrapper">
          <span class="aimd-table-trigger" @click="handleTrigger" :title="triggerTooltip">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </span>
          <span v-if="parsedDeps.length > 0" class="aimd-table-deps-badge" :title="depsTooltip">{{ parsedDeps.length }}</span>
        </span>
        <span v-if="rows.length > 0" class="aimd-table-status">
          {{ rows.length }} ROWS
        </span>
      </div>
    </div>

    <!-- Desktop Table View -->
    <div class="aimd-var-table-container custom-scrollbar aimd-desktop-view">
      <table class="aimd-var-table">
        <thead>
          <tr>
            <th v-for="(col, index) in parsedColumns" :key="col.id" 
                class="aimd-table-th" 
                :class="{ 'aimd-sticky-col': index === 0 }">
              <div class="aimd-th-content" :title="col.description || col.id">
                <span class="aimd-th-text">{{ getHeaderDisplay(col) }}</span>
                <span v-if="currentViewMode === 'value' || currentViewMode === 'title'" class="aimd-th-type">{{ col.type }}</span>
              </div>
            </th>
            <th class="aimd-table-th aimd-table-actions-th"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in rows" :key="rowIndex" class="aimd-var-table-row">
            <td v-for="(col, colIndex) in parsedColumns" :key="col.id"
                class="aimd-table-td"
                :class="{ 'aimd-sticky-col': colIndex === 0 }"
                :data-col-title="col.title">
              
              <input
                type="text"
                class="aimd-cell-input"
                :class="{ 'aimd-cell-input-primary': colIndex === 0 }"
                :data-variable-name="`${name}.${col.id}`"
                :data-var-id="col.id"
                :data-var-title="col.title"
                :data-var-type="col.type"
                :data-default-value="col.default"
                :placeholder="col.title"
                :value="getCellValue(row, col)"
                @input="updateCell(rowIndex, col.id, $event)"
                readonly
              />
            </td>
            <td class="aimd-table-td aimd-table-actions-td">
              <button class="aimd-row-delete-btn" @click="deleteRow(rowIndex)" title="Delete Row">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile Card View -->
    <div class="aimd-mobile-cards-view custom-scrollbar">
      <div v-for="(row, rowIndex) in rows" :key="rowIndex" class="aimd-card">
        <!-- Card Header -->
        <div class="aimd-card-header">
          <div class="aimd-card-title-group">
            <div class="aimd-card-main-title">
              {{ parsedColumns.length > 0 ? getCellValue(row, parsedColumns[0]) : 'Item ' + (rowIndex + 1) }}
            </div>
            <div class="aimd-card-subtitle" v-if="parsedColumns.length > 0">
              {{ parsedColumns[0].title }} <span class="aimd-card-type-badge">{{ parsedColumns[0].type }}</span>
            </div>
          </div>
          <button class="aimd-card-delete-btn" @click="deleteRow(rowIndex)" title="Delete Item">
            <span class="codicon codicon-trash"></span> Remove
          </button>
        </div>

        <!-- Card Body (Grid) -->
        <div class="aimd-card-body">
          <div v-for="(col, colIndex) in parsedColumns.slice(1)" :key="col.id" class="aimd-card-field">
            <div class="aimd-card-label" :title="col.description">{{ col.title }}</div>
            <div class="aimd-card-input-wrapper">
              <input
                type="text"
                class="aimd-card-input"
                :value="getCellValue(row, col)"
                @input="updateCell(rowIndex, col.id, $event)"
                readonly
              />
              <span class="aimd-card-type-hint">{{ col.type }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Bar -->
    <div class="aimd-table-footer-bar">
      <div class="aimd-table-meta">{{ rows.length }} Row{{ rows.length !== 1 ? 's' : '' }}</div>
      <div class="aimd-table-actions">
        <button class="aimd-btn-icon" @click="addRow" title="Add Row">+ Add Row</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

interface TableColumn {
  id: string;
  title: string;
  type: string;
  default: string;
  description?: string;
}

// Props definition
// We need to support String for columns because passing it as an attribute via custom element results in a string.
const props = defineProps<{
  name: string;
  title?: string;
  columns?: TableColumn[] | string;
  viewMode?: string;
  initialRows?: string;
  assignerMode?: string;
  assignerReadonly?: string;
  isCalculated?: string;
  assignerDeps?: string;  // JSON array of dependent field names
}>();

const emit = defineEmits<{
  (e: 'trigger-assigner', fieldName: string): void;
}>();

// Check if this table has a manual assigner mode
const hasManualAssigner = computed(() => {
  return props.assignerMode === 'manual' || 
         props.assignerMode === 'auto_first' || 
         props.assignerMode === 'manual_readonly';
});

// Mode label for header
const modeLabel = computed(() => {
  switch (props.assignerMode) {
    case 'auto': return '自动';
    case 'manual': return '手动';
    case 'auto_first': return '首次自动';
    case 'auto_readonly': return '自动(只读)';
    case 'manual_readonly': return '手动(只读)';
    default: return '';
  }
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

// Maximum deps to show in tooltip before truncation
const MAX_DEPS_DISPLAY = 5;

// Trigger button tooltip
const triggerTooltip = computed(() => {
  if (parsedDeps.value.length === 0) return '手动计算';
  const deps = parsedDeps.value.slice(0, MAX_DEPS_DISPLAY);
  const remaining = parsedDeps.value.length - MAX_DEPS_DISPLAY;
  let tooltip = `基于: ${deps.join(', ')}`;
  if (remaining > 0) tooltip += ` +${remaining}更多`;
  return tooltip;
});

// Dependencies tooltip for badge
const depsTooltip = computed(() => {
  const deps = parsedDeps.value;
  if (deps.length <= MAX_DEPS_DISPLAY) return `依赖变量: ${deps.join(', ')}`;
  const shown = deps.slice(0, MAX_DEPS_DISPLAY);
  return `依赖变量: ${shown.join(', ')} +${deps.length - MAX_DEPS_DISPLAY}更多`;
});

// Handle manual trigger - dispatch CustomEvent for parent to catch
function handleTrigger() {
  // Vue emit doesn't work across Custom Element boundary
  // So we need to dispatch a native CustomEvent
  const event = new CustomEvent('trigger-assigner', {
    bubbles: true,     // Allow event to bubble up
    composed: true,    // Allow crossing Shadow DOM boundary
    detail: { fieldName: props.name }
  });
  // Get the host element (the custom element itself)
  const hostElement = document.querySelector(`var-table[name="${props.name}"]`);
  if (hostElement) {
    hostElement.dispatchEvent(event);
  }
}

// Debug logging
onMounted(() => {
  console.log('[VarTable] Mounted with props:', {
    name: props.name,
    assignerMode: props.assignerMode,
    assignerReadonly: props.assignerReadonly,
    isCalculated: props.isCalculated,
    hasManualAssigner: hasManualAssigner.value
  });
});

// Normalize columns from possible JSON string
const parsedColumns = computed<TableColumn[]>(() => {
  if (!props.columns) return [];
  if (Array.isArray(props.columns)) return props.columns;
  if (typeof props.columns === 'string') {
    try {
      return JSON.parse(props.columns);
    } catch (e) {
      console.error('Failed to parse columns JSON:', e);
      return [];
    }
  }
  return [];
});

const currentViewMode = computed(() => props.viewMode || 'value');

const getHeaderDisplay = (col: TableColumn) => {
  if (currentViewMode.value === 'id') return col.id;
  if (currentViewMode.value === 'type') return col.type;
  return col.title || col.id;
};

const getCellValue = (row: Record<string, string>, col: TableColumn) => {
  if (currentViewMode.value === 'id') return col.id;
  if (currentViewMode.value === 'type') return col.type;
  // In 'title' or 'value' view mode, we show the actual value (or default)
  return row[col.id] || col.default;
};

const displayName = computed(() => {
  if (props.title) return props.title;
  return props.name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
});

const density = computed(() => parsedColumns.value.length > 3 ? 'compact' : 'normal');

// Parse initial rows from prop or use empty row
const parseInitialRows = () => {
  if (props.initialRows) {
    try {
      const parsed = JSON.parse(props.initialRows);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    } catch (e) {
      console.error('Failed to parse initialRows:', e);
    }
  }
  return [{}]; // Default to one empty row
};

const rows = ref<Record<string, string>[]>(parseInitialRows());

function addRow() {
  rows.value.push({});
}

function deleteRow(index: number) {
  if (rows.value.length > 1) {
    rows.value.splice(index, 1);
  }
}

function updateCell(rowIndex: number, colId: string, event: Event) {
  const target = event.target as HTMLInputElement;
  rows.value[rowIndex][colId] = target.value;
}
</script>

<style scoped>
.aimd-var-table-wrapper {
  margin: 1.5em 0;
  background: var(--aimd-bg-secondary);
  border: 1px solid var(--aimd-border-light);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.aimd-table-header-bar {
  height: 40px;
  background: var(--aimd-bg-tertiary);
  border-bottom: 1px solid var(--aimd-border-light);
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
  flex-shrink: 0;
}

.aimd-table-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--aimd-text-primary);
}

.aimd-table-status {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--aimd-text-tertiary);
  background: var(--aimd-bg-primary);
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid var(--aimd-border-light);
}

.aimd-table-header-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

.aimd-table-mode {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--aimd-text-tertiary);
  padding: 2px 6px;
  background: var(--aimd-bg-primary);
  border-radius: 3px;
  border: 1px solid var(--aimd-border-light);
}

.aimd-table-lock {
  font-size: 11px;
  opacity: 0.7;
}

.aimd-table-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 4px;
  background: var(--aimd-bg-primary);
  border: 1px solid var(--aimd-border-light);
  border-radius: 3px;
  cursor: pointer;
  color: var(--aimd-text-tertiary);
  transition: all 0.15s ease;
}

.aimd-table-trigger:hover {
  background: var(--aimd-bg-secondary);
  border-color: var(--aimd-text-tertiary);
  color: var(--aimd-text-secondary);
}

.aimd-table-trigger svg {
  width: 14px;
  height: 14px;
}

.aimd-table-header-bar.is-readonly {
  background: var(--aimd-bg-secondary);
}

.aimd-table-header-bar.is-readonly .aimd-table-title {
  color: var(--aimd-text-tertiary);
}

.aimd-table-trigger-wrapper {
  display: flex;
  align-items: center;
  position: relative;
}

.aimd-table-deps-badge {
  position: absolute;
  top: -4px;
  right: -6px;
  min-width: 14px;
  height: 14px;
  padding: 0 3px;
  font-size: 9px;
  font-weight: 600;
  color: white;
  background: var(--aimd-text-tertiary, #94a3b8);
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: help;
}

.aimd-table-deps-badge:hover {
  background: var(--aimd-text-secondary, #64748b);
}

.aimd-var-table-container {
  flex: 1;
  overflow: auto;
  position: relative;
  max-height: 400px;
  background: var(--aimd-bg-primary);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: var(--aimd-bg-secondary);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--aimd-border-subtle);
  border: 2px solid var(--aimd-bg-secondary);
  border-radius: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: var(--aimd-slate-400);
}

.aimd-var-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 600px;
}

.aimd-var-table thead {
  position: sticky;
  top: 0;
  z-index: 2;
}

.aimd-table-th {
  text-align: left;
  padding: 0;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--aimd-text-secondary);
  border-bottom: 1px solid var(--aimd-border-medium);
  background: var(--aimd-bg-secondary);
  vertical-align: middle;
  height: 38px;
  white-space: nowrap;
}

/* Removed redundant body.vscode-dark .aimd-table-th rule */

.aimd-th-content {
  padding: 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.aimd-th-text {
  flex: 1;
}

.aimd-th-type {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
  opacity: 0.5;
  font-weight: 400;
}

.aimd-table-td {
  padding: 0;
  background: transparent;
  border-bottom: 1px solid var(--aimd-border-subtle);
  vertical-align: middle;
  height: 36px;
}

/* Removed body.vscode-dark .aimd-table-td rule */

.aimd-var-table-row:nth-child(even) .aimd-table-td {
  background-color: rgba(0, 0, 0, 0.01);
}

/* Removed body.vscode-dark .aimd-var-table-row:nth-child(even) rule, opacity based bg should work in dark mode mostly or we can use vars. 
   Ideally use a transparent white for dark mode if using opacity. Let's make it simple: */
body.vscode-dark .aimd-var-table-row:nth-child(even) .aimd-table-td {
  background-color: rgba(255, 255, 255, 0.02);
}

.aimd-var-table-row:hover .aimd-table-td,
.aimd-var-table-row:hover .aimd-sticky-col {
  background-color: rgba(21, 128, 61, 0.08) !important;
}

.aimd-sticky-col {
  position: sticky;
  left: 0;
  z-index: 1;
}

.aimd-table-th.aimd-sticky-col {
  z-index: 3;
}

.aimd-cell-input {
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  padding: 0 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--aimd-text-primary);
  outline: none;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}

.aimd-cell-input:focus {
  background: var(--aimd-bg-page);
  box-shadow: inset 0 0 0 2px var(--aimd-status-success-icon);
  cursor: text;
}

.aimd-cell-input-primary {
  font-weight: 700;
  color: var(--aimd-brand-primary);
}

/* Removed body.vscode-dark .aimd-cell-input-primary rule */

.aimd-table-actions-th {
  width: 32px;
  min-width: 32px;
}

.aimd-table-actions-td {
  width: 32px;
  text-align: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.aimd-var-table-row:hover .aimd-table-actions-td {
  opacity: 1;
}

.aimd-row-delete-btn {
  color: var(--vscode-descriptionForeground);
  padding: 4px;
  border-radius: 4px;
  background: transparent;
  border: none;
  cursor: pointer;
}

.aimd-row-delete-btn:hover {
  background-color: var(--vscode-button-secondaryHoverBackground);
  color: var(--vscode-errorForeground);
}

.aimd-table-footer-bar {
  height: 32px;
  border-top: 1px solid var(--aimd-border-light);
  background: var(--aimd-bg-tertiary);
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 16px;
  font-size: 11px;
  color: var(--aimd-text-tertiary);
}

.aimd-table-meta {
  font-family: 'JetBrains Mono', monospace;
}

.aimd-table-actions {
  margin-left: auto;
}

.aimd-btn-icon {
  background: transparent;
  border: none;
  color: var(--aimd-brand-secondary);
  font-weight: 600;
  font-size: 11px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.aimd-btn-icon:hover {
  background: var(--aimd-status-info-bg);
  color: var(--aimd-brand-secondary);
}

/* Mobile Cards View - Default Hidden */
.aimd-mobile-cards-view {
  display: none;
}

/* ==========================================================================
   THEME: MODERN
   ========================================================================== */
/* Dark Mode Overrides for Modern now handled largely by vars, removing hardcoded */
/* Retaining minimal overrides if structure demands it, but standardizing on vars */
:host([data-design-theme="modern"]) .aimd-var-table-wrapper {
  background: var(--aimd-bg-secondary);
  border-color: var(--aimd-border-light);
}

/* ==========================================================================
   THEME: ELSEVIER (Journal)
   ========================================================================== */
:host([data-design-theme="elsevier"]) .aimd-var-table-wrapper {
  border: none;
  border-top: 2px solid var(--aimd-text-primary);
  border-bottom: 2px solid var(--aimd-text-primary);
  border-radius: 0;
  box-shadow: none;
  background: transparent;
}

:host([data-design-theme="elsevier"]) .aimd-table-header-bar {
  background: transparent;
  border-bottom: 1px solid var(--aimd-border-light);
}

:host([data-design-theme="elsevier"]) .aimd-table-title {
  font-family: "Georgia", serif;
  font-size: 14px;
  color: var(--aimd-text-primary);
}

:host([data-design-theme="elsevier"]) .aimd-table-th {
  background: transparent;
  border-bottom: 2px solid var(--aimd-border-light);
  color: var(--aimd-text-primary);
  font-weight: 600;
  font-family: "Georgia", serif;
  text-transform: none;
  letter-spacing: normal;
}

:host([data-design-theme="elsevier"]) .aimd-table-td {
  border-bottom: 1px solid var(--aimd-border-subtle);
}

:host([data-design-theme="elsevier"]) .aimd-table-footer-bar {
  background: transparent;
  border-top: 1px solid var(--aimd-border-light);
}

/* ==========================================================================
   THEME: CLINICAL (High Contrast)
   ========================================================================== */
:host([data-design-theme="clinical"]) .aimd-var-table-wrapper {
  border: 1px solid var(--aimd-border-strong);
  border-radius: 0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  background: var(--aimd-bg-primary);
}

:host([data-design-theme="clinical"]) .aimd-table-header-bar {
  background: var(--aimd-pre-bg); /* Use dark bg */
  color: var(--aimd-pre-text);
}

:host([data-design-theme="clinical"]) .aimd-table-title {
  color: var(--aimd-pre-text);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

:host([data-design-theme="clinical"]) .aimd-table-th {
  background: var(--aimd-bg-tertiary);
  border-bottom: 2px solid var(--aimd-border-medium);
  color: var(--aimd-text-primary);
  font-weight: 800;
}

:host([data-design-theme="clinical"]) .aimd-table-td {
  border-bottom: 1px solid var(--aimd-border-medium);
}

:host([data-design-theme="clinical"]) .aimd-var-table-row:nth-child(even) .aimd-table-td {
  background-color: var(--aimd-bg-secondary);
}

/* ==========================================================================
   THEME: WESTLAKE (Swedish Minimalism)
   ========================================================================== */
:host([data-design-theme="westlake"]) .aimd-var-table-wrapper {
  border: none;
  border-top: 2px solid var(--aimd-westlake-primary, #00498F);
  border-bottom: 1px solid var(--aimd-border-light);
  border-radius: 0;
  box-shadow: none;
  background: transparent;
}

:host([data-design-theme="westlake"]) .aimd-table-header-bar {
  background: transparent;
  border-bottom: none;
  padding: 12px 0;
}

:host([data-design-theme="westlake"]) .aimd-table-title {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 14px;
  color: var(--aimd-westlake-primary, #00498F);
  letter-spacing: 0.02em;
}

:host([data-design-theme="westlake"]) .aimd-table-th {
  background: transparent;
  border-bottom: 2px solid var(--aimd-westlake-primary, #00498F);
  color: var(--aimd-text-primary);
  font-weight: 600;
  font-family: 'Inter', sans-serif;
  text-transform: none;
  letter-spacing: normal;
}

:host([data-design-theme="westlake"]) .aimd-table-td {
  border-bottom: 1px solid var(--aimd-border-subtle);
}

:host([data-design-theme="westlake"]) .aimd-table-footer-bar {
  background: transparent;
  border-top: 1px solid var(--aimd-border-light);
}

:host([data-design-theme="westlake"]) .aimd-btn-icon {
  color: var(--aimd-westlake-primary, #00498F);
}

:host([data-design-theme="westlake"]) .aimd-btn-icon:hover {
  background: rgba(0, 73, 143, 0.06);
  color: var(--aimd-westlake-accent, #F18B1C);
}

/* Responsive Card Mode */
@media (max-width: 480px) {
  .aimd-var-table-wrapper {
    background: transparent;
    border: none;
    box-shadow: none;
    margin: 1em -8px;
  }

  /* Hide Desktop Table */
  .aimd-desktop-view {
    display: none;
  }

  /* Show Mobile Cards */
  .aimd-mobile-cards-view {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 4px;
  }

  .aimd-card {
    background: var(--aimd-bg-primary);
    border: 1px solid var(--aimd-border-light);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }

  /* Card Header */
  .aimd-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .aimd-card-title-group {
    flex: 1;
    min-width: 0;
    padding-right: 12px;
  }

  .aimd-card-main-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--aimd-text-primary);
    margin-bottom: 2px;
    word-break: break-word;
  }

  .aimd-card-subtitle {
    font-size: 11px;
    color: var(--aimd-text-tertiary);
    font-family: 'JetBrains Mono', monospace;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
  }

  .aimd-card-type-badge {
    background: var(--aimd-bg-tertiary);
    border: 1px solid var(--aimd-border-subtle);
    border-radius: 3px;
    padding: 1px 4px;
    font-size: 9px;
    opacity: 0.8;
  }

  .aimd-card-delete-btn {
    background: rgba(220, 38, 38, 0.1);
    color: #ef4444;
    border: 1px solid rgba(220, 38, 38, 0.2);
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
    transition: all 0.2s;
  }
  
  .aimd-card-delete-btn:hover {
    background: rgba(220, 38, 38, 0.15);
    border-color: rgba(220, 38, 38, 0.3);
  }

  /* Grid Body for Fields */
  .aimd-card-body {
    background: rgba(0, 0, 0, 0.03); 
    border: 1px solid var(--aimd-border-subtle);
    border-radius: 6px;
    padding: 10px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  body.vscode-dark .aimd-card-body {
    background: rgba(255, 255, 255, 0.03);
  }

  .aimd-card-field {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .aimd-card-label {
    font-size: 10px;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: var(--aimd-text-tertiary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .aimd-card-input-wrapper {
    display: flex;
    align-items: baseline;
    gap: 4px;
  }

  .aimd-card-input {
    flex: 1;
    min-width: 0;
    background: transparent;
    border: none;
    border-bottom: 1px solid transparent;
    padding: 2px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: var(--aimd-text-secondary);
    outline: none;
    transition: border-color 0.2s;
  }

  .aimd-card-input:focus {
    border-bottom-color: var(--aimd-status-success-icon);
    color: var(--aimd-text-primary);
  }

  .aimd-card-type-hint {
    font-size: 9px;
    color: var(--aimd-text-quaternary);
    font-family: 'JetBrains Mono', monospace;
  }
}
</style>
