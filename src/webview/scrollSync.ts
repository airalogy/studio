/**
 * Scroll Synchronization Module
 * 
 * Implements element-based scroll mapping for precise synchronization
 * between source editor line numbers and preview DOM elements.
 * 
 * Algorithm:
 * 1. Find anchor element: the element with data-source-line <= targetLine
 * 2. Find next element: the element with data-source-line > targetLine
 * 3. Linear interpolation: calculate exact scroll position between anchor and next
 */

// Flag to prevent auto-scroll loops when both directions are synced
let isAutoScrolling = false;
const AUTO_SCROLL_LOCKOUT_MS = 150;

// Top offset for header clearance (adjust if you have a fixed header)
const HEADER_OFFSET = 20;

/**
 * Get the absolute top position of an element relative to the document
 */
function getElementTop(el: HTMLElement): number {
    const rect = el.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    return rect.top + scrollTop;
}

/**
 * Scroll the preview to match the source editor's line position
 * Uses element-based mapping with linear interpolation for precision
 * 
 * @param targetLine - The line number in the source file (0-indexed)
 */
export function scrollToLine(targetLine: number): void {
    // Get all elements that have source line markers
    const elements = Array.from(
        document.querySelectorAll('[data-source-line]')
    ) as HTMLElement[];

    if (elements.length === 0) {
        // No elements with line markers, use ratio-based fallback
        const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
        // Use a reasonable estimate for document length
        const ratio = Math.min(1, targetLine / 200);
        window.scrollTo({ top: ratio * maxScroll, behavior: 'auto' });
        return;
    }

    // Sort elements by their source line
    elements.sort((a, b) => {
        const lineA = parseInt(a.getAttribute('data-source-line') || '0', 10);
        const lineB = parseInt(b.getAttribute('data-source-line') || '0', 10);
        return lineA - lineB;
    });

    // Find anchor element (last element with line <= targetLine)
    // and next element (first element with line > targetLine)
    let anchorElement: HTMLElement | null = null;
    let anchorLine = 0;
    let nextElement: HTMLElement | null = null;
    let nextLine = 0;

    for (let i = 0; i < elements.length; i++) {
        const elLine = parseInt(elements[i].getAttribute('data-source-line') || '0', 10);

        if (elLine <= targetLine) {
            anchorElement = elements[i];
            anchorLine = elLine;
        } else {
            // Found the first element with line > targetLine
            nextElement = elements[i];
            nextLine = elLine;
            break;
        }
    }

    // Calculate scroll position
    let scrollToY = 0;

    if (!anchorElement) {
        // Target line is before any marked element, scroll to top
        scrollToY = 0;
    } else {
        // Start with the anchor element's position
        scrollToY = getElementTop(anchorElement) - HEADER_OFFSET;

        // Apply linear interpolation if we have a next element
        // This smooths scrolling between elements
        if (nextElement && nextLine > anchorLine) {
            const anchorTop = getElementTop(anchorElement);
            const nextTop = getElementTop(nextElement);
            const pixelDiff = nextTop - anchorTop;
            const lineDiff = nextLine - anchorLine;

            // Calculate progress (how far between anchor and next)
            const progress = (targetLine - anchorLine) / lineDiff;

            // Interpolate pixel position
            scrollToY = anchorTop + (pixelDiff * progress) - HEADER_OFFSET;
        }
    }

    // Ensure bounds
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    scrollToY = Math.max(0, Math.min(scrollToY, maxScroll));

    // Set auto-scrolling flag to prevent feedback loops
    isAutoScrolling = true;

    // Perform the scroll with 'auto' for immediate response
    window.scrollTo({
        top: scrollToY,
        behavior: 'auto'
    });

    // Clear the lock after a short delay
    setTimeout(() => {
        isAutoScrolling = false;
    }, AUTO_SCROLL_LOCKOUT_MS);
}

/**
 * Check if we're currently in an auto-scroll state
 * Use this to prevent feedback loops when implementing bidirectional sync
 */
export function isAutoScrollingActive(): boolean {
    return isAutoScrolling;
}

/**
 * Get the source line for a given scroll position
 * Useful for implementing preview-to-source sync (bidirectional)
 */
export function getLineForScrollPosition(): number | null {
    const elements = Array.from(
        document.querySelectorAll('[data-source-line]')
    ) as HTMLElement[];

    if (elements.length === 0) return null;

    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const viewportTop = scrollTop + HEADER_OFFSET + 50; // A bit below the top

    // Find the element closest to the viewport top
    let closestElement: HTMLElement | null = null;
    let closestDistance = Infinity;

    for (const el of elements) {
        const elTop = getElementTop(el);
        const distance = Math.abs(elTop - viewportTop);

        if (distance < closestDistance) {
            closestDistance = distance;
            closestElement = el;
        }
    }

    if (closestElement) {
        return parseInt(closestElement.getAttribute('data-source-line') || '0', 10);
    }

    return null;
}
