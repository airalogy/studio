<template>
  <span 
    class="aimd-var-wrapper" 
    :class="{
      'aimd-var-readonly': assignerReadonly === 'true',
      'aimd-var-has-assigner': hasManualAssigner
    }"
    @mouseenter="showTooltip" 
    @mouseleave="hideTooltip"
  >
    <input
      :type="inputType"
      class="aimd-var-input"
      :class="{ 
        'aimd-var-input-calculated': calculatedValue,
        'aimd-var-input-readonly': assignerReadonly === 'true',
        'aimd-var-input-secret': isSecret
      }"
      :data-variable-name="name"
      :data-variable-type="variableType"
      :data-var-type="varType"
      :data-default-value="defaultValue"
      :placeholder="displayName"
      :value="displayValue"
      :readonly="isInputReadonly"
      @input="handleInput"
      @click="handleClick"
    />
    <!-- Secret visibility toggle -->
    <button 
      v-if="isSecret" 
      class="aimd-secret-toggle" 
      @click.stop="togglePasswordVisibility"
      :title="passwordVisible ? 'Hide' : 'Show'"
      type="button"
    >
      <span v-if="passwordVisible">👁️</span>
      <span v-else>🔒</span>
    </button>
    <span v-if="assignerReadonly === 'true'" class="aimd-var-lock" title="只读（由 Assigner 计算）">🔒</span>
    <span 
      v-if="hasManualAssigner" 
      class="aimd-var-trigger-wrapper"
      @mouseenter.stop="showTriggerTooltip"
      @mouseleave.stop="hideTriggerTooltip"
    >
      <span class="aimd-var-trigger" @click.stop="handleTrigger">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </span>
      <span v-if="triggerTooltipVisible" class="aimd-trigger-tooltip">
        <span class="aimd-trigger-tooltip-title">手动计算</span>
        <span v-if="parsedDeps.length > 0" class="aimd-trigger-tooltip-deps">
          依赖: {{ depsDisplayText }}
        </span>
      </span>
    </span>
    <span v-if="tooltipVisible" class="aimd-var-tooltip">
      <span class="aimd-tooltip-header">
        <span class="aimd-tooltip-title">{{ displayName }}</span>
        <span class="aimd-tooltip-type">{{ varType }}</span>
      </span>
      <span class="aimd-tooltip-meta">
        <span v-if="assignerMode" class="aimd-tooltip-mode">{{ modeDescription }}</span>
        <span v-if="calculatedValue" class="aimd-tooltip-calculated">{{ calculatedValue }}</span>
        <span v-if="description" class="aimd-tooltip-desc">{{ description }}</span>
        <span v-if="constraints" class="aimd-tooltip-constraints">{{ constraints }}</span>
      </span>
    </span>
  </span>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Props {
  name: string;
  variableType?: string;
  varType?: string;
  title?: string;
  defaultValue?: string;
  description?: string;
  calculatedValue?: string;
  assignerMode?: string;
  assignerReadonly?: string;
  assignerDeps?: string;  // JSON array of dependent field names
  min?: string;
  max?: string;
  ge?: string;
  le?: string;
  gt?: string;
  lt?: string;
  viewMode?: string;
  isRecording?: string; // 'true' or 'false'
  sessionValue?: string;
}

const props = withDefaults(defineProps<Props>(), {
  variableType: 'var',
  varType: 'str',
  title: '',
  defaultValue: '',
  description: '',
  viewMode: 'value',
  isRecording: 'false',
  sessionValue: ''
});

const vscode = (window as any).vscode;

const emit = defineEmits<{
  (e: 'trigger-assigner', fieldName: string): void;
}>();

const tooltipVisible = ref(false);
const triggerTooltipVisible = ref(false);
const passwordVisible = ref(false);

const isRecordingMode = computed(() => props.isRecording === 'true');
const isSecret = computed(() => props.varType === 'IgnoreStr');

const inputType = computed(() => {
  if (isSecret.value && !passwordVisible.value) {
    return 'password';
  }
  return 'text';
});

function togglePasswordVisibility() {
  passwordVisible.value = !passwordVisible.value;
}

// Check if this field has a manual assigner mode
const hasManualAssigner = computed(() => {
  return props.assignerMode === 'manual' || 
         props.assignerMode === 'auto_first' || 
         props.assignerMode === 'manual_readonly';
});

// Mode description for tooltip
const modeDescription = computed(() => {
  switch (props.assignerMode) {
    case 'auto': return '自动计算';
    case 'manual': return '手动触发';
    case 'auto_first': return '首次自动，后续手动';
    case 'auto_readonly': return '自动计算（只读）';
    case 'manual_readonly': return '手动触发（只读）';
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

// Maximum deps to show before truncation
const MAX_DEPS_DISPLAY = 5;

// Deps display text with truncation
const depsDisplayText = computed(() => {
  const deps = parsedDeps.value;
  if (deps.length === 0) return '';
  if (deps.length <= MAX_DEPS_DISPLAY) return deps.join(', ');
  return deps.slice(0, MAX_DEPS_DISPLAY).join(', ') + ` +${deps.length - MAX_DEPS_DISPLAY}更多`;
});

// Trigger tooltip show/hide
function showTriggerTooltip() {
  triggerTooltipVisible.value = true;
  tooltipVisible.value = false; // Hide main tooltip when trigger hovered
}
function hideTriggerTooltip() {
  triggerTooltipVisible.value = false;
}

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
  const hostElement = document.querySelector(`var-input[name="${props.name}"]`);
  if (hostElement) {
    hostElement.dispatchEvent(event);
  }
}

const displayValue = computed(() => {
  // Priority: sessionValue (if recording) > calculatedValue > defaultValue
  if (isRecordingMode.value && props.sessionValue) return props.sessionValue;
  if (props.calculatedValue) return props.calculatedValue;
  if (props.viewMode === 'value') return props.defaultValue;
  if (props.viewMode === 'type') return props.varType;
  if (props.viewMode === 'title') return props.title || displayName.value;
  return props.name;
});

const displayName = computed(() => {
  if (props.title) return props.title;
  // Convert snake_case to Title Case
  return props.name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
});

const constraints = computed(() => {
  const parts: string[] = [];
  if (props.min) parts.push(`min: ${props.min}`);
  if (props.max) parts.push(`max: ${props.max}`);
  if (props.ge) parts.push(`≥ ${props.ge}`);
  if (props.le) parts.push(`≤ ${props.le}`);
  if (props.gt) parts.push(`> ${props.gt}`);
  if (props.lt) parts.push(`< ${props.lt}`);
  return parts.join(', ');
});

function showTooltip() {
  tooltipVisible.value = true;
}

function hideTooltip() {
  tooltipVisible.value = false;
}

function handleClick() {
  if (isRecordingMode.value) return; // In record mode, click just focuses input
  
  // Legacy behavior needs to trigger update flow if not recording?
  // Current implementation relies on extensions handling updates differently or just being unable to update simple inputs?
  // We'll leave it empty for now as requested by previous state, or add the update request if needed.
  // Actually, checking previous files, handleClick was empty.
}

function handleInput(event: Event) {
  if (!isRecordingMode.value) return;
  
  const target = event.target as HTMLInputElement;
  const newValue = target.value;
  
  vscode.postMessage({
    type: 'session:set-var',
    payload: {
      varId: props.name,
      value: newValue
    }
  });
}

// Input is readonly unless in Record Mode
const isInputReadonly = computed(() => {
   // If assignerReadonly is true, it's always readonly
   if (props.assignerReadonly === 'true') return true;
   // Otherwise, it's readonly if NOT in record mode
   return !isRecordingMode.value;
});
</script>

<style scoped>
/* Variable Wrapper - Inline Flex for proper alignment */
.aimd-var-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
  margin: 0 4px;
  vertical-align: middle;
  transition: z-index 0.1s;
}

.aimd-var-wrapper:hover {
  z-index: 100;
}

/* Base Input Style */
.aimd-var-input {
  display: inline-block;
  border: none;
  border-radius: 2px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 0.9em;
  padding: 1px 6px;
  margin: 0;
  text-align: center;
  min-width: 80px;
  outline: none;
  transition: all 0.2s ease;
  cursor: pointer;
}

/* ==========================================================================
   THEME: MODERN (Default)
   ========================================================================== */
:host([data-design-theme="modern"]) .aimd-var-input {
  background: rgba(22, 101, 52, 0.05);
  border-bottom: 2px solid var(--aimd-green-500, #16a34a);
  color: var(--aimd-green-800, #166534);
}

:host([data-design-theme="modern"]) .aimd-var-input:hover,
:host([data-design-theme="modern"]) .aimd-var-input:focus {
  background: rgba(22, 101, 52, 0.12);
  border-bottom-color: var(--aimd-green-700, #15803d);
}

/* Modern Dark Mode */
:global(body.vscode-dark) :host([data-design-theme="modern"]) .aimd-var-input {
  background: rgba(22, 197, 94, 0.1);
  color: #4ade80;
}

/* ==========================================================================
   THEME: ELSEVIER (Journal)
   ========================================================================== */
:host([data-design-theme="elsevier"]) .aimd-var-input {
  background: transparent;
  border-bottom: 1px dashed var(--aimd-var-elsevier-border, #94a3b8);
  color: var(--aimd-var-elsevier-text, #e2e8f0);
  font-family: "Georgia", serif;
  font-style: italic;
  padding: 0 4px;
}

:host([data-design-theme="elsevier"]) .aimd-var-input:hover,
:host([data-design-theme="elsevier"]) .aimd-var-input:focus {
  background: var(--aimd-var-elsevier-hover-bg, rgba(255, 255, 255, 0.08));
  border-bottom-style: solid;
  border-bottom-color: var(--aimd-var-elsevier-hover-border, #f1f5f9);
}

/* ==========================================================================
   THEME: CLINICAL (High Contrast)
   ========================================================================== */
:host([data-design-theme="clinical"]) .aimd-var-input {
  background: var(--aimd-bg-primary, #ffffff);
  border: 1px solid var(--aimd-border-medium, #cbd5e1);
  border-radius: 0;
  color: var(--aimd-text-primary, #0f172a);
  font-weight: 700;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

:host([data-design-theme="clinical"]) .aimd-var-input:hover,
:host([data-design-theme="clinical"]) .aimd-var-input:focus {
  border-color: var(--aimd-status-success-icon, #16a34a);
  box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.1);
}

/* ==========================================================================
   THEME: WESTLAKE (Swedish Minimalism)
   Clean, precise, restrained color usage
   ========================================================================== */
:host([data-design-theme="westlake"]) .aimd-var-input {
  background: transparent;
  border: none;
  border-bottom: 2px solid var(--aimd-var-westlake-border, #00498F);
  border-radius: 0;
  color: var(--aimd-var-westlake-text, #00498F);
  font-family: 'Inter', -apple-system, sans-serif;
  font-weight: 600;
  font-style: normal;
  padding: 2px 6px;
  letter-spacing: 0.01em;
}

:host([data-design-theme="westlake"]) .aimd-var-input:hover,
:host([data-design-theme="westlake"]) .aimd-var-input:focus {
  background: var(--aimd-var-westlake-hover-bg, rgba(0, 73, 143, 0.06));
  border-bottom-color: var(--aimd-var-westlake-hover-border, #F18B1C);
}

/* Tooltip Styles (Shared / Generic) */
.aimd-var-tooltip {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(4px);
  margin-top: 8px;
  background-color: #ffffff;
  border: 1px solid var(--aimd-green-700, #15803d);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 8px 12px;
  min-width: 200px;
  max-width: 320px;
  z-index: 10;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  text-align: left;
  display: block;
}

.aimd-var-tooltip::after {
  content: '';
  position: absolute;
  bottom: 100%;
  left: 50%;
  margin-left: -6px;
  border-width: 6px;
  border-style: solid;
  border-color: transparent transparent var(--aimd-green-700, #15803d) transparent;
}

.aimd-tooltip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 6px;
  margin-bottom: 6px;
}

.aimd-tooltip-title {
  font-weight: 700;
  color: #1e293b;
  font-size: 0.95em;
}

.aimd-tooltip-type {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8em;
  color: var(--aimd-green-700, #15803d);
  background-color: var(--aimd-green-50, #f0fdf4);
  padding: 2px 6px;
  border-radius: 4px;
}

.aimd-tooltip-meta {
  font-size: 0.85em;
  color: var(--aimd-text-secondary, #64748b);
  display: block;
}

.aimd-tooltip-desc {
  margin-bottom: 4px;
  color: var(--aimd-text-tertiary, #94a3b8);
  font-style: italic;
  display: block;
}

.aimd-tooltip-constraints {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8em;
  color: var(--aimd-text-tertiary, #94a3b8);
  background: var(--aimd-bg-secondary, #f8fafc);
  padding: 2px 4px;
  border-radius: 2px;
  display: inline-block;
}

/* Calculated Value Styles - Subtle indicator */
.aimd-var-input-calculated {
  /* Just a subtle left border to indicate this is auto-calculated */
  border-left: 2px solid var(--aimd-text-tertiary, #94a3b8);
}

.aimd-tooltip-calculated {
  display: block;
  background: var(--aimd-bg-secondary, #f8fafc);
  border-left: 2px solid var(--aimd-text-tertiary, #94a3b8);
  padding: 4px 8px;
  margin-bottom: 6px;
  font-size: 0.9em;
  color: var(--aimd-text-secondary, #64748b);
}

/* Assigner Mode Indicator in Tooltip */
.aimd-tooltip-mode {
  display: block;
  font-size: 0.75em;
  color: var(--aimd-text-tertiary, #94a3b8);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Readonly State */
.aimd-var-readonly .aimd-var-input {
  background: var(--aimd-bg-tertiary, #f1f5f9);
  color: var(--aimd-text-tertiary, #94a3b8);
  cursor: not-allowed;
}

.aimd-var-input-readonly {
  opacity: 0.8;
}

/* Lock Icon */
.aimd-var-lock {
  font-size: 10px;
  margin-left: 2px;
  opacity: 0.6;
  vertical-align: middle;
}

/* Secret Toggle Button */
.aimd-secret-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  margin-left: 4px;
  padding: 0;
  background: transparent;
  border: 1px solid var(--aimd-border-light, #e2e8f0);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  opacity: 0.7;
  transition: opacity 0.2s, background 0.2s;
  vertical-align: middle;
}

.aimd-secret-toggle:hover {
  opacity: 1;
  background: var(--aimd-bg-secondary, #f1f5f9);
}

.aimd-var-input-secret {
  letter-spacing: 2px;
}

/* Manual Trigger Button */
.aimd-var-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  margin-left: 4px;
  padding: 2px;
  background: var(--aimd-bg-secondary, #f1f5f9);
  border: 1px solid var(--aimd-border-light, #e2e8f0);
  border-radius: 3px;
  cursor: pointer;
  color: var(--aimd-text-tertiary, #94a3b8);
  transition: all 0.15s ease;
  vertical-align: middle;
}

.aimd-var-trigger:hover {
  background: var(--aimd-bg-hover, #e2e8f0);
  border-color: var(--aimd-text-tertiary, #94a3b8);
  color: var(--aimd-text-secondary, #64748b);
}

.aimd-var-trigger svg {
  width: 12px;
  height: 12px;
}

.aimd-var-has-assigner .aimd-var-input {
  border-right: none;
  border-radius: 4px 0 0 4px;
}

/* Trigger Wrapper */
.aimd-var-trigger-wrapper {
  display: inline-flex;
  align-items: center;
  position: relative;
  vertical-align: middle;
}

/* Trigger Tooltip (separate from main tooltip) */
.aimd-trigger-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--aimd-bg-primary, #ffffff);
  border: 1px solid var(--aimd-border-strong, #94a3b8);
  border-radius: 6px;
  padding: 8px 12px;
  min-width: 120px;
  max-width: 250px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1001;
  white-space: normal;
  font-size: 12px;
}

.aimd-trigger-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border-width: 6px;
  border-style: solid;
  border-color: var(--aimd-border-strong, #94a3b8) transparent transparent transparent;
}

.aimd-trigger-tooltip-title {
  display: block;
  font-weight: 600;
  color: var(--aimd-text-primary, #1e293b);
  margin-bottom: 4px;
}

.aimd-trigger-tooltip-deps {
  display: block;
  font-size: 11px;
  color: var(--aimd-text-secondary, #64748b);
  line-height: 1.4;
}
</style>
