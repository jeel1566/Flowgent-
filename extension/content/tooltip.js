/**
 * Tooltip functionality for Information Hand feature
 * This script runs in the page context and communicates with content script
 */

(function () {
  'use strict';

  let tooltip = null;
  let currentNodeType = null;
  let fetchTimeout = null;
  const pendingRequests = new Map();
  const cache = {}; // Simple in-memory cache for fast repeat requests

  // Create tooltip element
  function createTooltip() {
    if (tooltip) return tooltip;

    tooltip = document.createElement('div');
    tooltip.className = 'flowgent-tooltip';
    tooltip.style.cssText = `
            display: none;
            position: fixed;
            z-index: 999999;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 16px;
            max-width: 350px;
            min-width: 280px;
            color: #fff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.4);
            backdrop-filter: blur(10px);
            pointer-events: none; /* Let clicks pass through */
        `;
    document.body.appendChild(tooltip);

    return tooltip;
  }

  // Show tooltip
  async function showTooltip(nodeType, position) {
    if (currentNodeType === nodeType && tooltip && tooltip.style.display === 'block') {
      return;
    }

    currentNodeType = nodeType;
    const tooltipEl = createTooltip();

    tooltipEl.style.left = (position.x + 15) + 'px';
    tooltipEl.style.top = (position.y + 15) + 'px';
    tooltipEl.style.display = 'block';
    tooltipEl.innerHTML = '<div style="color: #8b5cf6;">✨ Loading node info...</div>';

    clearTimeout(fetchTimeout);
    fetchTimeout = setTimeout(async () => {
      try {
        if (currentNodeType !== nodeType) return;

        const info = await fetchNodeInfo(nodeType);

        if (currentNodeType === nodeType) {
          displayNodeInfo(info);
        }
      } catch (error) {
        if (currentNodeType === nodeType) {
          tooltipEl.innerHTML = `
                        <div style="color: #f87171;">
                            <strong>⚠️ Unable to load</strong>
                            <p style="margin: 5px 0 0; opacity: 0.7; font-size: 12px;">${error.message}</p>
                        </div>
                    `;
        }
      }
    }, 100);
  }

  // Hide tooltip
  function hideTooltip() {
    currentNodeType = null;
    clearTimeout(fetchTimeout);
    if (tooltip) {
      tooltip.style.display = 'none';
    }
  }

  // Fetch node info via content script -> background
  function fetchNodeInfo(nodeType) {
    // Return cached result immediately if available
    if (cache[nodeType]) {
      return Promise.resolve(cache[nodeType]);
    }

    return new Promise((resolve, reject) => {
      const requestId = Math.random().toString(36).substring(7);

      // Set timeout
      const timeout = setTimeout(() => {
        pendingRequests.delete(requestId);
        reject(new Error('Timeout fetching node data (30s)'));
      }, 30000);

      pendingRequests.set(requestId, { resolve, reject, timeout });

      window.postMessage({
        type: 'FLOWGENT_FETCH_NODE_INFO',
        nodeType,
        requestId
      }, '*');
    });
  }

  // Display node information
  function displayNodeInfo(info) {
    if (!tooltip) return;

    const description = info.description || 'No description available';
    const displayName = info.name || info.display_name || info.node_type || 'Node';
    const howItWorks = info.howItWorks || '';
    const whatItDoes = info.whatItDoes || '';

    tooltip.innerHTML = `
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h3 style="margin: 0; font-size: 16px; color: #fff; font-weight: 600;">${displayName}</h3>
                    <span style="background: rgba(139, 92, 246, 0.2); color: #c4b5fd; padding: 2px 8px; border-radius: 12px; font-size: 11px; border: 1px solid rgba(139, 92, 246, 0.4);">✨ Flowgent</span>
                </div>
                
                <p style="margin: 0 0 12px; color: rgba(255,255,255,0.85); line-height: 1.5; font-size: 13px;">
                    ${description.substring(0, 150)}${description.length > 150 ? '...' : ''}
                </p>

                ${howItWorks ? `
                    <div style="margin-bottom: 10px;">
                        <h4 style="margin: 0 0 6px; font-size: 12px; color: #a78bfa; text-transform: uppercase; letter-spacing: 0.5px;">⚙️ How it works</h4>
                        <p style="margin: 0; color: rgba(255,255,255,0.75); font-size: 12px; line-height: 1.4;">
                            ${howItWorks.substring(0, 200)}${howItWorks.length > 200 ? '...' : ''}
                        </p>
                    </div>
                ` : ''}

                ${whatItDoes ? `
                    <div style="margin-bottom: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <h4 style="margin: 0 0 6px; font-size: 12px; color: #a78bfa; text-transform: uppercase; letter-spacing: 0.5px;">🎯 What it does</h4>
                        <p style="margin: 0; color: rgba(255,255,255,0.75); font-size: 12px; line-height: 1.4;">
                            ${whatItDoes.substring(0, 200)}${whatItDoes.length > 200 ? '...' : ''}
                        </p>
                    </div>
                ` : ''}

                <div style="margin-top: 10px; font-size: 10px; color: rgba(255,255,255,0.3); text-align: right;">
                    Flowgent AI • Move mouse to close
                </div>
            </div>
        `;

    adjustPosition();
  }

  function adjustPosition() {
    if (!tooltip) return;
    const rect = tooltip.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
      tooltip.style.left = (window.innerWidth - rect.width - 20) + 'px';
    }
    if (rect.bottom > window.innerHeight) {
      tooltip.style.top = (window.innerHeight - rect.height - 20) + 'px';
    }
  }

  // Listen for responses from content script
  window.addEventListener('message', (event) => {
    if (event.source !== window) return;

    if (event.data.type === 'FLOWGENT_NODE_INFO_RESPONSE') {
      const { requestId, success, info, error } = event.data;

      const pending = pendingRequests.get(requestId);
      if (pending) {
        clearTimeout(pending.timeout);
        pendingRequests.delete(requestId);

        if (success && info) {
          // Cache the response for future fast access
          cache[info.nodeType || info.name || 'unknown'] = info;
          pending.resolve(info);
        } else {
          const fallbackInfo = {
            display_name: currentNodeType,
            description: error || "Could not load info",
            howItWorks: "Configuration node for workflow automation",
            whatItDoes: "Performs automated tasks within workflows",
            use_cases: []
          };
          // Cache the fallback too to avoid repeated failures
          cache[currentNodeType] = fallbackInfo;
          pending.resolve(fallbackInfo);
        }
      }
    } else if (event.data.type === 'FLOWGENT_SHOW_TOOLTIP') {
      showTooltip(event.data.nodeType, event.data.position);
    } else if (event.data.type === 'FLOWGENT_HIDE_TOOLTIP') {
      hideTooltip();
    }
  });

  console.log('Flowgent: Tooltip script (v2) loaded');

})();
