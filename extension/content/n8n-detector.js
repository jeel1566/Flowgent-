/**
 * n8n node detector content script
 * Detects n8n workflow canvas and node elements
 */

(function () {
    'use strict';

    let isN8nPage = false;
    let observer = null;
    let tooltipScript = null;

    // Check if this is an n8n page
    function detectN8n() {
        // Look for n8n-specific elements
        const n8nIndicators = [
            '[data-test-id="canvas"]',
            '[data-test-id="node-view-root"]',
            '.node-view-root',
            '.jtk-connector',
            '#node-creator',
            '.n8n-node',
            '[class*="NodeViewWrapper"]',
            '[class*="WorkflowCanvas"]'
        ];

        for (const selector of n8nIndicators) {
            if (document.querySelector(selector)) {
                isN8nPage = true;
                return true;
            }
        }

        // Check URL patterns
        const url = window.location.href.toLowerCase();
        if (url.includes('/workflow/') ||
            url.includes('n8n.io') ||
            url.includes('n8n.cloud') ||
            window.location.hostname.includes('n8n')) {
            isN8nPage = true;
            return true;
        }

        return false;
    }

    // Initialize the Information Hand feature
    function initInformationHand() {
        if (!isN8nPage) {
            console.log('Flowgent: Not an n8n page');
            return;
        }

        console.log('Flowgent: n8n page detected! Initializing Information Hand...');

        // Inject tooltip resources
        injectTooltipResources();

        // Watch for node elements
        setTimeout(() => {
            watchForNodes();
            // Scan existing nodes
            scanAndAttach();
        }, 2000);
    }

    // Inject tooltip script and stylesheet
    function injectTooltipResources() {
        // Inject inline styles for tooltip (more reliable)
        const style = document.createElement('style');
        style.textContent = `
            .flowgent-tooltip {
                transition: opacity 0.2s ease;
            }
            .flowgent-tooltip:hover {
                opacity: 1 !important;
            }
            .flowgent-node-highlight {
                outline: 2px solid #8b5cf6 !important;
                outline-offset: 2px;
            }
        `;
        document.head.appendChild(style);

        // Inject tooltip script
        if (!tooltipScript) {
            tooltipScript = document.createElement('script');
            tooltipScript.src = chrome.runtime.getURL('content/tooltip.js');
            tooltipScript.onload = () => console.log('Flowgent: Tooltip script loaded');
            tooltipScript.onerror = (e) => console.error('Flowgent: Failed to load tooltip script', e);
            document.body.appendChild(tooltipScript);
        }
    }

    // Scan and attach to all nodes
    function scanAndAttach() {
        console.log('Flowgent: Scanning for n8n nodes...');
        const attached = attachTooltipHandlers(document.body);
        console.log(`Flowgent: Attached handlers to ${attached} nodes`);
    }

    // Watch for n8n node elements
    function watchForNodes() {
        if (observer) return;

        observer = new MutationObserver((mutations) => {
            let shouldScan = false;
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length > 0) {
                    shouldScan = true;
                }
            });
            if (shouldScan) {
                // Debounce
                setTimeout(scanAndAttach, 500);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // Attach tooltip event handlers to nodes
    function attachTooltipHandlers(container) {
        let count = 0;

        // Updated selectors for modern n8n
        const nodeSelectors = [
            '[data-test-id^="canvas-node"]',
            '[data-test-id*="node"]',
            '.vue-flow__node',
            '[class*="CanvasNode"]',
            '[class*="node-wrapper"]',
            '.node-wrapper',
            '[data-node-name]',
            '[data-node-type]'
        ];

        const allNodes = new Set();

        nodeSelectors.forEach(selector => {
            try {
                const nodes = container.querySelectorAll(selector);
                nodes.forEach(n => allNodes.add(n));
            } catch (e) { }
        });

        allNodes.forEach(nodeElement => {
            if (nodeElement.dataset.flowgentAttached) return;

            const nodeType = extractNodeType(nodeElement);
            if (nodeType) {
                nodeElement.dataset.flowgentAttached = 'true';

                nodeElement.addEventListener('mouseenter', (e) => {
                    e.stopPropagation();
                    nodeElement.classList.add('flowgent-node-highlight');
                    showTooltip(e, nodeType);
                });

                nodeElement.addEventListener('mouseleave', (e) => {
                    nodeElement.classList.remove('flowgent-node-highlight');
                    hideTooltip();
                });

                count++;
            }
        });

        return count;
    }

    // Extract node type from element
    function extractNodeType(element) {
        // Try data attributes first
        let nodeType = element.dataset.nodeType ||
            element.dataset.nodeName ||
            element.getAttribute('data-node-type') ||
            element.getAttribute('data-name');

        if (nodeType) {
            return normalizeNodeType(nodeType);
        }

        // Try to get from text content or title
        const title = element.querySelector('[class*="title"], [class*="name"], .node-title, .node-name');
        if (title) {
            const text = title.textContent.trim();
            return normalizeNodeType(text);
        }

        // Try class names
        const className = element.className || '';
        const match = className.match(/node-(\w+)/i);
        if (match) {
            return normalizeNodeType(match[1]);
        }

        return null;
    }

    // Normalize node type to n8n format
    function normalizeNodeType(name) {
        if (!name) return null;

        const cleaned = name.trim().replace(/\s+/g, '');

        // If already in n8n format
        if (cleaned.startsWith('n8n-nodes-')) {
            return cleaned;
        }

        // Map common names to node types
        const nodeMap = {
            'httprequest': 'n8n-nodes-base.httpRequest',
            'http': 'n8n-nodes-base.httpRequest',
            'webhook': 'n8n-nodes-base.webhook',
            'set': 'n8n-nodes-base.set',
            'if': 'n8n-nodes-base.if',
            'switch': 'n8n-nodes-base.switch',
            'code': 'n8n-nodes-base.code',
            'function': 'n8n-nodes-base.function',
            'slack': 'n8n-nodes-base.slack',
            'googlesheets': 'n8n-nodes-base.googleSheets',
            'gmail': 'n8n-nodes-base.gmail',
            'schedule': 'n8n-nodes-base.scheduleTrigger',
            'scheduletrigger': 'n8n-nodes-base.scheduleTrigger',
            'cron': 'n8n-nodes-base.cron',
            'merge': 'n8n-nodes-base.merge',
            'split': 'n8n-nodes-base.splitInBatches',
            'postgres': 'n8n-nodes-base.postgres',
            'mysql': 'n8n-nodes-base.mysql',
            'notion': 'n8n-nodes-base.notion',
            'airtable': 'n8n-nodes-base.airtable',
            'discord': 'n8n-nodes-base.discord',
            'telegram': 'n8n-nodes-base.telegram',
            'openai': 'n8n-nodes-base.openai',
        };

        const lower = cleaned.toLowerCase();
        if (nodeMap[lower]) {
            return nodeMap[lower];
        }

        // Default: assume it's a valid node type
        return `n8n-nodes-base.${cleaned}`;
    }

    // Show tooltip
    function showTooltip(event, nodeType) {
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

    // Initialize
    function init() {
        console.log('Flowgent: Content script initializing...');

        // Check immediately
        if (detectN8n()) {
            initInformationHand();
        }

        // Also check after short delay (for SPA)
        setTimeout(() => {
            if (!isN8nPage && detectN8n()) {
                initInformationHand();
            }
        }, 3000);

        // Re-check on navigation (for SPA)
        let lastUrl = location.href;
        new MutationObserver(() => {
            if (location.href !== lastUrl) {
                lastUrl = location.href;
                if (detectN8n()) {
                    setTimeout(initInformationHand, 1000);
                }
            }
        }).observe(document, { subtree: true, childList: true });
    }

    // Listen for messages from injected script
    window.addEventListener('message', async (event) => {
        if (event.source !== window) return;

        if (event.data.type === 'FLOWGENT_FETCH_NODE_INFO') {
            const { nodeType, requestId } = event.data;

            try {
                // Check cache first via background
                const cacheRes = await chrome.runtime.sendMessage({
                    action: 'getNodeInfo',
                    data: { nodeType }
                });

                if (cacheRes.success) {
                    window.postMessage({
                        type: 'FLOWGENT_NODE_INFO_RESPONSE',
                        requestId,
                        success: true,
                        info: cacheRes.info
                    }, '*');
                    return;
                }

                // Fetch via background
                const fetchRes = await chrome.runtime.sendMessage({
                    action: 'fetchNodeInfo',
                    data: { nodeType }
                });

                window.postMessage({
                    type: 'FLOWGENT_NODE_INFO_RESPONSE',
                    requestId,
                    success: fetchRes.success,
                    info: fetchRes.info,
                    error: fetchRes.error
                }, '*');

            } catch (error) {
                window.postMessage({
                    type: 'FLOWGENT_NODE_INFO_RESPONSE',
                    requestId,
                    success: false,
                    error: error.message
                }, '*');
            }
        }
    });

    // Run init
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
