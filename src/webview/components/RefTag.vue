<template>
  <span 
    ref="host" 
    :class="['aimd-ref-tag', `aimd-ref-${type}`]"
    @mouseenter="showTooltip" 
    @mouseleave="hideTooltip"
  >
    <span class="aimd-ref-icon">{{ icon }}</span>
    <span class="aimd-ref-text">{{ currentDisplayText }}</span>
    <span v-if="jumpable" class="aimd-ref-jump" @click="handleJump" title="Jump to definition">↗</span>
    
    <!-- Tooltip -->
    <span v-if="tooltipVisible && targetMetadata" class="aimd-ref-tooltip">
      <span class="aimd-tooltip-header">
        <span class="aimd-tooltip-title">{{ targetMetadata.title || targetMetadata.name }}</span>
        <span class="aimd-tooltip-type">{{ targetMetadata.type }}</span>
      </span>
      <span class="aimd-tooltip-meta">
        <span v-if="targetMetadata.value !== undefined" class="aimd-tooltip-value">Value: {{ targetMetadata.value }}</span>
        <span v-if="targetMetadata.description" class="aimd-tooltip-desc">{{ targetMetadata.description }}</span>
      </span>
    </span>
  </span>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';

interface Props {
  type: 'step' | 'var';
  target: string;
  displayText?: string;
  jumpable?: boolean;
  viewMode?: string; // 'id' | 'value' | 'title' | 'type'
}

const props = withDefaults(defineProps<Props>(), {
  jumpable: true,
  viewMode: 'value' // Match default of VarInput
});

const emit = defineEmits<{
  (e: 'jump', target: string): void;
}>();

const host = ref<HTMLElement | null>(null);
const tooltipVisible = ref(false);
const targetMetadata = ref<any>(null);

const icon = computed(() => {
  return props.type === 'step' ? '📍' : '🔗';
});

// Calculate what text to show based on mode
const currentDisplayText = computed(() => {
  if (props.displayText) return props.displayText;
  
  // If it's a step reference, just show formatted name
  if (props.type === 'step') {
    return formatName(props.target);
  }

  // If we haven't found the target yet, fallback to formatted name
  if (!targetMetadata.value) {
    return formatName(props.target);
  }

  // Variable reference logic based on viewMode
  switch (props.viewMode) {
    case 'id':
      return props.target;
    case 'value':
      return targetMetadata.value.value !== undefined ? targetMetadata.value.value : props.target;
    case 'title':
      return targetMetadata.value.title || formatName(props.target);
    case 'type':
      return targetMetadata.value.type || 'var';
    default:
      return formatName(props.target);
  }
});

function formatName(name: string): string {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Look up the target element in the DOM to get metadata
function lookupTarget() {
  if (props.type !== 'var') return;

  // Try to find var-input or var-table
  // We need to look in the main document, outside the shadow root if this were a shadow root
  // But Custom Element slots/light DOM might be complex. 
  // Since we are in the same document context for these lightweight components:
  const selector = `var-input[name="${props.target}"], var-table[name="${props.target}"]`;
  const el = document.querySelector(selector);

  if (el) {
    targetMetadata.value = {
      name: props.target,
      title: el.getAttribute('title') || '',
      type: el.getAttribute('var-type') || 'str',
      value: el.getAttribute('default-value') || el.getAttribute('value') || '',
      description: el.getAttribute('description') || ''
    };
  }
}

function showTooltip() {
  lookupTarget(); // Refresh data just in case
  if (targetMetadata.value) {
    tooltipVisible.value = true;
  }
}

function hideTooltip() {
  tooltipVisible.value = false;
}

function handleJump() {
  emit('jump', props.target);
  
  if (host.value) {
    const event = new CustomEvent('jump', {
      detail: { target: props.target },
      bubbles: true,
      composed: true
    });
    host.value.dispatchEvent(event);
  }
}

// Initial lookup and watch for mode changes
onMounted(() => {
  // Give a small delay to allow other components to mount
  setTimeout(lookupTarget, 100);
});

// Re-lookup if target changes
watch(() => props.target, lookupTarget);
</script>

<style scoped>
.aimd-ref-tag {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 0.9em;
  font-weight: 600;
  text-decoration: none;
  vertical-align: baseline;
  margin: 4px 6px;
  cursor: default;
}

/* Step Reference */
.aimd-ref-step {
  color: var(--aimd-green-700, #15803d);
  background-color: transparent;
  border: 1px solid var(--aimd-green-500, #22c55e);
  border-radius: 12px;
  padding: 1px 8px;
  font-size: 0.85em;
}

/* Variable Reference */
.aimd-ref-var {
  color: var(--aimd-green-800, #166534);
  background-color: transparent;
  border-radius: 0;
  font-family: 'JetBrains Mono', monospace;
  border-bottom: 1px dotted var(--aimd-green-600, #16a34a);
  padding: 0 2px;
  transition: all 0.2s ease;
}

.aimd-ref-var:hover {
  background-color: rgba(22, 197, 94, 0.1);
  border-bottom-style: solid;
}

.aimd-ref-icon {
  font-size: 0.85em;
  line-height: 1;
}

.aimd-ref-text {
  font-weight: 500;
}

.aimd-ref-jump {
  cursor: pointer;
  padding: 2px 4px;
  margin-left: 2px;
  border-radius: 3px;
  transition: all 0.15s ease;
}

.aimd-ref-step .aimd-ref-jump {
  color: var(--aimd-green-600, #16a34a);
}

.aimd-ref-jump:hover {
  background: var(--aimd-green-700, #15803d);
  color: white;
}

/* Tooltip Styles (copied/adapted from VarInput) */
.aimd-ref-tooltip {
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
  min-width: 180px;
  max-width: 300px;
  z-index: 100;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  text-align: left;
  display: block;
  white-space: normal;
}

.aimd-ref-tooltip::after {
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
  color: #64748b;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.aimd-tooltip-value {
  color: #0f172a;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
}

.aimd-tooltip-desc {
  color: #94a3b8;
  font-style: italic;
}
</style>
