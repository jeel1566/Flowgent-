/**
 * Tooltip functionality for Information Hand feature
 * This script runs in the page context
 */

(function () {
    'use strict';

    let tooltip = null;
    let currentNodeType = null;
    let fetchTimeout = null;

    // Create tooltip element
    function createTooltip() {
        if (tooltip) return tooltip;

        tooltip = document.createElement('div');
        tooltip.className = 'flowgent-tooltip';
        tooltip.style.display = 'none';
        document.body.appendChild(tooltip);

        return tooltip;
    }

    // Show tooltip with node information
    async function showTooltip(nodeType, position) {
        if (currentNodeType === nodeType && tooltip && tooltip.style.display === 'block') {
            return; // Already showing for this node
        }

        currentNodeType = nodeType;
        const tooltipEl = createTooltip();

        // Position tooltip
        tooltipEl.style.left = (position.x + 15) + 'px';
        tooltipEl.style.top = (position.y + 15) + 'px';
        tooltipEl.style.display = 'block';
        tooltipEl.innerHTML = '<div class="flowgent-tooltip-loading">Loading...</div>';

        // Fetch node info with delay
        clearTimeout(fetchTimeout);
        fetchTimeout = setTimeout(async () => {
            try {
                const info = await getNodeInfo(nodeType);
                if (currentNodeType === nodeType) { // Still hovering
                    displayNodeInfo(info);
                }
            } catch (error) {
                if (currentNodeType === nodeType) {
                    tooltipEl.innerHTML = `
            <div class="flowgent-tooltip-error">
              <strong>Unable to load node information</strong>
              <p>${error.message}</p>
            </div>
          `;
                }
            }
        }, 300); // Small delay before fetching
    }

    // Hide tooltip
    function hideTooltip() {
        currentNodeType = null;
        clearTimeout(fetchTimeout);

        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }

    // Get node information from backend
    async function getNodeInfo(nodeType) {
        // Check cache first
        const response = await chrome.runtime.sendMessage({
            action: 'getNodeInfo',
            data: { nodeType }
        });

        if (response.cached) {
            return response.info;
        }

        // Fetch from backend
        const backendResponse = await chrome.runtime.sendMessage({
            action: 'fetchNodeInfo',
            data: { nodeType }
        });

        return backendResponse.info;
    }

    // Display node information in tooltip
    function displayNodeInfo(info) {
        if (!tooltip) return;

        const html = `
      <div class="flowgent-tooltip-content">
        <div class="tooltip-header">
          <h3>${info.display_name || info.node_type}</h3>
          <span class="tooltip-tag">✨ Flowgent</span>
        </div>
        
        <div class="tooltip-description">
          <p>${info.description || 'No description available'}</p>
        </div>

        ${info.use_cases && info.use_cases.length > 0 ? `
          <div class="tooltip-section">
            <h4>💡 Use Cases</h4>
            <ul>
              ${info.use_cases.slice(0, 3).map(useCase => `<li>${useCase}</li>`).join('')}
            </ul>
          </div>
        ` : ''}

        ${info.best_practices && info.best_practices.length > 0 ? `
          <div class="tooltip-section">
            <h4>⭐ Best Practices</h4>
            <ul>
              ${info.best_practices.slice(0, 2).map(practice => `<li>${practice}</li>`).join('')}
            </ul>
          </div>
        ` : ''}

        <div class="tooltip-footer">
          <small>Hover to keep open • Move away to close</small>
        </div>
      </div>
    `;

        tooltip.innerHTML = html;

        // Adjust position if tooltip goes off screen
        const rect = tooltip.getBoundingClientRect();
        if (rect.right > window.innerWidth) {
            tooltip.style.left = (window.innerWidth - rect.width - 10) + 'px';
        }
        if (rect.bottom > window.innerHeight) {
            tooltip.style.top = (window.innerHeight - rect.height - 10) + 'px';
        }
    }

    // Listen for messages from content script
    window.addEventListener('message', (event) => {
        if (event.source !== window) return;

        if (event.data.type === 'FLOWGENT_SHOW_TOOLTIP') {
            showTooltip(event.data.nodeType, event.data.position);
        } else if (event.data.type === 'FLOWGENT_HIDE_TOOLTIP') {
            hideTooltip();
        }
    });

    console.log('Flowgent tooltip script loaded');

})();
