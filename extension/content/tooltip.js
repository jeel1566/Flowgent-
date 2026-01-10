/**
 * Enhanced Information Hand tooltip functionality
 * Features: Mouse-following, click-to-expand, keyboard navigation
 * This script runs in the page context and communicates with content script
 */

(function () {
    'use strict';

    const Tooltip = {
        element: null,
        currentNodeType: null,
        currentPosition: { x: 0, y: 0 },
        fetchTimeout: null,
        pendingRequests: new Map(),
        isExpanded: false,
        isVisible: false,
        mouseMoveThrottle: null,
        hoverStartTime: 0,

        // Configuration
        config: {
            delay: 100,           // ms before showing tooltip
            expandDelay: 500,     // ms before expanding on click
            followMouse: true,    // follow mouse position
            fadeDuration: 200,    // ms for fade animations
            maxWidth: 380,
            minWidth: 280,
            expandWidth: 500
        },

        /**
         * Initialize the tooltip system
         */
        init() {
            this.createTooltip();
            this.bindEvents();
            this.bindKeyboard();
            console.log('Flowgent: Enhanced Information Hand initialized');
        },

        /**
         * Create tooltip DOM element
         */
        createTooltip() {
            if (this.element) return;

            this.element = document.createElement('div');
            this.element.className = 'flowgent-tooltip';
            this.element.innerHTML = this.getTemplate('loading');
            document.body.appendChild(this.element);
            this.addStyles();
        },

        /**
         * Add CSS styles for tooltip
         */
        addStyles() {
            const style = document.createElement('style');
            style.textContent = `
                .flowgent-tooltip {
                    display: none;
                    position: fixed;
                    z-index: 2147483647;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    border: 1px solid rgba(139, 92, 246, 0.3);
                    border-radius: 16px;
                    padding: 0;
                    max-width: 380px;
                    min-width: 280px;
                    color: #fff;
                    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 14px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(139, 92, 246, 0.1);
                    backdrop-filter: blur(20px);
                    pointer-events: auto;
                    transition: opacity ${this.config.fadeDuration}ms ease, transform ${this.config.fadeDuration}ms ease, max-width ${this.config.fadeDuration}ms ease;
                    opacity: 0;
                    transform: translateY(10px);
                }

                .flowgent-tooltip.visible {
                    display: block;
                    opacity: 1;
                    transform: translateY(0);
                }

                .flowgent-tooltip.expanded {
                    max-width: 500px;
                }

                /* Header section */
                .tooltip-header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 16px 20px;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                    background: rgba(139, 92, 246, 0.05);
                    border-radius: 16px 16px 0 0;
                }

                .tooltip-icon {
                    font-size: 32px;
                    line-height: 1;
                }

                .tooltip-title-section {
                    flex: 1;
                    min-width: 0;
                }

                .tooltip-title {
                    margin: 0;
                    font-size: 16px;
                    font-weight: 600;
                    color: #fff;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .tooltip-meta {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-top: 4px;
                    font-size: 12px;
                    color: rgba(255,255,255,0.6);
                }

                .tooltip-category {
                    background: rgba(139, 92, 246, 0.2);
                    color: #c4b5fd;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 11px;
                }

                .tooltip-popularity {
                    color: #fbbf24;
                }

                /* Close button */
                .tooltip-close {
                    position: absolute;
                    top: 12px;
                    right: 12px;
                    width: 24px;
                    height: 24px;
                    border: none;
                    background: rgba(255,255,255,0.1);
                    color: rgba(255,255,255,0.7);
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    transition: all 0.2s;
                }

                .tooltip-close:hover {
                    background: rgba(255,255,255,0.2);
                    color: #fff;
                }

                /* Body section */
                .tooltip-body {
                    padding: 16px 20px;
                    line-height: 1.6;
                    max-height: 200px;
                    overflow-y: auto;
                }

                .tooltip-body::-webkit-scrollbar {
                    width: 4px;
                }

                .tooltip-body::-webkit-scrollbar-track {
                    background: transparent;
                }

                .tooltip-body::-webkit-scrollbar-thumb {
                    background: rgba(139, 92, 246, 0.5);
                    border-radius: 4px;
                }

                /* Description */
                .tooltip-description {
                    margin: 0;
                    color: rgba(255,255,255,0.85);
                    font-size: 14px;
                }

                /* Use cases */
                .tooltip-section {
                    margin-top: 16px;
                    padding-top: 16px;
                    border-top: 1px solid rgba(255,255,255,0.1);
                }

                .tooltip-section-title {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 12px;
                    font-weight: 600;
                    color: #a78bfa;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 8px;
                }

                .tooltip-use-cases {
                    list-style: none;
                    padding: 0;
                    margin: 0;
                }

                .tooltip-use-cases li {
                    padding: 6px 0;
                    padding-left: 20px;
                    position: relative;
                    color: rgba(255,255,255,0.8);
                    font-size: 13px;
                }

                .tooltip-use-cases li::before {
                    content: '✓';
                    position: absolute;
                    left: 0;
                    color: #34d399;
                    font-size: 12px;
                }

                /* Best practices */
                .tooltip-best-practices {
                    list-style: none;
                    padding: 0;
                    margin: 0;
                }

                .tooltip-best-practices li {
                    padding: 6px 0;
                    padding-left: 20px;
                    position: relative;
                    color: rgba(255,255,255,0.8);
                    font-size: 13px;
                }

                .tooltip-best-practices li::before {
                    content: '💡';
                    position: absolute;
                    left: 0;
                    font-size: 12px;
                }

                /* Expanded content (hidden by default) */
                .tooltip-expanded-content {
                    display: none;
                    padding: 16px 20px;
                    border-top: 1px solid rgba(255,255,255,0.1);
                    background: rgba(0,0,0,0.2);
                }

                .flowgent-tooltip.expanded .tooltip-expanded-content {
                    display: block;
                }

                /* Parameters table */
                .tooltip-parameters {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12px;
                }

                .tooltip-parameters th {
                    text-align: left;
                    padding: 8px;
                    color: #a78bfa;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }

                .tooltip-parameters td {
                    padding: 8px;
                    color: rgba(255,255,255,0.8);
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                }

                /* Example code */
                .tooltip-example {
                    background: rgba(0,0,0,0.3);
                    border-radius: 8px;
                    padding: 12px;
                    font-family: 'Monaco', 'Menlo', monospace;
                    font-size: 12px;
                    overflow-x: auto;
                    color: #a5f3fc;
                }

                /* Actions footer */
                .tooltip-actions {
                    display: flex;
                    gap: 8px;
                    padding: 12px 20px;
                    border-top: 1px solid rgba(255,255,255,0.1);
                    background: rgba(139, 92, 246, 0.05);
                    border-radius: 0 0 16px 16px;
                }

                .tooltip-action-btn {
                    flex: 1;
                    padding: 8px 12px;
                    border: 1px solid rgba(139, 92, 246, 0.4);
                    background: rgba(139, 92, 246, 0.1);
                    color: #c4b5fd;
                    border-radius: 8px;
                    font-size: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                }

                .tooltip-action-btn:hover {
                    background: rgba(139, 92, 246, 0.2);
                    border-color: rgba(139, 92, 246, 0.6);
                }

                .tooltip-action-btn.primary {
                    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
                    border: none;
                    color: #fff;
                }

                .tooltip-action-btn.primary:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
                }

                /* Loading animation */
                .tooltip-loading {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    padding: 40px;
                    color: rgba(255,255,255,0.6);
                }

                .tooltip-loading-dots {
                    display: flex;
                    gap: 4px;
                }

                .tooltip-loading-dots span {
                    width: 8px;
                    height: 8px;
                    background: #8b5cf6;
                    border-radius: 50%;
                    animation: tooltipBounce 1.4s infinite ease-in-out;
                }

                .tooltip-loading-dots span:nth-child(1) { animation-delay: 0s; }
                .tooltip-loading-dots span:nth-child(2) { animation-delay: 0.16s; }
                .tooltip-loading-dots span:nth-child(3) { animation-delay: 0.32s; }

                @keyframes tooltipBounce {
                    0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
                    40% { transform: scale(1); opacity: 1; }
                }

                /* Error state */
                .tooltip-error {
                    text-align: center;
                    padding: 30px;
                    color: #f87171;
                }

                .tooltip-error-icon {
                    font-size: 40px;
                    margin-bottom: 12px;
                }

                /* Highlight effect */
                .flowgent-node-highlight {
                    outline: 2px solid #8b5cf6 !important;
                    outline-offset: 3px !important;
                    border-radius: 8px !important;
                    transition: outline 0.2s ease;
                }

                /* Expand hint */
                .tooltip-expand-hint {
                    position: absolute;
                    bottom: 60px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(139, 92, 246, 0.9);
                    color: #fff;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 11px;
                    white-space: nowrap;
                    opacity: 0;
                    transition: opacity 0.3s;
                }

                .flowgent-tooltip.expanded .tooltip-expand-hint {
                    display: none;
                }

                /* Keyboard hint */
                .tooltip-keyboard-hint {
                    position: absolute;
                    bottom: 60px;
                    right: 20px;
                    display: flex;
                    gap: 4px;
                    font-size: 10px;
                    color: rgba(255,255,255,0.4);
                }

                .tooltip-key {
                    padding: 2px 6px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 4px;
                }
            `;
            document.head.appendChild(style);
        },

        /**
         * Get HTML template for different states
         */
        getTemplate(state, data = null) {
            switch (state) {
                case 'loading':
                    return `
                        <div class="tooltip-loading">
                            <span>✨</span>
                            <span>Loading node info</span>
                            <div class="tooltip-loading-dots"><span></span><span></span><span></span></div>
                        </div>
                    `;

                case 'error':
                    return `
                        <div class="tooltip-error">
                            <div class="tooltip-error-icon">⚠️</div>
                            <strong>Unable to load</strong>
                            <p style="margin: 8px 0 0; opacity: 0.7; font-size: 13px;">${data?.message || 'Unknown error'}</p>
                        </div>
                    `;

                case 'content':
                    const preview = data?.preview || {};
                    const icon = preview.icon_emoji || '📦';
                    const displayName = preview.display_name || preview.node_type || 'Node';
                    const description = preview.short_description || preview.description || 'No description available';
                    const category = preview.category || 'General';
                    const popularity = preview.popularity || '⭐⭐';
                    const useCases = preview.use_cases || [];
                    const bestPractices = preview.best_practices || [];

                    return `
                        <div class="tooltip-header">
                            <span class="tooltip-icon">${icon}</span>
                            <div class="tooltip-title-section">
                                <h3 class="tooltip-title">${this.escapeHtml(displayName)}</h3>
                                <div class="tooltip-meta">
                                    <span class="tooltip-category">${category}</span>
                                    <span class="tooltip-popularity">${popularity}</span>
                                </div>
                            </div>
                            <button class="tooltip-close" title="Close (Esc)">✕</button>
                        </div>
                        
                        <div class="tooltip-body">
                            <p class="tooltip-description">${this.escapeHtml(description)}</p>
                            
                            ${useCases.length > 0 ? `
                                <div class="tooltip-section">
                                    <h4 class="tooltip-section-title">💡 Use Cases</h4>
                                    <ul class="tooltip-use-cases">
                                        ${useCases.slice(0, 3).map(uc => `<li>${this.escapeHtml(uc)}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                            
                            ${bestPractices.length > 0 ? `
                                <div class="tooltip-section">
                                    <h4 class="tooltip-section-title">⚡ Best Practices</h4>
                                    <ul class="tooltip-best-practices">
                                        ${bestPractices.slice(0, 2).map(bp => `<li>${this.escapeHtml(bp)}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>

                        <div class="tooltip-expanded-content">
                            ${preview.parameters?.length > 0 ? `
                                <div class="tooltip-section">
                                    <h4 class="tooltip-section-title">⚙️ Parameters</h4>
                                    <table class="tooltip-parameters">
                                        <thead><tr><th>Name</th><th>Type</th><th>Description</th></tr></thead>
                                        <tbody>
                                            ${preview.parameters.slice(0, 5).map(p => `
                                                <tr>
                                                    <td><code>${this.escapeHtml(p.name || '—')}</code></td>
                                                    <td>${this.escapeHtml(p.type || '—')}</td>
                                                    <td>${this.escapeHtml(p.description || '—')}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            ` : ''}
                            
                            ${preview.documentation_url ? `
                                <div class="tooltip-section">
                                    <h4 class="tooltip-section-title">📚 Documentation</h4>
                                    <a href="${preview.documentation_url}" target="_blank" style="color: #a78bfa;">View full documentation →</a>
                                </div>
                            ` : ''}
                        </div>

                        <div class="tooltip-actions">
                            <button class="tooltip-action-btn primary" data-action="expand">
                                ${this.isExpanded ? 'Show Less' : 'Show More'}
                            </button>
                            <button class="tooltip-action-btn" data-action="copy">
                                📋 Copy
                            </button>
                            <button class="tooltip-action-btn" data-action="help">
                                🤖 Ask AI
                            </button>
                        </div>

                        <div class="tooltip-expand-hint">Click to expand</div>
                        <div class="tooltip-keyboard-hint">
                            <span class="tooltip-key">Esc</span> close
                        </div>
                    `;

                default:
                    return '';
            }
        },

        /**
         * Bind mouse and touch events
         */
        bindEvents() {
            // Mouse move - throttled for performance
            document.addEventListener('mousemove', (e) => {
                if (!this.mouseMoveThrottle) {
                    this.mouseMoveThrottle = setTimeout(() => {
                        this.mouseMoveThrottle = null;
                        if (this.isVisible && this.config.followMouse) {
                            this.updatePosition(e.clientX, e.clientY);
                        }
                    }, 16); // ~60fps
                }
                this.currentPosition = { x: e.clientX, y: e.clientY };
            });

            // Click to expand
            this.element.addEventListener('click', (e) => {
                const action = e.target.closest('[data-action]')?.dataset.action;
                if (action === 'expand') {
                    this.toggleExpand();
                } else if (action === 'copy') {
                    this.copyNodeInfo();
                } else if (action === 'help') {
                    this.askAI();
                }
            });

            // Close button
            this.element.querySelector('.tooltip-close')?.addEventListener('click', () => {
                this.hide();
            });

            // Prevent tooltip from stealing focus
            this.element.addEventListener('mousedown', (e) => {
                e.preventDefault();
            });
        },

        /**
         * Bind keyboard events
         */
        bindKeyboard() {
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isVisible) {
                    this.hide();
                }
            });
        },

        /**
         * Show tooltip at position
         */
        show(nodeType, position, options = {}) {
            if (this.currentNodeType === nodeType && this.isVisible) {
                // Update position if changed significantly
                if (Math.abs(position.x - this.currentPosition.x) > 50 ||
                    Math.abs(position.y - this.currentPosition.y) > 50) {
                    this.updatePosition(position.x, position.y);
                }
                return;
            }

            this.currentNodeType = nodeType;
            this.hoverStartTime = Date.now();
            this.currentPosition = position;

            // Reset state
            this.isExpanded = false;

            // Show loading state
            this.element.innerHTML = this.getTemplate('loading');
            this.element.classList.add('visible');
            this.isVisible = true;

            // Update position
            this.updatePosition(position.x, position.y);

            // Fetch data with delay
            clearTimeout(this.fetchTimeout);
            this.fetchTimeout = setTimeout(async () => {
                try {
                    // Only fetch if still on same node
                    if (this.currentNodeType !== nodeType) return;

                    const info = await this.fetchNodeInfo(nodeType);

                    // Check again after fetch
                    if (this.currentNodeType !== nodeType) return;

                    this.displayContent(nodeType, info);
                } catch (error) {
                    if (this.currentNodeType === nodeType) {
                        this.element.innerHTML = this.getTemplate('error', { message: error.message });
                    }
                }
            }, this.config.delay);
        },

        /**
         * Update tooltip position
         */
        updatePosition(x, y) {
            const tooltipRect = this.element.getBoundingClientRect();
            
            // Calculate position
            let left = x + 20;
            let top = y + 20;

            // Adjust if off-screen
            if (left + this.element.offsetWidth > window.innerWidth - 20) {
                left = x - this.element.offsetWidth - 20;
            }
            if (top + this.element.offsetHeight > window.innerHeight - 20) {
                top = y - this.element.offsetHeight - 20;
            }

            // Keep within viewport
            left = Math.max(10, Math.min(left, window.innerWidth - this.element.offsetWidth - 10));
            top = Math.max(10, Math.min(top, window.innerHeight - this.element.offsetHeight - 10));

            this.element.style.left = left + 'px';
            this.element.style.top = top + 'px';
            this.currentPosition = { x, y };
        },

        /**
         * Display content in tooltip
         */
        displayContent(nodeType, info) {
            // Check if still relevant
            if (this.currentNodeType !== nodeType) return;

            this.element.innerHTML = this.getTemplate('content', info);
            this.updatePosition(this.currentPosition.x, this.currentPosition.y);
        },

        /**
         * Toggle expanded state
         */
        toggleExpand() {
            this.isExpanded = !this.isExpanded;
            this.element.classList.toggle('expanded', this.isExpanded);
            
            // Update button text
            const expandBtn = this.element.querySelector('[data-action="expand"]');
            if (expandBtn) {
                expandBtn.textContent = this.isExpanded ? 'Show Less' : 'Show More';
            }

            // Re-fetch full info if expanding
            if (this.isExpanded && this.currentNodeType) {
                this.fetchNodeInfo(this.currentNodeType, 'full').then(info => {
                    if (this.currentNodeType && this.isExpanded) {
                        this.element.innerHTML = this.getTemplate('content', info);
                    }
                });
            }
        },

        /**
         * Copy node info to clipboard
         */
        async copyNodeInfo() {
            if (!this.currentNodeType) return;

            try {
                const info = await this.fetchNodeInfo(this.currentNodeType);
                const preview = info.preview || {};
                const text = `${preview.display_name || preview.node_type}\n${preview.short_description || ''}\n\nType: ${preview.node_type}\nCategory: ${preview.category}`;
                
                await navigator.clipboard.writeText(text);
                
                // Show feedback
                const btn = this.element.querySelector('[data-action="copy"]');
                if (btn) {
                    const original = btn.textContent;
                    btn.textContent = '✓ Copied!';
                    setTimeout(() => btn.textContent = original, 2000);
                }
            } catch (error) {
                console.error('Failed to copy:', error);
            }
        },

        /**
         * Open AI chat for help with this node
         */
        askAI() {
            if (!this.currentNodeType) return;

            // Send message to open side panel with context
            window.postMessage({
                type: 'FLOWGENT_ASK_AI',
                nodeType: this.currentNodeType,
                context: {
                    action: 'help',
                    nodeType: this.currentNodeType
                }
            }, '*');

            this.hide();
        },

        /**
         * Hide tooltip
         */
        hide() {
            this.currentNodeType = null;
            this.isVisible = false;
            this.isExpanded = false;
            clearTimeout(this.fetchTimeout);
            
            this.element.classList.remove('visible', 'expanded');
            
            // Clean up highlights
            document.querySelectorAll('.flowgent-node-highlight').forEach(el => {
                el.classList.remove('flowgent-node-highlight');
            });
        },

        /**
         * Fetch node info from background script
         */
        fetchNodeInfo(nodeType, previewType = 'brief') {
            return new Promise((resolve, reject) => {
                const requestId = Math.random().toString(36).substring(7);

                const timeout = setTimeout(() => {
                    this.pendingRequests.delete(requestId);
                    reject(new Error('Timeout'));
                }, 10000);

                this.pendingRequests.set(requestId, { resolve, reject, timeout });

                window.postMessage({
                    type: 'FLOWGENT_FETCH_NODE_INFO',
                    nodeType,
                    requestId,
                    previewType
                }, '*');
            });
        },

        /**
         * Escape HTML to prevent XSS
         */
        escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };

    // Listen for messages from content script
    window.addEventListener('message', (event) => {
        if (event.source !== window) return;

        if (event.data.type === 'FLOWGENT_NODE_INFO_RESPONSE') {
            const { requestId, success, info, error } = event.data;

            const pending = Tooltip.pendingRequests.get(requestId);
            if (pending) {
                clearTimeout(pending.timeout);
                Tooltip.pendingRequests.delete(requestId);

                if (success) {
                    pending.resolve(info);
                } else {
                    pending.reject(new Error(error || 'Unknown error'));
                }
            }
        } else if (event.data.type === 'FLOWGENT_SHOW_TOOLTIP') {
            Tooltip.show(event.data.nodeType, event.data.position, event.data.options);
        } else if (event.data.type === 'FLOWGENT_HIDE_TOOLTIP') {
            Tooltip.hide();
        }
    });

    // Initialize on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => Tooltip.init());
    } else {
        Tooltip.init();
    }

    // Export for debugging
    window.FlowgentTooltip = Tooltip;

})();
