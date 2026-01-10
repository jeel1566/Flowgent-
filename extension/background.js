/**
 * Background service worker for Flowgent extension
 */

// Initialize extension on install
chrome.runtime.onInstalled.addListener(async (details) => {
    console.log('Flowgent installed:', details);

    // Set default backend URL
    const { backendUrl } = await chrome.storage.local.get('backendUrl');
    if (!backendUrl) {
        await chrome.storage.local.set({ backendUrl: 'http://localhost:8000' });
    }
});

// Handle extension icon click - open side panel
chrome.action.onClicked.addListener(async (tab) => {
    await chrome.sidePanel.open({ windowId: tab.windowId });
});

// Listen for messages from content scripts and side panel
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    handleMessage(request, sender).then(sendResponse);
    return true; // Keep message channel open for async response
});

async function handleMessage(request, sender) {
    const { action, data } = request;

    switch (action) {
        case 'getBackendUrl':
            const { backendUrl } = await chrome.storage.local.get('backendUrl');
            return { backendUrl: backendUrl || 'http://localhost:8000' };

        case 'setBackendUrl':
            await chrome.storage.local.set({ backendUrl: data.url });
            return { success: true };

        case 'openSidePanel':
            if (sender.tab) {
                await chrome.sidePanel.open({ windowId: sender.tab.windowId });
            }
            return { success: true };

        case 'fetchNodeInfo':
            // Proxy request to backend
            const settings = await chrome.storage.local.get('backendUrl');
            const baseUrl = settings.backendUrl || 'http://localhost:8000';

            try {
                const response = await fetch(`${baseUrl}/api/node-info/${encodeURIComponent(data.nodeType)}`);
                if (!response.ok) {
                    throw new Error(`Backend error: ${response.status}`);
                }
                const info = await response.json();

                // Cache it
                const currentCache = await chrome.storage.local.get('nodeCache');
                const updatedCache = currentCache.nodeCache || {};
                updatedCache[data.nodeType] = {
                    info: info,
                    timestamp: Date.now()
                };
                await chrome.storage.local.set({ nodeCache: updatedCache });

                return { success: true, info };
            } catch (error) {
                console.error('Fetch error:', error);
                return { error: error.message };
            }

        case 'getNodeInfo':
            // Check cache first
            const cache = await chrome.storage.local.get('nodeCache');
            const nodeCache = cache.nodeCache || {};

            if (nodeCache[data.nodeType]) {
                const cached = nodeCache[data.nodeType];
                const age = Date.now() - cached.timestamp;

                // Cache valid for 24 hours
                if (age < 24 * 60 * 60 * 1000) {
                    return { success: true, info: cached.info, cached: true };
                }
            }

            return { success: false };

        case 'cacheNodeInfo':
            const currentCache = await chrome.storage.local.get('nodeCache');
            const updatedCache = currentCache.nodeCache || {};

            updatedCache[data.nodeType] = {
                info: data.info,
                timestamp: Date.now()
            };

            await chrome.storage.local.set({ nodeCache: updatedCache });
            return { success: true };

        case 'getCurrentTab':
            if (sender.tab) {
                return {
                    id: sender.tab.id,
                    url: sender.tab.url,
                    title: sender.tab.title
                };
            }
            return null;

        default:
            console.warn('Unknown action:', action);
            return { error: 'Unknown action' };
    }
}

// Clean up expired cache periodically (every 6 hours)
setInterval(async () => {
    const cache = await chrome.storage.local.get('nodeCache');
    const nodeCache = cache.nodeCache || {};
    const now = Date.now();
    const DAY_MS = 24 * 60 * 60 * 1000;

    const cleaned = Object.entries(nodeCache).reduce((acc, [key, value]) => {
        if (now - value.timestamp < DAY_MS) {
            acc[key] = value;
        }
        return acc;
    }, {});

    await chrome.storage.local.set({ nodeCache: cleaned });
    console.log('Cache cleaned');
}, 6 * 60 * 60 * 1000);

console.log('Flowgent background service worker initialized');
