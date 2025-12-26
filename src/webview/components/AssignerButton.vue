<template>
  <button 
    class="aimd-assigner-btn" 
    :class="{
      'is-loading': loading,
      'is-success': success,
      'is-error': error
    }"
    :disabled="loading"
    @click="handleClick"
    :title="tooltip"
  >
    <span class="aimd-assigner-icon">
      <svg v-if="!loading && !success && !error" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      <svg v-else-if="loading" class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="12" />
      </svg>
      <svg v-else-if="success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
      <svg v-else-if="error" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </span>
    <span v-if="showLabel" class="aimd-assigner-label">{{ label }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Props {
  fieldName: string;
  mode?: string; // 'manual' | 'auto_first' | 'manual_readonly'
  showLabel?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'manual',
  showLabel: false
});

const emit = defineEmits<{
  (e: 'trigger', fieldName: string): void;
  (e: 'success', result: any): void;
  (e: 'error', error: string): void;
}>();

const loading = ref(false);
const success = ref(false);
const error = ref(false);

const label = computed(() => {
  if (loading.value) return '计算中...';
  if (success.value) return '完成';
  if (error.value) return '失败';
  return '计算';
});

const tooltip = computed(() => {
  if (props.mode === 'manual') return '手动执行计算';
  if (props.mode === 'auto_first') return '首次自动计算，后续手动触发';
  if (props.mode === 'manual_readonly') return '手动计算（结果只读）';
  return '执行计算';
});

function handleClick() {
  if (loading.value) return;
  
  loading.value = true;
  success.value = false;
  error.value = false;
  
  emit('trigger', props.fieldName);
  
  // Auto-reset state after animation
  setTimeout(() => {
    loading.value = false;
    // Success/error will be set by parent via exposed methods
  }, 800);
}

// Exposed methods for parent to control state
function setSuccess() {
  success.value = true;
  setTimeout(() => { success.value = false; }, 2000);
}

function setError() {
  error.value = true;
  setTimeout(() => { error.value = false; }, 2000);
}

defineExpose({ setSuccess, setError });
</script>

<style scoped>
.aimd-assigner-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  margin-left: 4px;
  background: var(--aimd-bg-secondary, #f1f5f9);
  border: 1px solid var(--aimd-border-light, #e2e8f0);
  border-radius: 4px;
  color: var(--aimd-text-secondary, #64748b);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  vertical-align: middle;
}

.aimd-assigner-btn:hover:not(:disabled) {
  background: var(--aimd-bg-hover, #e2e8f0);
  border-color: var(--aimd-border-strong, #94a3b8);
  color: var(--aimd-text-primary, #334155);
}

.aimd-assigner-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.aimd-assigner-btn.is-loading {
  background: var(--aimd-bg-secondary, #f1f5f9);
}

.aimd-assigner-btn.is-success {
  background: var(--aimd-green-50, #f0fdf4);
  border-color: var(--aimd-green-300, #86efac);
  color: var(--aimd-green-700, #15803d);
}

.aimd-assigner-btn.is-error {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #b91c1c;
}

.aimd-assigner-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
}

.aimd-assigner-icon svg {
  width: 100%;
  height: 100%;
}

.aimd-assigner-label {
  white-space: nowrap;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 1s linear infinite;
}

/* Compact mode (no label) */
.aimd-assigner-btn:not(:has(.aimd-assigner-label)) {
  padding: 3px 5px;
}

/* Theme variants */
:host([data-design-theme="westlake"]) .aimd-assigner-btn {
  border-radius: 2px;
  font-family: 'Inter', sans-serif;
}

:host([data-design-theme="westlake"]) .aimd-assigner-btn:hover:not(:disabled) {
  border-color: var(--aimd-westlake-accent, #F18B1C);
  color: var(--aimd-westlake-accent, #F18B1C);
}
</style>
