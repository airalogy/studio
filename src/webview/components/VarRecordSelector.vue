<template>
  <div class="var-record-selector" ref="container">
    <div class="input-wrapper">
      <i class="codicon codicon-search input-icon"></i>
      <input 
        type="text" 
        v-model="query" 
        @focus="handleFocus" 
        @blur="handleBlur"
        @input="handleInput"
        :placeholder="placeholder"
        class="record-input"
      />
      <button v-if="query" class="clear-btn" @mousedown.prevent="clear">
        <i class="codicon codicon-close"></i>
      </button>
    </div>

    <!-- Dropdown Results -->
    <div class="dropdown-menu" v-if="isOpen && (results.length > 0 || isLoading)">
      <div v-if="isLoading" class="loading-item">Loading...</div>
      <template v-else>
        <div 
          v-for="item in results" 
          :key="item.id" 
          class="dropdown-item"
          @mousedown.prevent="select(item)"
        >
          <div class="item-icon">
            <i class="codicon codicon-symbol-class"></i>
          </div>
          <div class="item-details">
            <div class="item-title">{{ item.title || item.id }}</div>
            <div class="item-desc" v-if="item.description">{{ item.description }}</div>
          </div>
          <i class="codicon codicon-check check-icon" v-if="item.id === selectedId"></i>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';

const props = defineProps<{
  name: string;
  varType: string;
  defaultValue?: string;
  calculatedValue?: string;
  isRecording?: string; // string 'true' or 'false'
  sessionValue?: string;
}>();

const vscode = (window as any).vscode;
const container = ref<HTMLElement | null>(null);

const query = ref('');
const results = ref<any[]>([]);
const isOpen = ref(false);
const isLoading = ref(false);
const searchTimeout = ref<any>(null);

const isRecordingMode = computed(() => props.isRecording === 'true');

// Initialize from default, prioritizing sessionValue
const selectedId = computed(() => {
    if (isRecordingMode.value && props.sessionValue !== undefined && props.sessionValue !== null && props.sessionValue !== '') {
        return props.sessionValue;
    }
    return props.calculatedValue || props.defaultValue || '';
});

watch(() => selectedId.value, (newVal) => {
    if (newVal && !isOpen.value) {
        query.value = newVal;
    }
}, { immediate: true });

const placeholder = computed(() => `Select ${props.varType}...`);

const handleFocus = () => {
    isOpen.value = true;
    if (results.value.length === 0) {
        triggerSearch();
    }
};

const handleBlur = () => {
    // Delay hiding to allow click event to fire
    setTimeout(() => {
        isOpen.value = false;
        // Reset query to selected ID if no change
        if (selectedId.value && query.value !== selectedId.value) {
            query.value = selectedId.value;
        }
    }, 200);
};

const handleInput = () => {
    isLoading.value = true;
    if (searchTimeout.value) clearTimeout(searchTimeout.value);
    
    searchTimeout.value = setTimeout(() => {
        triggerSearch();
    }, 300);
};

const triggerSearch = () => {
    vscode.postMessage({
        type: 'record:search',
        payload: {
            fieldName: props.name,
            query: query.value
        }
    });
};

const select = (item: any) => {
    query.value = item.id;
    isOpen.value = false;
    
    if (isRecordingMode.value) {
        vscode.postMessage({
            type: 'session:set-var',
            payload: {
                varId: props.name,
                value: item.id
            }
        });
    } else {
        vscode.postMessage({
            type: 'variable:update',
            payload: {
                fieldName: props.name,
                value: item.id
            }
        });
    }
};

const clear = () => {
    query.value = '';
    handleInput(); // triggers empty search
};

const handleMessage = (event: MessageEvent) => {
    const message = event.data;
    if (message.type === 'record:search:result') {
        if (message.payload.fieldName === props.name) {
            results.value = message.payload.results;
            isLoading.value = false;
        }
    }
};

onMounted(() => {
    window.addEventListener('message', handleMessage);
});

onUnmounted(() => {
    window.removeEventListener('message', handleMessage);
});
</script>

<style scoped>
.var-record-selector {
  position: relative;
  margin: 8px 0;
  font-family: var(--vscode-font-family);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--vscode-input-background);
  border: 1px solid var(--vscode-input-border);
  border-radius: 4px;
  color: var(--vscode-input-foreground);
}

.input-wrapper:focus-within {
  border-color: var(--vscode-focusBorder);
  outline: 1px solid var(--vscode-focusBorder);
}

.input-icon {
    padding-left: 8px;
    color: var(--vscode-input-placeholderForeground);
}

.record-input {
  width: 100%;
  padding: 6px 8px;
  background: transparent;
  border: none;
  color: inherit;
  outline: none;
  font-size: 13px;
}

.record-input::placeholder {
  color: var(--vscode-input-placeholderForeground);
}

.clear-btn {
    background: none;
    border: none;
    color: var(--vscode-icon-foreground);
    cursor: pointer;
    padding: 4px 8px;
    display: flex;
    align-items: center;
}
.clear-btn:hover {
    color: var(--vscode-foreground);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  max-height: 200px;
  overflow-y: auto;
  background: var(--vscode-dropdown-background);
  border: 1px solid var(--vscode-widget-border);
  border-radius: 4px;
  margin-top: 4px;
  z-index: 100;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  cursor: pointer;
  color: var(--vscode-dropdown-foreground);
  gap: 8px;
}

.dropdown-item:hover {
  background: var(--vscode-list-hoverBackground);
  color: var(--vscode-list-hoverForeground);
}

.item-icon {
    color: var(--vscode-symbolIcon-classForeground);
}

.item-details {
    flex: 1;
    overflow: hidden;
}

.item-title {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.item-desc {
    font-size: 11px;
    opacity: 0.8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.loading-item {
    padding: 8px;
    text-align: center;
    color: var(--vscode-descriptionForeground);
    font-style: italic;
}
</style>
