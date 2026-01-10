/**
 * n8n node detector content script - Enhanced Information Hand
 * Detects n8n workflow canvas and node elements with improved selectors
 */

(function () {
    'use strict';

    const N8nDetector = {
        isN8nPage: false,
        observer: null,
        tooltipScript: null,
        retryCount: 0,
        maxRetries: 5,

        // n8n page indicators
        n8nIndicators: [
            // Modern n8n (Vue Flow based)
            '[data-test-id="canvas"]',
            '[data-test-id="node-view-root"]',
            '.node-view-root',
            '.jtk-connector',
            '#node-creator',
            '.n8n-node',
            '[class*="NodeViewWrapper"]',
            '[class*="WorkflowCanvas"]',
            // Vue Flow canvas
            '.vue-flow__node',
            '.vue-flow__edge',
            '[class*="VueFlow"]',
            // n8n custom nodes
            '[data-node-name]',
            '[data-node-type]',
            '[data-test-id*="node"]',
            // Common n8n elements
            '.node-connection',
            '.workflow-canvas',
            '[class*="canvas-wrapper"]',
            // Node creator panel
            '.node-creator-search',
            '[class*="NodeCreator"]'
        ],

        /**
         * Initialize the detector
         */
        init() {
            console.log('Flowgent: Initializing Information Hand detector...');

            // Check immediately
            if (this.detectN8n()) {
                this.initInformationHand();
                return;
            }

            // Retry for SPA applications
            this.retryCheck();
        },

        /**
         * Retry detection with exponential backoff
         */
        retryCheck() {
            if (this.retryCount >= this.maxRetries) {
                console.log('Flowgent: Max retries reached, not an n8n page');
                return;
            }

            this.retryCount++;
            const delay = Math.min(1000 * Math.pow(2, this.retryCount), 10000);

            setTimeout(() => {
                if (!this.isN8nPage && this.detectN8n()) {
                    this.initInformationHand();
                } else {
                    this.retryCheck();
                }
            }, delay);
        },

        /**
         * Detect if this is an n8n page
         */
        detectN8n() {
            // Check URL patterns first (fastest)
            const url = window.location.href.toLowerCase();
            const n8nPatterns = [
                '/workflow/',
                'n8n.io',
                'n8n.cloud',
                '.n8n.',
                '/instance/'
            ];

            for (const pattern of n8nPatterns) {
                if (url.includes(pattern)) {
                    this.isN8nPage = true;
                    console.log('Flowgent: n8n URL pattern detected:', pattern);
                    return true;
                }
            }

            // Check for n8n elements
            for (const selector of this.n8nIndicators) {
                try {
                    if (document.querySelector(selector)) {
                        this.isN8nPage = true;
                        console.log('Flowgent: n8n element detected:', selector);
                        return true;
                    }
                } catch (e) {
                    // Invalid selector, skip
                }
            }

            // Check page title
            if (document.title && (
                document.title.toLowerCase().includes('n8n') ||
                document.title.toLowerCase().includes('workflow')
            )) {
                this.isN8nPage = true;
                console.log('Flowgent: n8n title detected');
                return true;
            }

            return false;
        },

        /**
         * Initialize Information Hand on n8n page
         */
        initInformationHand() {
            if (!this.isN8nPage) return;

            console.log('Flowgent: n8n page detected! Initializing Information Hand...');

            // Inject tooltip resources
            this.injectTooltipResources();

            // Set up node watching with debounce
            this.setupNodeWatcher();

            // Initial scan
            this.scheduleNodeScan();

            // Monitor for navigation in SPA
            this.setupNavigationMonitor();

            console.log('Flowgent: Information Hand ready');
        },

        /**
         * Inject tooltip script and styles
         */
        injectTooltipResources() {
            // Inject tooltip script
            if (!this.tooltipScript) {
                this.tooltipScript = document.createElement('script');
                this.tooltipScript.src = chrome.runtime.getURL('content/tooltip.js');
                this.tooltipScript.onload = () => console.log('Flowgent: Tooltip script loaded');
                this.tooltipScript.onerror = (e) => console.error('Flowgent: Failed to load tooltip script', e);
                document.body.appendChild(this.tooltipScript);
            }
        },

        /**
         * Set up mutation observer for dynamic nodes
         */
        setupNodeWatcher() {
            if (this.observer) return;

            let debounceTimer = null;

            this.observer = new MutationObserver((mutations) => {
                // Debounce to avoid excessive scanning
                if (debounceTimer) {
                    clearTimeout(debounceTimer);
                }

                debounceTimer = setTimeout(() => {
                    // Only scan if nodes were added
                    const hasNewNodes = mutations.some(m => 
                        m.addedNodes.length > 0 && 
                        !m.addedNodes[0].classList?.contains('flowgent-tooltip')
                    );

                    if (hasNewNodes) {
                        this.scanAndAttach();
                    }
                }, 500);
            });

            this.observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        },

        /**
         * Schedule node scan (debounced)
         */
        scheduleNodeScan() {
            // Initial scan after DOM is ready
            setTimeout(() => this.scanAndAttach(), 500);

            // Additional scan after resources load
            setTimeout(() => this.scanAndAttach(), 2000);

            // Periodic scan for late-loading nodes
            setTimeout(() => this.scanAndAttach(), 5000);
        },

        /**
         * Monitor for navigation in single-page applications
         */
        setupNavigationMonitor() {
            let lastUrl = location.href;

            new MutationObserver(() => {
                if (location.href !== lastUrl) {
                    lastUrl = location.href;
                    console.log('Flowgent: URL changed, reinitializing...');
                    
                    // Reset state
                    this.isN8nPage = false;
                    this.retryCount = 0;
                    
                    // Re-detect
                    setTimeout(() => {
                        if (this.detectN8n()) {
                            this.scanAndAttach();
                        }
                    }, 1000);
                }
            }).observe(document, { subtree: true, childList: true });
        },

        /**
         * Scan and attach handlers to all nodes
         */
        scanAndAttach() {
            if (!this.isN8nPage) return;

            console.log('Flowgent: Scanning for n8n nodes...');
            
            const nodes = this.findNodeElements();
            console.log(`Flowgent: Found ${nodes.length} potential nodes`);

            let attached = 0;
            nodes.forEach(nodeElement => {
                if (this.attachHandler(nodeElement)) {
                    attached++;
                }
            });

            console.log(`Flowgent: Attached handlers to ${attached} nodes`);
        },

        /**
         * Find all node elements on the page
         */
        findNodeElements() {
            const allNodes = new Set();

            // Enhanced selectors for modern n8n
            const nodeSelectors = [
                // Vue Flow nodes (modern n8n)
                '.vue-flow__node',
                '[class*="CanvasNode"]',
                '[class*="NodeWrapper"]',
                '[class*="node-wrapper"]',
                // Data test IDs
                '[data-test-id^="canvas-node"]',
                '[data-test-id*="node"]',
                '[data-node-name]',
                '[data-node-type]',
                // Legacy selectors
                '.node-wrapper',
                '.n8n-node',
                // Connection points (might indicate nodes nearby)
                '.jtk-connector',
                '[class*="connector"]'
            ];

            // First, try to find the canvas container
            const canvas = this.findCanvas();
            if (canvas) {
                nodeSelectors.forEach(selector => {
                    try {
                        canvas.querySelectorAll(selector).forEach(n => allNodes.add(n));
                    } catch (e) {}
                });
            }

            // Also search entire document for safety
            nodeSelectors.forEach(selector => {
                try {
                    document.querySelectorAll(selector).forEach(n => allNodes.add(n));
                } catch (e) {}
            });

            // Filter out non-node elements
            return Array.from(allNodes).filter(el => this.isLikelyNode(el));
        },

        /**
         * Find the workflow canvas element
         */
        findCanvas() {
            const canvasSelectors = [
                '[data-test-id="canvas"]',
                '.workflow-canvas',
                '[class*="WorkflowCanvas"]',
                '[class*="canvas-wrapper"]',
                '.node-view-root',
                '.vue-flow'
            ];

            for (const selector of canvasSelectors) {
                const canvas = document.querySelector(selector);
                if (canvas) return canvas;
            }

            return document.body;
        },

        /**
         * Check if element is likely an n8n node
         */
        isLikelyNode(element) {
            // Skip non-elements
            if (element.nodeType !== Node.ELEMENT_NODE) return false;

            // Skip our own tooltip
            if (element.classList.contains('flowgent-tooltip')) return false;

            // Skip very small elements
            const rect = element.getBoundingClientRect();
            if (rect.width < 40 || rect.height < 20) return false;

            // Skip if already processed
            if (element.dataset.flowgentAttached) return false;

            // Check if element has node-like characteristics
            const className = element.className || '';
            const id = element.id || '';
            const dataAttrs = element.dataset;

            // Has node data attribute
            if (dataAttrs.nodeName || dataAttrs.nodeType || dataAttrs['test-id']?.includes('node')) {
                return true;
            }

            // Has node-related class
            const nodeClassPatterns = [
                /node/i,
                /vue-flow__node/i,
                /canvas.*node/i,
                /node.*wrapper/i
            ];

            for (const pattern of nodeClassPatterns) {
                if (pattern.test(className) || pattern.test(id)) {
                    return true;
                }
            }

            return false;
        },

        /**
         * Attach tooltip handler to a node element
         */
        attachHandler(nodeElement) {
            if (nodeElement.dataset.flowgentAttached) return false;

            const nodeType = this.extractNodeType(nodeElement);
            if (!nodeType) return false;

            nodeElement.dataset.flowgentAttached = 'true';
            nodeElement.dataset.flowgentNodeType = nodeType;

            // Mouse events with throttling
            let hoverTimeout = null;
            let lastMoveTime = 0;
            const HOVER_DELAY = 100;
            const MOVE_THROTTLE = 50;

            nodeElement.addEventListener('mouseenter', (e) => {
                const now = Date.now();
                if (now - lastMoveTime < MOVE_THROTTLE) return;
                lastMoveTime = now;

                hoverTimeout = setTimeout(() => {
                    this.showTooltip(e, nodeType);
                    nodeElement.classList.add('flowgent-node-highlight');
                }, HOVER_DELAY);
            });

            nodeElement.addEventListener('mouseleave', (e) => {
                clearTimeout(hoverTimeout);
                
                // Delay hiding to allow moving to tooltip
                setTimeout(() => {
                    if (!this.isOverTooltip(e.relatedTarget)) {
                        nodeElement.classList.remove('flowgent-node-highlight');
                        this.hideTooltip();
                    }
                }, 100);
            });

            nodeElement.addEventListener('mousemove', (e) => {
                if (this.isTooltipVisible()) {
                    this.updateTooltipPosition(e.clientX, e.clientY);
                }
            });

            nodeElement.addEventListener('click', (e) => {
                this.handleNodeClick(nodeType, nodeElement);
            });

            // Keyboard accessibility
            nodeElement.setAttribute('tabindex', '0');
            nodeElement.setAttribute('role', 'button');
            nodeElement.setAttribute('aria-label', `Node: ${nodeType}`);

            nodeElement.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.showTooltip({
                        clientX: nodeElement.getBoundingClientRect().left + 100,
                        clientY: nodeElement.getBoundingClientRect().top + 50
                    }, nodeType);
                }
                if (e.key === 'Escape') {
                    this.hideTooltip();
                }
            });

            return true;
        },

        /**
         * Extract node type from element
         */
        extractNodeType(element) {
            // Priority 1: Data attributes
            const dataType = element.dataset.nodeType ||
                            element.dataset.nodeName ||
                            element.getAttribute('data-node-type') ||
                            element.getAttribute('data-name');

            if (dataType) {
                return this.normalizeNodeType(dataType);
            }

            // Priority 2: Element attributes
            const titleEl = element.querySelector('[class*="title"], [class*="name"], .node-title, .node-name');
            if (titleEl) {
                const text = titleEl.textContent.trim();
                if (text) {
                    return this.normalizeNodeType(text);
                }
            }

            // Priority 3: Class name parsing
            const className = element.className || '';
            const classMatch = className.match(/node[-_]?(\w+)/i);
            if (classMatch) {
                return this.normalizeNodeType(classMatch[1]);
            }

            // Priority 4: Test ID parsing
            const testId = element.getAttribute('data-test-id') || '';
            if (testId.includes('node')) {
                const parts = testId.split('node');
                if (parts.length > 1) {
                    return this.normalizeNodeType(parts[1]);
                }
            }

            return null;
        },

        /**
         * Normalize node type to n8n format
         */
        normalizeNodeType(name) {
            if (!name) return null;

            const cleaned = name.trim().replace(/\s+/g, '');

            // Already in n8n format
            if (cleaned.startsWith('n8n-nodes-')) {
                return cleaned;
            }

            // Map common names
            const nodeMap = {
                'httprequest': 'n8n-nodes-base.httpRequest',
                'http': 'n8n-nodes-base.httpRequest',
                'webhook': 'n8n-nodes-base.webhook',
                'set': 'n8n-nodes-base.set',
                'if': 'n8n-nodes-base.if',
                'switch': 'n8n-nodes-base.switch',
                'code': 'n8n-nodes-base.code',
                'function': 'n8n-nodes-base.function',
                'functionitem': 'n8n-nodes-base.functionItem',
                'slack': 'n8n-nodes-base.slack',
                'googlesheets': 'n8n-nodes-base.googleSheets',
                'gmail': 'n8n-nodes-base.gmail',
                'schedule': 'n8n-nodes-base.scheduleTrigger',
                'scheduletrigger': 'n8n-nodes-base.scheduleTrigger',
                'cron': 'n8n-nodes-base.cron',
                'merge': 'n8n-nodes-base.merge',
                'splitinbatches': 'n8n-nodes-base.splitInBatches',
                'postgres': 'n8n-nodes-base.postgres',
                'mysql': 'n8n-nodes-base.mysql',
                'notion': 'n8n-nodes-base.notion',
                'airtable': 'n8n-nodes-base.airtable',
                'discord': 'n8n-nodes-base.discord',
                'telegram': 'n8n-nodes-base.telegram',
                'openai': 'n8n-nodes-base.openai',
                'gpt': 'n8n-nodes-base.openai',
                'email': 'n8n-nodes-base.emailReadImap',
                'imap': 'n8n-nodes-base.emailReadImap',
                'smtp': 'n8n-nodes-base.emailSend',
                'filter': 'n8n-nodes-base.filter',
                'editfields': 'n8n-nodes-base.editFields',
                'setnode': 'n8n-nodes-base.set',
                'wait': 'n8n-nodes-base.wait',
                'nope': 'n8n-nodes-base.noOp',
                'noop': 'n8n-nodes-base.noOp',
                'errortrigger': 'n8n-nodes-base.errorTrigger',
                'httprequest': 'n8n-nodes-base.httpRequest'
            };

            const lower = cleaned.toLowerCase();
            if (nodeMap[lower]) {
                return nodeMap[lower];
            }

            // Default format
            return `n8n-nodes-base.${cleaned}`;
        },

        /**
         * Show tooltip at position
         */
        showTooltip(event, nodeType) {
            window.postMessage({
                type: 'FLOWGENT_SHOW_TOOLTIP',
                nodeType,
                position: {
                    x: event.clientX || event.pageX,
                    y: event.clientY || event.pageY
                }
            }, '*');
        },

        /**
         * Update tooltip position (for mouse following)
         */
        updateTooltipPosition(x, y) {
            window.postMessage({
                type: 'FLOWGENT_UPDATE_POSITION',
                position: { x, y }
            }, '*');
        },

        /**
         * Hide tooltip
         */
        hideTooltip() {
            window.postMessage({
                type: 'FLOWGENT_HIDE_TOOLTIP'
            }, '*');
        },

        /**
         * Handle node click
         */
        handleNodeClick(nodeType, element) {
            // Could expand tooltip or show more options
            console.log('Flowgent: Node clicked:', nodeType);
        },

        /**
         * Check if mouse is over tooltip
         */
        isOverTooltip(target) {
            if (!target) return false;
            return target.classList?.contains('flowgent-tooltip') ||
                   target.closest('.flowgent-tooltip');
        },

        /**
         * Check if tooltip is visible
         */
        isTooltipVisible() {
            const tooltip = document.querySelector('.flowgent-tooltip');
            return tooltip && tooltip.classList.contains('visible');
        },

        /**
         * Handle messages from injected scripts
         */
        async handleMessage(event) {
            if (event.source !== window) return;

            if (event.data.type === 'FLOWGENT_FETCH_NODE_INFO') {
                const { nodeType, requestId, previewType } = event.data;

                try {
                    // Check cache first
                    const cacheKey = `${previewType || 'brief'}:${nodeType}`;
                    const cacheRes = await this.getCachedNodeInfo(nodeType, previewType);

                    if (cacheRes) {
                        this.sendNodeInfoResponse(requestId, true, cacheRes);
                        return;
                    }

                    // Fetch from background
                    const fetchRes = await this.fetchNodeInfo(nodeType, previewType);

                    if (fetchRes.success) {
                        // Cache the result
                        await this.cacheNodeInfo(nodeType, fetchRes.info, previewType);
                        this.sendNodeInfoResponse(requestId, true, fetchRes.info);
                    } else {
                        this.sendNodeInfoResponse(requestId, false, null, fetchRes.error);
                    }
                } catch (error) {
                    this.sendNodeInfoResponse(requestId, false, null, error.message);
                }
            } else if (event.data.type === 'FLOWGENT_ASK_AI') {
                // Open side panel with context
                if (chrome.runtime?.id) {
                    chrome.runtime.sendMessage({
                        action: 'openSidePanelWithContext',
                        context: event.data.context
                    });
                }
            }
        },

        /**
         * Send node info response to tooltip
         */
        sendNodeInfoResponse(requestId, success, info, error = null) {
            window.postMessage({
                type: 'FLOWGENT_NODE_INFO_RESPONSE',
                requestId,
                success,
                info,
                error
            }, '*');
        },

        /**
         * Get cached node info
         */
        async getCachedNodeInfo(nodeType, previewType = 'brief') {
            try {
                if (!chrome.runtime?.sendMessage) return null;

                const res = await chrome.runtime.sendMessage({
                    action: 'getNodeInfo',
                    data: { nodeType, previewType }
                });

                if (res?.success && res?.info) {
                    // Check cache age (1 hour for brief, 24 hours for full)
                    const maxAge = previewType === 'full' ? 24 * 60 * 60 * 1000 : 60 * 60 * 1000;
                    if (res.cached && res.age < maxAge) {
                        return res.info;
                    }
                }
            } catch (e) {
                // Cache miss or error
            }
            return null;
        },

        /**
         * Cache node info
         */
        async cacheNodeInfo(nodeType, info, previewType = 'brief') {
            try {
                if (!chrome.runtime?.sendMessage) return;

                await chrome.runtime.sendMessage({
                    action: 'cacheNodeInfo',
                    data: { nodeType, info, previewType }
                });
            } catch (e) {
                console.error('Failed to cache node info:', e);
            }
        },

        /**
         * Fetch node info from background
         */
        async fetchNodeInfo(nodeType, previewType = 'brief') {
            try {
                if (!chrome.runtime?.sendMessage) {
                    // Fallback to direct fetch
                    return this.directFetchNodeInfo(nodeType, previewType);
                }

                return await chrome.runtime.sendMessage({
                    action: 'fetchNodePreview',
                    data: { nodeType, previewType }
                });
            } catch (e) {
                return this.directFetchNodeInfo(nodeType, previewType);
            }
        },

        /**
         * Direct fetch node info (fallback)
         */
        async directFetchNodeInfo(nodeType, previewType) {
            try {
                const settings = await chrome.storage.local.get('backendUrl');
                const baseUrl = settings.backendUrl || 'http://localhost:8000';

                const response = await fetch(
                    `${baseUrl}/api/node-preview/${encodeURIComponent(nodeType)}?preview_type=${previewType}`
                );

                if (!response.ok) {
                    throw new Error(`Backend error: ${response.status}`);
                }

                const data = await response.json();
                return { success: data.success, info: data, error: data.error };
            } catch (error) {
                return { success: false, error: error.message };
            }
        }
    };

    // Set up message handling
    window.addEventListener('message', (event) => {
        N8nDetector.handleMessage(event);
    });

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => N8nDetector.init());
    } else {
        N8nDetector.init();
    }

    // Export for debugging
    window.FlowgentDetector = N8nDetector;

})();
