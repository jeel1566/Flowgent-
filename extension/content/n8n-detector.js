/**
 * n8n node detector content script
 * Detects n8n workflow canvas and node elements
 */

(function () {
    'use strict';

    let isN8nPage = false;
    let observer = null;

    // Check if this is an n8n page
    function detectN8n() {
        // Look for n8n-specific elements
        const n8nIndicators = [
            '[data-test-id="canvas"]',
            '.node-view',
            '.jtk-connector',
            '#node-creator',
            '[class*="n8n"]'
        ];

        for (const selector of n8nIndicators) {
            if (document.querySelector(selector)) {
                isN8nPage = true;
                return true;
            }
        }

        // Check URL patterns
        if (window.location.href.includes('/workflow/') ||
            window.location.href.includes('n8n.io') ||
            window.location.hostname.includes('n8n')) {
            isN8nPage = true;
            return true;
        }

        return false;
    }

    // Initialize the Information Hand feature
    function initInformationHand() {
        if (!isN8nPage) {
            console.log('Flowgent: Not an n8n page, skipping Information Hand');
            return;
        }

        console.log('Flowgent: n8n page detected, initializing Information Hand');

        // Inject tooltip script and styles
        injectTooltipResources();

        // Watch for node elements
        watchForNodes();
    }

    // Inject tooltip script and stylesheet
    function injectTooltipResources() {
        // Inject CSS
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = chrome.runtime.getURL('content/styles.css');
        document.head.appendChild(link);

        // Inject tooltip script
        const script = document.createElement('script');
        script.src = chrome.runtime.getURL('content/tooltip.js');
        document.body.appendChild(script);
    }

    // Watch for n8n node elements
    function watchForNodes() {
        // Observe DOM changes to detect new nodes
        observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        attachTooltipHandlers(node);
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Attach to existing nodes
        attachTooltipHandlers(document.body);
    }

    // Attach tooltip event handlers to nodes
    function attachTooltipHandlers(container) {
        // Look for n8n node elements
        const nodeSelectors = [
            '[data-test-id*="node"]',
            '.node-wrapper',
            '.node',
            '[class*="Node_"]',
            '[data-node-name]'
        ];

        nodeSelectors.forEach(selector => {
            const nodes = container.querySelectorAll ? container.querySelectorAll(selector) : [];

            nodes.forEach(nodeElement => {
                // Skip if already has handler
                if (nodeElement.dataset.flowgentTooltip) return;

                nodeElement.dataset.flowgentTooltip = 'true';

                // Extract node type
                const nodeType = extractNodeType(nodeElement);
                if (nodeType) {
                    nodeElement.addEventListener('mouseenter', (e) => showTooltip(e, nodeType));
                    nodeElement.addEventListener('mouseleave', hideTooltip);
                }
            });
        });
    }

    // Extract node type from element
    function extractNodeType(element) {
        // Try various methods to get node type
        const nodeName = element.dataset.nodeName ||
            element.dataset.name ||
            element.getAttribute('data-node-type') ||
            element.className;

        // Common n8n node patterns
        if (nodeName.includes('HttpRequest')) return 'n8n-nodes-base.httpRequest';
        if (nodeName.includes('Webhook')) return 'n8n-nodes-base.webhook';
        if (nodeName.includes('Set')) return 'n8n-nodes-base.set';
        if (nodeName.includes('If')) return 'n8n-nodes-base.if';
        if (nodeName.includes('Code')) return 'n8n-nodes-base.code';
        if (nodeName.includes('Slack')) return 'n8n-nodes-base.slack';
        if (nodeName.includes('Google')) {
            if (nodeName.includes('Sheets')) return 'n8n-nodes-base.googleSheets';
            if (nodeName.includes('Drive')) return 'n8n-nodes-base.googleDrive';
        }

        // Return the raw name if we can't determine specific type
        return nodeName || null;
    }

    // Show tooltip
    function showTooltip(event, nodeType) {
        // Send message to get node info
        window.postMessage({
            type: 'FLOWGENT_SHOW_TOOLTIP',
            nodeType: nodeType,
            position: {
                x: event.clientX,
                y: event.clientY
            }
        }, '*');
    }

    // Hide tooltip
    function hideTooltip() {
        window.postMessage({
            type: 'FLOWGENT_HIDE_TOOLTIP'
        }, '*');
    }

    // Initialize when page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            if (detectN8n()) {
                setTimeout(initInformationHand, 1000); // Wait for n8n to load
            }
        });
    } else {
        if (detectN8n()) {
            setTimeout(initInformationHand, 1000);
        }
    }

})();
