<template>
  <div class="aimd-toolbar">
    <!-- Theme Toggle Button -->
    <button 
      class="aimd-theme-toggle" 
      @click="handleThemeToggle"
      :title="`Theme: ${currentThemeLabel}`"
    >
      <span class="theme-icon">{{ themeIcon }}</span>
    </button>

    <div 
      class="aimd-ring-dial" 
      :data-mode="currentMode" 
      @click="handleToggle"
      title="Toggle Variable View Mode"
    >
      <!-- SVG Ring -->
      <svg class="dial-ring" viewBox="0 0 64 64">
        <circle class="dial-bg" cx="32" cy="32" r="28" fill="none" stroke-width="4" />
        <circle 
          class="dial-segment" 
          cx="32" 
          cy="32" 
          r="28" 
          fill="none" 
          stroke-width="4" 
          stroke-dasharray="44 132"
          :data-mode="currentMode"
        />
      </svg>

      <!-- Center content -->
      <div class="dial-center">
        <span class="dial-letter">{{ currentModeLabel.letter }}</span>
        <span class="dial-label">{{ currentModeLabel.label }}</span>
      </div>

      <!-- Segment labels -->
      <div class="dial-labels">
        <div 
          v-for="(mode, index) in MODES" 
          :key="index"
          :class="['dial-seg-label', `seg-${index}`, { active: currentMode === index }]"
        >
          {{ mode.letter }}
        </div>
      </div>
    </div>

    <!-- History Button -->
    <button 
      class="aimd-record-history" 
      @click="$emit('record-history')"
      title="Historical Records"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </button>

    <!-- Record Mode Toggle -->
    <button 
      class="aimd-record-toggle" 
      :class="{ active: isRecording }"
      @click="$emit('record-toggle')"
      :title="isRecording ? 'Stop Recording' : 'Start Record Mode'"
    >
      <div class="record-icon"></div>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{
  mode: number;
  theme: 'elsevier' | 'modern' | 'clinical' | 'westlake';
  isRecording?: boolean;
}>();

const emit = defineEmits(['mode-change', 'theme-change', 'record-toggle', 'record-history']);

const MODES = [
  { letter: 'ID', label: 'ID' },
  { letter: 'V',  label: 'Value' },
  { letter: 'T',  label: 'Title' },
  { letter: 'Σ',  label: 'Type' }
];

const THEME_MODES: Array<'modern' | 'elsevier' | 'clinical' | 'westlake'> = ['modern', 'elsevier', 'clinical', 'westlake'];
const THEME_ICONS: Record<string, string> = {
  modern: '✨',   // Modern LIMS
  elsevier: '📖', // Journal
  clinical: '🏥', // Clinical
  westlake: '🏛️'  // Westlake Academy
};
const THEME_LABELS: Record<string, string> = {
  modern: 'Modern',
  elsevier: 'Journal',
  clinical: 'Clinical',
  westlake: 'Westlake'
};

const currentMode = computed(() => props.mode);
const currentModeLabel = computed(() => MODES[currentMode.value]);

const themeIcon = computed(() => THEME_ICONS[props.theme] ?? '✨');
const currentThemeLabel = computed(() => THEME_LABELS[props.theme] ?? 'Modern');

function handleToggle() {
  const nextMode = (currentMode.value + 1) % MODES.length;
  emit('mode-change', nextMode);
}

function handleThemeToggle() {
  const currentIndex = THEME_MODES.indexOf(props.theme);
  const nextIndex = (currentIndex + 1) % THEME_MODES.length;
  emit('theme-change', THEME_MODES[nextIndex]);
}
</script>

<style scoped>
.aimd-toolbar {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

/* Theme Toggle Button */
.aimd-theme-toggle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: var(--aimd-bg-primary);
  color: var(--aimd-text-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.aimd-theme-toggle:hover {
  transform: scale(1.08);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
}

.aimd-theme-toggle:active {
  transform: scale(0.95);
}

.theme-icon {
  font-size: 18px;
  line-height: 1;
}

.aimd-ring-dial {
  width: 64px;
  height: 64px;
  position: relative;
  cursor: pointer;
  background: var(--aimd-bg-primary);
  border-radius: 50%;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  user-select: none;
}

.aimd-ring-dial:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

.aimd-ring-dial:active {
  transform: scale(0.98);
}

/* SVG Ring */
.dial-ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg); /* Start from top */
}

.dial-bg {
  stroke: var(--aimd-border-light);
}

.dial-segment {
  stroke: var(--aimd-brand-primary);
  stroke-linecap: round;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: center;
}

/* Mode-specific segment rotation */
.dial-segment[data-mode="0"] { transform: rotate(0deg); }
.dial-segment[data-mode="1"] { transform: rotate(90deg); }
.dial-segment[data-mode="2"] { transform: rotate(180deg); }
.dial-segment[data-mode="3"] { transform: rotate(270deg); }

/* Center label */
.dial-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.dial-letter {
  font-size: 18px;
  font-weight: 700;
  color: var(--aimd-brand-primary);
  line-height: 1;
  transition: all 0.3s ease;
}

.dial-label {
  font-size: 8px;
  font-weight: 500;
  color: var(--aimd-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 2px;
  transition: all 0.3s ease;
}

/* Segment labels around the ring */
.dial-labels {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.dial-seg-label {
  position: absolute;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 600;
  color: var(--aimd-text-tertiary);
  border-radius: 50%;
  transition: all 0.3s ease;
}

.dial-seg-label.active {
  color: var(--aimd-brand-primary);
  background: var(--aimd-bg-tertiary);
  transform: scale(1.1);
}

/* Position labels at cardinal directions */
.seg-0 { top: 2px; left: 50%; transform: translateX(-50%); }
.seg-1 { right: 2px; top: 50%; transform: translateY(-50%); }
.seg-2 { bottom: 2px; left: 50%; transform: translateX(-50%); }
.seg-3 { left: 2px; top: 50%; transform: translateY(-50%); }

.seg-0.active { transform: translateX(-50%) scale(1.1); }
.seg-1.active { transform: translateY(-50%) scale(1.1); }
.seg-2.active { transform: translateX(-50%) scale(1.1); }
.seg-3.active { transform: translateY(-50%) scale(1.1); }

/* Mode colors */
.aimd-ring-dial[data-mode="0"] .dial-segment { stroke: var(--aimd-brand-primary); }
.aimd-ring-dial[data-mode="1"] .dial-segment { stroke: #6366f1; }
.aimd-ring-dial[data-mode="2"] .dial-segment { stroke: #f59e0b; }
.aimd-ring-dial[data-mode="3"] .dial-segment { stroke: #8b5cf6; }

.aimd-ring-dial[data-mode="0"] .dial-letter { color: var(--aimd-brand-primary); }
.aimd-ring-dial[data-mode="1"] .dial-letter { color: #4f46e5; }
.aimd-ring-dial[data-mode="2"] .dial-letter { color: #d97706; }
.aimd-ring-dial[data-mode="3"] .dial-letter { color: #7c3aed; }

/* Record Toggle */
.aimd-record-toggle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: var(--aimd-bg-primary);
  color: var(--aimd-text-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.aimd-record-toggle:hover {
  transform: scale(1.08);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
}

/* History Button Styles */
.aimd-record-history {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: var(--aimd-bg-primary);
  color: var(--aimd-text-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.aimd-record-history:hover {
  transform: scale(1.08);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
}

.aimd-record-history:active {
  transform: scale(0.95);
}

.aimd-record-history svg {
  width: 18px;
  height: 18px;
  color: var(--aimd-text-secondary);
}

.aimd-record-toggle:active {
  transform: scale(0.95);
}

.aimd-record-toggle.active .record-icon {
  animation: pulse-red 1.5s infinite;
}

.record-icon {
  width: 14px;
  height: 14px;
  background-color: #ef4444; /* Red-500 */
  border-radius: 50%;
  transition: all 0.3s ease;
}

.aimd-record-toggle.active .record-icon {
  width: 14px;
  height: 14px;
  border-radius: 2px; /* Square stop icon */
}

@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}
</style>
