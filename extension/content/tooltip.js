/**
 * Tooltip functionality for Information Hand feature
 * This script runs as a content script with Chrome API access
 */

(function () {
  'use strict';

  let tooltip = null;
  let currentNodeType = null;
  let fetchTimeout = null;
  const BACKEND_URL = 'http://localhost:8000';

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
        `;
    document.body.appendChild(tooltip);

    return tooltip;
  }

  // Show tooltip with node information
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
        const info = await fetchNodeInfo(nodeType);
        if (currentNodeType === nodeType) {
          displayNodeInfo(info);
        }
      } catch (error) {
        if (currentNodeType === nodeType) {
          tooltipEl.innerHTML = `
                        <div style="color: #f87171;">
                            <strong>⚠️ Unable to load</strong>
                            <p style="margin: 5px 0 0; opacity: 0.7;">${error.message}</p>
                        </div>
                    `;
        }
      }
    }, 300);
  }

  // Hide tooltip
  function hideTooltip() {
    currentNodeType = null;
    clearTimeout(fetchTimeout);
    if (tooltip) {
      tooltip.style.display = 'none';
    }
  }

  // Fetch node info from backend directly
  async function fetchNodeInfo(nodeType) {
    const response = await fetch(`${BACKEND_URL}/api/node-info/${encodeURIComponent(nodeType)}`);
    if (!response.ok) {
      throw new Error('Backend not available');
    }
    return await response.json();
  }

  // Display node information in tooltip
  function displayNodeInfo(info) {
    if (!tooltip) return;

    const description = info.description || 'No description available';
    const displayName = info.display_name || info.node_type || 'Node';

    tooltip.innerHTML = `
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h3 style="margin: 0; font-size: 16px; color: #fff;">${displayName}</h3>
                    <span style="background: #8b5cf6; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">✨ Flowgent</span>
                </div>
                
                <p style="margin: 0; color: rgba(255,255,255,0.85); line-height: 1.5;">
                    ${description.substring(0, 200)}${description.length > 200 ? '...' : ''}
                </p>

                ${info.use_cases && info.use_cases.length > 0 ? `
                    <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <h4 style="margin: 0 0 8px; font-size: 12px; color: #8b5cf6;">💡 Use Cases</h4>
                        <ul style="margin: 0; padding-left: 16px; color: rgba(255,255,255,0.75); font-size: 13px;">
                            ${info.use_cases.slice(0, 2).map(uc => `<li>${uc}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                <div style="margin-top: 10px; font-size: 11px; color: rgba(255,255,255,0.4);">
                    Move mouse away to close
                </div>
            </div>
        `;

    // Adjust position if off-screen
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

  console.log('Flowgent: Tooltip script loaded');

})();
