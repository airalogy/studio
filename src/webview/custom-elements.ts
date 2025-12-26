/**
 * Custom Elements Registration
 * 
 * Register Vue components as Web Components (Custom Elements)
 * so they can be used in v-html rendered content.
 */

import { defineCustomElement } from 'vue';
import VarInputComponent from './components/VarInput.vue';
import VarTableComponent from './components/VarTable.vue';
import StepCardComponent from './components/StepCard.vue';
import CalloutComponent from './components/Callout.vue';
import RefTagComponent from './components/RefTag.vue';
import CheckPillComponent from './components/CheckPill.vue';
import VarCodeBlockComponent from './components/VarCodeBlock.vue';
import VarMarkdownPreviewComponent from './components/VarMarkdownPreview.vue';
import VarFileCardComponent from './components/VarFileCard.vue';
import VarRecordSelectorComponent from './components/VarRecordSelector.vue';

/**
 * Register all AIMD components as custom elements
 */
export function registerCustomElements() {
    // Convert Vue components to custom elements
    const VarInput = defineCustomElement(VarInputComponent);
    const VarTable = defineCustomElement(VarTableComponent);
    const StepCard = defineCustomElement(StepCardComponent);
    const Callout = defineCustomElement(CalloutComponent);
    const RefTag = defineCustomElement(RefTagComponent);
    const CheckPill = defineCustomElement(CheckPillComponent);
    const VarCodeBlock = defineCustomElement(VarCodeBlockComponent);
    const VarMarkdownPreview = defineCustomElement(VarMarkdownPreviewComponent);
    const VarFileCard = defineCustomElement(VarFileCardComponent);
    const VarRecordSelector = defineCustomElement(VarRecordSelectorComponent);

    // Register custom elements
    if (!customElements.get('var-input')) {
        customElements.define('var-input', VarInput);
    }
    if (!customElements.get('var-table')) {
        customElements.define('var-table', VarTable);
    }
    if (!customElements.get('step-card')) {
        customElements.define('step-card', StepCard);
    }
    if (!customElements.get('callout-block')) {
        customElements.define('callout-block', Callout);
    }
    if (!customElements.get('ref-tag')) {
        customElements.define('ref-tag', RefTag);
    }
    if (!customElements.get('check-pill')) {
        customElements.define('check-pill', CheckPill);
    }
    if (!customElements.get('var-code-block')) {
        customElements.define('var-code-block', VarCodeBlock);
    }
    if (!customElements.get('var-markdown-preview')) {
        customElements.define('var-markdown-preview', VarMarkdownPreview);
    }
    if (!customElements.get('var-file-card')) {
        customElements.define('var-file-card', VarFileCard);
    }
    if (!customElements.get('var-record-selector')) {
        customElements.define('var-record-selector', VarRecordSelector);
    }
}
