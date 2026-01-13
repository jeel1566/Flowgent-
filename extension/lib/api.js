/**
 * API client for communicating with Flowgent backend
 */

class FlowgentAPI {
    constructor() {
        this.baseUrl = null;
        this.n8nInstanceUrl = null;
        this.n8nApiKey = null;
        this.initialized = false;
    }

    /**
     * Initialize the API client with backend URL and n8n config from storage
     */
    async init() {
        if (this.initialized) return;

        const { backendUrl, n8nInstanceUrl, n8nApiKey } = await chrome.storage.local.get([
            'backendUrl', 'n8nInstanceUrl', 'n8nApiKey'
        ]);

        this.baseUrl = backendUrl || 'http://localhost:8000';
        this.n8nInstanceUrl = n8nInstanceUrl || '';
        this.n8nApiKey = n8nApiKey || '';
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
     * Reload n8n config from storage
     */
    async reloadN8nConfig() {
        const { n8nInstanceUrl, n8nApiKey } = await chrome.storage.local.get(['n8nInstanceUrl', 'n8nApiKey']);
        this.n8nInstanceUrl = n8nInstanceUrl || '';
        this.n8nApiKey = n8nApiKey || '';
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
                'X-Extension-Version': chrome.runtime.getManifest().version,
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
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`API error: ${response.status} - ${errorData.detail || response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            
            // Handle specific error types
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                throw new Error('Network error: Cannot connect to backend. Check if the server is running.');
            } else if (error.message.includes('timeout')) {
                throw new Error('Request timeout: The server took too long to respond.');
            }
            
            throw error;
        }
    }

    /**
     * Send a chat message to the AI (includes n8n config)
     */
    async chat(message, context = null) {
        await this.reloadN8nConfig();

        return this.request('/api/chat', {
            method: 'POST',
            body: {
                message,
                context,
                // Include n8n config so backend can use it
                n8n_config: {
                    instance_url: this.n8nInstanceUrl,
                    api_key: this.n8nApiKey
                }
            }
        });
    }

    /**
     * Get all workflows
     */
    async getWorkflows() {
        await this.reloadN8nConfig();

        return this.request('/api/workflows', {
            method: 'GET',
            headers: {
                'X-N8N-Instance-URL': this.n8nInstanceUrl,
                'X-N8N-API-Key': this.n8nApiKey
            }
        });
    }

    /**
     * Get a specific workflow
     */
    async getWorkflow(workflowId) {
        await this.reloadN8nConfig();

        return this.request(`/api/workflows/${workflowId}`, {
            headers: {
                'X-N8N-Instance-URL': this.n8nInstanceUrl,
                'X-N8N-API-Key': this.n8nApiKey
            }
        });
    }

    /**
     * Execute a workflow
     */
    async executeWorkflow(workflowId, inputData = null) {
        await this.reloadN8nConfig();

        return this.request('/api/execute', {
            method: 'POST',
            body: {
                workflow_id: workflowId,
                input_data: inputData,
                n8n_config: {
                    instance_url: this.n8nInstanceUrl,
                    api_key: this.n8nApiKey
                }
            }
        });
    }

    /**
     * Create a workflow
     */
    async createWorkflow(name, nodes, connections) {
        await this.reloadN8nConfig();

        return this.request('/api/workflows', {
            method: 'POST',
            body: {
                name,
                nodes,
                connections,
                n8n_config: {
                    instance_url: this.n8nInstanceUrl,
                    api_key: this.n8nApiKey
                }
            }
        });
    }

    /**
     * Update an existing workflow
     */
    async updateWorkflow(workflowId, updates) {
        await this.reloadN8nConfig();

        return this.request(`/api/workflows/${workflowId}`, {
            method: 'PUT',
            body: {
                workflow_id: workflowId,
                ...updates,
                n8n_config: {
                    instance_url: this.n8nInstanceUrl,
                    api_key: this.n8nApiKey
                }
            }
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
        await this.reloadN8nConfig();

        const query = workflowId ? `?workflow_id=${workflowId}` : '';
        return this.request(`/api/executions${query}`, {
            headers: {
                'X-N8N-Instance-URL': this.n8nInstanceUrl,
                'X-N8N-API-Key': this.n8nApiKey
            }
        });
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
