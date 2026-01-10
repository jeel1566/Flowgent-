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

        case 'openSidePanelWithContext':
            // Open side panel with context for AI help
            if (sender.tab) {
                await chrome.sidePanel.open({ windowId: sender.tab.windowId });
                
                // Store context for the side panel
                if (data.context) {
                    await chrome.storage.local.set({ 
                        aiContext: {
                            ...data.context,
                            timestamp: Date.now()
                        }
                    });
                }
            }
            return { success: true };

        case 'fetchNodeInfo':
            // Proxy request to backend (original endpoint)
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

        case 'fetchNodePreview':
            // Proxy request to new preview endpoint (optimized for Information Hand)
            const previewSettings = await chrome.storage.local.get('backendUrl');
            const previewBaseUrl = previewSettings.backendUrl || 'http://localhost:8000';
            const previewTypeValue = data.previewType || 'brief';

            try {
                const response = await fetch(
                    `${previewBaseUrl}/api/node-preview/${encodeURIComponent(data.nodeType)}?preview_type=${previewTypeValue}`
                );
                if (!response.ok) {
                    throw new Error(`Backend error: ${response.status}`);
                }
                const previewData = await response.json();

                // Cache with preview type
                const previewCacheKey = `preview_${previewTypeValue}_${data.nodeType}`;
                const currentPreviewCache = await chrome.storage.local.get(previewCacheKey);
                const updatedPreviewCache = currentPreviewCache[previewCacheKey] || {};
                updatedPreviewCache[data.nodeType] = {
                    info: previewData,
                    previewType: previewTypeValue,
                    timestamp: Date.now()
                };
                await chrome.storage.local.set({ [previewCacheKey]: updatedPreviewCache });

                return { success: true, info: previewData };
            } catch (error) {
                console.error('Preview fetch error:', error);
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

        case 'getNodePreview':
            // Get cached preview data
            const getPreviewType = data.previewType || 'brief';
            const getPreviewCacheKey = `preview_${getPreviewType}_${data.nodeType}`;
            const getPreviewCache = await chrome.storage.local.get(getPreviewCacheKey);
            const getPreviewDataCache = getPreviewCache[getPreviewCacheKey] || {};

            if (getPreviewDataCache[data.nodeType]) {
                const cached = getPreviewDataCache[data.nodeType];
                const age = Date.now() - cached.timestamp;

                // Cache valid for 1 hour for brief, 24 hours for full
                const maxAge = getPreviewType === 'full' ? 24 * 60 * 60 * 1000 : 60 * 60 * 1000;
                if (age < maxAge) {
                    return { success: true, info: cached.info, cached: true, age };
                }
            }

            return { success: false };

        case 'cacheNodePreview':
            // Cache preview data with preview type
            const cachePreviewType = data.previewType || 'brief';
            const cachePreviewKey = `preview_${cachePreviewType}_${data.nodeType}`;
            const currentPreviewCache = await chrome.storage.local.get(cachePreviewKey);
            const updatedPreviewCache = currentPreviewCache[cachePreviewKey] || {};

            updatedPreviewCache[data.nodeType] = {
                info: data.info,
                cachedPreviewType: cachePreviewType,
                timestamp: Date.now()
            };

            await chrome.storage.local.set({ [cachePreviewKey]: updatedPreviewCache });
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
