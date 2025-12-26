<template>
  <label :class="['aimd-check-pill', { 'is-checked': checked }]">
    <input 
      type="checkbox" 
      class="aimd-check-input" 
      v-model="checked"
      :data-variable-name="name"
      data-variable-type="check"
    />
    <span class="aimd-check-box">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
    </span>
    <span class="aimd-check-content">
      <span class="aimd-check-name">{{ title || name }}</span>
      <span v-if="checked && displayMessage" class="aimd-check-msg">
        {{ displayMessage }}
      </span>
    </span>
  </label>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

interface Props {
  name: string;
  title?: string;
  checkedMessage?: string;
  autoChecked?: string;       // 'true' or 'false' from assigner
  autoAnnotation?: string;    // Annotation from assigner
}

const props = defineProps<Props>();

// Initialize checked state from auto-checked if provided
const checked = ref(props.autoChecked === 'true');

// Display message: prefer auto-annotation if available, else fall back to checkedMessage
const displayMessage = computed(() => {
  if (props.autoAnnotation) return props.autoAnnotation;
  return props.checkedMessage || '';
});
</script>

<style scoped>
/* ==== BASE (Default/Modern Theme - Teal) ==== */
.aimd-check-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  margin: 4px 4px;
  background: var(--aimd-check-bg, #f8fafc);
  border: 1px solid var(--aimd-check-border, #cbd5e1);
  border-radius: 999px;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
  position: relative;
}

.aimd-check-pill:hover {
  border-color: var(--aimd-check-accent, #14b8a6);
}

.aimd-check-pill.is-checked {
  border-color: var(--aimd-border-light, #e2e8f0);
  background: var(--aimd-bg-primary, #ffffff);
}

.aimd-check-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
}

.aimd-check-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border: 2px solid var(--aimd-border-strong, #94a3b8);
  border-radius: 4px;
  margin-right: 10px;
  transition: all 0.2s ease;
  flex-shrink: 0;
  background: transparent;
}

.aimd-check-box svg {
  width: 10px;
  height: 10px;
  color: white;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.is-checked .aimd-check-box {
  background: var(--aimd-check-accent, #14b8a6);
  border-color: var(--aimd-check-accent, #14b8a6);
}

.is-checked .aimd-check-box svg {
  opacity: 1;
}

.aimd-check-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.aimd-check-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--aimd-check-text, #475569);
  transition: all 0.2s ease;
}

.aimd-check-pill:hover .aimd-check-name {
  color: var(--aimd-check-accent, #14b8a6);
}

.is-checked .aimd-check-name {
  color: var(--aimd-text-tertiary, #94a3b8);
  text-decoration: line-through;
  opacity: 0.6;
}

.aimd-check-msg {
  font-size: 11px;
  font-weight: 700;
  color: var(--aimd-check-msg-text, #0f766e);
  background: var(--aimd-check-msg-bg, #ccfbf1);
  padding: 2px 10px;
  border-radius: 999px;
  animation: aimd-fade-in 0.2s ease-out;
  display: inline-block;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

@keyframes aimd-fade-in {
  from { opacity: 0; transform: translateX(-4px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes highlight-flash-teal {
  0%, 100% { box-shadow: none; }
  25%, 75% { box-shadow: 0 0 0 3px #14b8a6; }
  50% { box-shadow: 0 0 0 5px #14b8a6; }
}

.aimd-highlight-flash {
  animation: highlight-flash-teal 1.5s ease-in-out;
}

/* ==== THEME: ELSEVIER (Green) ==== */
:host([data-design-theme="elsevier"]) .aimd-check-pill:hover {
  border-color: #15803d;
}

:host([data-design-theme="elsevier"]) .is-checked .aimd-check-box {
  background: #15803d;
  border-color: #15803d;
}

:host([data-design-theme="elsevier"]) .aimd-check-pill:hover .aimd-check-name {
  color: #15803d;
}

:host([data-design-theme="elsevier"]) .aimd-check-msg {
  color: #166534;
  background: #f0fdf4;
}

/* ==== THEME: CLINICAL (Blue) ==== */
:host([data-design-theme="clinical"]) .aimd-check-pill:hover {
  border-color: #0ea5e9;
}

:host([data-design-theme="clinical"]) .is-checked .aimd-check-box {
  background: #0ea5e9;
  border-color: #0ea5e9;
}

:host([data-design-theme="clinical"]) .aimd-check-pill:hover .aimd-check-name {
  color: #0ea5e9;
}

:host([data-design-theme="clinical"]) .aimd-check-msg {
  color: #0369a1;
  background: #f0f9ff;
}

/* ==== THEME: WESTLAKE (Swedish Minimalism) ==== */
:host([data-design-theme="westlake"]) .aimd-check-pill {
  border-radius: 4px;
  border-color: var(--aimd-westlake-primary, #00498F);
}

:host([data-design-theme="westlake"]) .aimd-check-pill:hover {
  border-color: var(--aimd-westlake-accent, #F18B1C);
}

:host([data-design-theme="westlake"]) .aimd-check-box {
  border-radius: 2px;
  border-color: var(--aimd-westlake-primary, #00498F);
}

:host([data-design-theme="westlake"]) .is-checked .aimd-check-box {
  background: var(--aimd-check-westlake-accent, #00498F);
  border-color: var(--aimd-check-westlake-accent, #00498F);
}

:host([data-design-theme="westlake"]) .aimd-check-pill:hover .aimd-check-name {
  color: var(--aimd-westlake-accent, #F18B1C);
}

:host([data-design-theme="westlake"]) .aimd-check-name {
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  letter-spacing: 0.01em;
}

:host([data-design-theme="westlake"]) .aimd-check-msg {
  color: var(--aimd-check-westlake-msg-text, #00498F);
  background: var(--aimd-check-westlake-msg-bg, rgba(0, 73, 143, 0.08));
  border-radius: 4px;
}
</style>
