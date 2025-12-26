<template>
  <div 
    class="aimd-step-container" 
    :class="[levelClass, { 'aimd-highlight-flash': highlighted }]"
    :data-step-id="stepNumber"
    :data-checked="checked"
  >
    <div class="aimd-step-content" :class="{ 'is-result': isResultStep, 'is-awaiting-action': isCheckedCheckable && !checked }">
      <!-- Result Label -->
      <div v-if="isResultStep" class="aimd-result-label">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10 2v7.31L4.89 20.69C4.46 21.49 5.03 22.5 5.94 22.5h12.12c.91 0 1.48-1.01 1.05-1.81L14 9.31V2h-4z"/>
          <line x1="8.5" y1="2" x2="15.5" y2="2"/>
          <path d="M10 14h4"/>
        </svg>
        Result
      </div>
      
      <!-- Header -->
      <div class="aimd-step-header" @click="toggleCollapse">
        <div class="aimd-step-header-left">
          <div 
            :class="['aimd-step-badge', { 'is-checkable': isCheckedCheckable, 'is-checked': checked, 'is-warning': isCheckedCheckable && !checked }]"
            :data-checkable="isCheckedCheckable"
            :data-checked="checked"
            @click.stop="toggleCheck"
          >
            {{ stepNumber }}
          </div>
          <div class="aimd-step-title-group">
            <div class="aimd-step-title">{{ title }}</div>
            <div v-if="subtitle" class="aimd-step-subtitle">{{ subtitle }}</div>
            <div v-if="checkedMessage && checked" class="aimd-step-checked-message">{{ checkedMessage }}</div>
          </div>
        </div>
        <div class="aimd-chevron" :class="{ 'collapsed': collapsed }">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>
      </div>
      
      <!-- Body -->
      <div v-show="!collapsed" class="aimd-step-body">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Props {
  stepNumber: string | number;
  title: string;
  subtitle?: string;
  level?: string | number;
  hasCheck?: boolean | string;
  checkedMessage?: string;
  isResult?: boolean | string;
}

const props = withDefaults(defineProps<Props>(), {
  level: 1,
  hasCheck: false,
  checkedMessage: '',
  isResult: false
});

const isCheckedCheckable = computed(() => {
  return props.hasCheck === true || props.hasCheck === 'true';
});

const isResultStep = computed(() => {
  return props.isResult === true || props.isResult === 'true';
});

const collapsed = ref(false);
const checked = ref(false);
const highlighted = ref(false);

const levelClass = computed(() => {
  const levelNum = typeof props.level === 'string' ? parseInt(props.level, 10) : (props.level || 1);
  return levelNum > 1 ? `aimd-step-level-${levelNum}` : '';
});

function toggleCollapse() {
  collapsed.value = !collapsed.value;
}

function toggleCheck() {
  if (isCheckedCheckable.value) {
    checked.value = !checked.value;
  }
}
</script>

<style scoped>
.aimd-step-container {
  margin-bottom: 12px;
}

.aimd-step-container:last-child {
  margin-bottom: 0;
}

.aimd-step-content {
  flex: 1;
  min-width: 0;
  background-color: var(--aimd-bg-primary);
  border: 1px solid var(--aimd-border-light);
  border-left: 2px solid var(--aimd-brand-primary); /* Thinner border */
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
  overflow: visible;
  display: flex;
  flex-direction: column;
}

.aimd-step-content:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-left-width: 4px; /* Reduced hover expansion */
}

/* Awaiting Action State (Pulse Animation) */
.aimd-step-content.is-awaiting-action {
  border-left-color: #f59e0b; /* Amber 500 */
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.1);
  animation: card-pulse 2s infinite ease-in-out;
}

@keyframes card-pulse {
  0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); }
  70% { box-shadow: 0 0 0 4px rgba(245, 158, 11, 0); }
  100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
}

.aimd-step-content.is-result {
  border-top-color: var(--aimd-status-success-icon);
  background-color: var(--aimd-status-success-bg);
}

.aimd-result-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--aimd-status-success-text);
  font-weight: 700;
  padding: 12px 20px 0 20px;
}

.aimd-step-header {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  background-color: rgba(128, 128, 128, 0.02);
}

.aimd-step-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.aimd-step-badge {
  width: 32px;
  height: 32px;
  min-width: 32px;
  aspect-ratio: 1 / 1;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--aimd-brand-primary);
  color: var(--aimd-text-inverse);
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'Menlo', 'Monaco', monospace;
  font-weight: 800;
  font-size: 15px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
  cursor: default;
}

.aimd-step-badge.is-checkable {
  cursor: pointer;
}

.aimd-step-badge.is-warning {
  background-color: #f59e0b; /* Amber 500 */
}

/* Badge pulse animation removed as card now pulses */
/* .aimd-step-badge.is-warning { animation: pulse-ring 2s infinite; } */

.aimd-step-badge.is-checked {
  background-color: var(--aimd-brand-primary);
  transform: scale(1.05);
}

.aimd-step-title-group {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.aimd-step-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--aimd-text-primary);
}

.aimd-step-subtitle {
  font-size: 13px;
  color: var(--aimd-text-secondary);
  margin-top: 4px;
}

.aimd-step-checked-message {
  font-size: 13px;
  color: #14b8a6;
  font-weight: 500;
  margin-top: 4px;
  font-style: italic;
}

.aimd-step-body {
  padding: 12px 20px 16px 20px;
  color: var(--aimd-text-primary);
  font-size: 14px;
  line-height: 1.6;
  transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: visible;
  min-height: 20px;
}

.aimd-chevron {
  color: #94a3b8;
  transition: transform 0.2s;
}

.aimd-chevron.collapsed {
  transform: rotate(-90deg);
}

/* Indentation Levels */
.aimd-step-level-2 { margin-left: 40px; }
.aimd-step-level-3 { margin-left: 80px; }

/* Highlight Animation */
@keyframes highlight-flash {
  0%, 100% { box-shadow: none; }
  25%, 75% { box-shadow: 0 0 0 3px #22c55e; }
  50% { box-shadow: 0 0 0 5px #22c55e; }
}

.aimd-highlight-flash {
  animation: highlight-flash 1.5s ease-in-out;
}

/* Base Styles */
.aimd-step-container { margin-bottom: 12px; }
.aimd-step-content {
  background-color: var(--aimd-bg-primary);
  border: 1px solid var(--aimd-border-light);
  border-left: 2px solid var(--aimd-brand-primary);
  border-radius: 4px;
}

/* ==========================================================================
   THEME: MODERN (Default - Darker in dark mode)
   ========================================================================== */
/* ==========================================================================
   THEME: MODERN (Default - Darker in dark mode)
   ========================================================================== */
:host([data-design-theme="modern"]) .aimd-step-content {
  border-left-width: 4px;
}

:host([data-design-theme="modern"]) .aimd-step-content.is-awaiting-action {
  background-color: var(--aimd-status-warning-bg);
  border-left-color: var(--aimd-status-warning-icon);
}

/* Dark Mode Overrides for Modern - NOW HANDLED BY VARS but kept for specific tweaks if needed */
/* Removed hardcoded dark mode overrides as vars handle this now */

/* ==========================================================================
   THEME: ELSEVIER (Journal)
   ========================================================================== */
:host([data-design-theme="elsevier"]) .aimd-step-container {
  border-bottom: 1px solid var(--aimd-border-light);
  padding-bottom: 16px;
  margin-bottom: 24px;
}

:host([data-design-theme="elsevier"]) .aimd-step-content {
  border: none;
  border-left: none;
  background: transparent;
  box-shadow: none;
  border-radius: 0;
}

:host([data-design-theme="elsevier"]) .aimd-step-content.is-awaiting-action {
  border: 1px dashed var(--aimd-status-warning-icon);
  padding: 8px;
  background-color: var(--aimd-status-warning-bg);
}

:host([data-design-theme="elsevier"]) .aimd-step-header {
  padding: 0;
  background: transparent;
  margin-bottom: 8px;
}

:host([data-design-theme="elsevier"]) .aimd-step-badge {
  background-color: transparent;
  color: var(--aimd-text-primary);
  border: 1px solid var(--aimd-border-medium);
  box-shadow: none;
  font-family: "Georgia", serif;
}

:host([data-design-theme="elsevier"]) .aimd-step-badge.is-warning {
  border-color: var(--aimd-status-warning-icon);
  color: var(--aimd-status-warning-text);
  background-color: var(--aimd-status-warning-bg);
}

:host([data-design-theme="elsevier"]) .aimd-step-title {
  font-family: "Georgia", serif;
  font-size: 1.1em;
  color: var(--aimd-text-primary);
}

/* ==========================================================================
   THEME: CLINICAL (High Contrast)
   ========================================================================== */
:host([data-design-theme="clinical"]) .aimd-step-content {
  border: 1px solid var(--aimd-border-medium);
  border-left: 6px solid var(--aimd-brand-primary); /* Thick status line */
  border-radius: 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  background: var(--aimd-bg-primary);
}

:host([data-design-theme="clinical"]) .aimd-step-content.is-awaiting-action {
  border-left-color: var(--aimd-status-error-icon); /* Red/Orange for Clinical Alert */
  background-color: var(--aimd-status-error-bg);
}

:host([data-design-theme="clinical"]) .aimd-step-header {
  border-bottom: 1px solid var(--aimd-border-light);
  background: var(--aimd-bg-secondary);
}

:host([data-design-theme="clinical"]) .aimd-step-badge {
  border-radius: 2px;
  background-color: var(--aimd-brand-primary);
  box-shadow: none;
}

:host([data-design-theme="clinical"]) .aimd-step-badge.is-warning {
  background-color: var(--aimd-status-error-icon);
  animation: pulse-ring 2s infinite;
}

/* ==========================================================================
   THEME: WESTLAKE (Swedish Minimalism)
   Clean lines, restrained, sophisticated
   ========================================================================== */
:host([data-design-theme="westlake"]) .aimd-step-container {
  margin-bottom: 20px;
}

:host([data-design-theme="westlake"]) .aimd-step-content {
  border: none;
  border-left: 3px solid var(--aimd-westlake-primary, #00498F);
  background: var(--aimd-bg-primary);
  box-shadow: none;
  border-radius: 0;
}

:host([data-design-theme="westlake"]) .aimd-step-content:hover {
  border-left-width: 4px;
  background: var(--aimd-bg-secondary);
}

:host([data-design-theme="westlake"]) .aimd-step-content.is-awaiting-action {
  border-left-color: var(--aimd-westlake-accent, #F18B1C);
  background-color: rgba(241, 139, 28, 0.04);
}

:host([data-design-theme="westlake"]) .aimd-step-header {
  padding: 16px 20px;
  background: transparent;
}

:host([data-design-theme="westlake"]) .aimd-step-badge {
  background-color: var(--aimd-westlake-primary, #00498F);
  color: #ffffff;
  border-radius: 0;
  box-shadow: none;
  font-family: 'Inter', sans-serif;
}

:host([data-design-theme="westlake"]) .aimd-step-badge.is-warning {
  background-color: var(--aimd-westlake-accent, #F18B1C);
}

:host([data-design-theme="westlake"]) .aimd-step-badge.is-checked {
  background-color: var(--aimd-westlake-neutral, #5B5657);
}

:host([data-design-theme="westlake"]) .aimd-step-title {
  font-family: 'Inter', -apple-system, sans-serif;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--aimd-text-primary);
}
</style>
