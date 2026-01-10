/**
 * API client for communicating with Flowgent backend
 */

class FlowgentAPI {
    constructor() {
        this.baseUrl = null;
        this.initialized = false;
    }

    /**
     * Initialize the API client with backend URL from storage
     */
    async init() {
        if (this.initialized) return;

        const { backendUrl } = await chrome.storage.local.get('backendUrl');
        this.baseUrl = backendUrl || 'http://localhost:8000';
        this.initialized = true;
    }

    /**
     * Set new backend URL
     */
    async setBackendUrl(url) {
        this.baseUrl = url;
        await chrome.storage.local.set({ backendUrl: url });
    }

    /**
     * Make an API request
     */
    async request(endpoint, options = {}) {
        await this.init();

        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (options.body) {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * Send a chat message to the AI
     */
    async chat(message, context = null) {
        return this.request('/api/chat', {
            method: 'POST',
            body: { message, context }
        });
    }

    /**
     * Get all workflows
     */
    async getWorkflows() {
        return this.request('/api/workflows');
    }

    /**
     * Get a specific workflow
     */
    async getWorkflow(workflowId) {
        return this.request(`/api/workflows/${workflowId}`);
    }

    /**
     * Execute a workflow
     */
    async executeWorkflow(workflowId, inputData = null) {
        return this.request('/api/execute', {
            method: 'POST',
            body: { workflow_id: workflowId, input_data: inputData }
        });
    }

    /**
     * Get node information
     */
    async getNodeInfo(nodeType) {
        return this.request(`/api/node-info/${encodeURIComponent(nodeType)}`);
    }

    /**
     * Get execution history
     */
    async getExecutions(workflowId = null) {
        const query = workflowId ? `?workflow_id=${workflowId}` : '';
        return this.request(`/api/executions${query}`);
    }

    /**
     * Check backend connection
     */
    async checkHealth() {
        try {
            return await this.request('/health');
        } catch (error) {
            return { status: 'unhealthy', error: error.message };
        }
    }
}

// Export singleton instance
const api = new FlowgentAPI();
