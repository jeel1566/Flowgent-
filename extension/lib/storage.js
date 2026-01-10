/**
 * Chrome storage helpers for Flowgent extension
 */

const Storage = {
    /**
     * Get a value from storage
     */
    async get(key, defaultValue = null) {
        const result = await chrome.storage.local.get(key);
        return result[key] !== undefined ? result[key] : defaultValue;
    },

    /**
     * Set a value in storage
     */
    async set(key, value) {
        await chrome.storage.local.set({ [key]: value });
    },

    /**
     * Get multiple values
     */
    async getMultiple(keys) {
        return await chrome.storage.local.get(keys);
    },

    /**
     * Set multiple values
     */
    async setMultiple(items) {
        await chrome.storage.local.set(items);
    },

    /**
     * Remove a value
     */
    async remove(key) {
        await chrome.storage.local.remove(key);
    },

    /**
     * Clear all storage
     */
    async clear() {
        await chrome.storage.local.clear();
    },

    /**
     * Get backend URL
     */
    async getBackendUrl() {
        return await this.get('backendUrl', 'http://localhost:8000');
    },

    /**
     * Set backend URL
     */
    async setBackendUrl(url) {
        await this.set('backendUrl', url);
    },

    /**
     * Get node info cache
     */
    async getNodeCache(nodeType) {
        const cache = await this.get('nodeCache', {});
        return cache[nodeType] || null;
    },

    /**
     * Set node info in cache
     */
    async setNodeCache(nodeType, info) {
        const cache = await this.get('nodeCache', {});
        cache[nodeType] = {
            info,
            timestamp: Date.now()
        };
        await this.set('nodeCache', cache);
    },

    /**
     * Clear expired cache entries (older than 24 hours)
     */
    async clearExpiredCache() {
        const cache = await this.get('nodeCache', {});
        const now = Date.now();
        const DAY_MS = 24 * 60 * 60 * 1000;

        const cleaned = Object.entries(cache).reduce((acc, [key, value]) => {
            if (now - value.timestamp < DAY_MS) {
                acc[key] = value;
            }
            return acc;
        }, {});

        await this.set('nodeCache', cleaned);
    }
};
