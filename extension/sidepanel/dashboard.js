/**
 * Dashboard functionality for Flowgent
 */

const Dashboard = {
    workflows: [],
    executions: [],

    init() {
        // Load when dashboard tab is activated
        document.querySelector('[data-tab="dashboard"]').addEventListener('click', () => {
            this.loadWorkflows();
            this.loadExecutions();
        });
    },

    async loadWorkflows() {
        const container = document.getElementById('workflowsList');
        container.innerHTML = '<div class="loading">Loading workflows...</div>';

        try {
            const workflows = await api.getWorkflows();
            this.workflows = workflows;

            if (!workflows || workflows.length === 0) {
                container.innerHTML = `
          <div class="empty-state">
            <p>No workflows found.</p>
            <p class="hint">Create some workflows using the Chat tab, or configure your n8n credentials in Settings!</p>
          </div>
        `;
                return;
            }

            container.innerHTML = '';
            workflows.forEach(workflow => {
                const item = this.createWorkflowItem(workflow);
                container.appendChild(item);
            });
        } catch (error) {
            console.error('Failed to load workflows:', error);
            let errorMessage = error.message;
            
            // Provide helpful error messages
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage = 'Cannot connect to backend. Is it running?';
            } else if (error.message.includes('401') || error.message.includes('403')) {
                errorMessage = 'Authentication failed. Check your n8n credentials in Settings.';
            } else if (error.message.includes('500')) {
                errorMessage = 'Backend error. Check backend logs for details.';
            }
            
            container.innerHTML = `
                <div class="error">
                    <p><strong>⚠️ Failed to load workflows</strong></p>
                    <p>${errorMessage}</p>
                    <p class="hint">Check the Settings tab to configure your backend and n8n credentials.</p>
                </div>
            `;
        }
    },

    createWorkflowItem(workflow) {
        const item = document.createElement('div');
        item.className = 'workflow-item';

        const createdDate = workflow.created_at ? new Date(workflow.created_at).toLocaleDateString() : 'Unknown';

        item.innerHTML = `
      <div class="workflow-header">
        <div class="workflow-name">${workflow.name}</div>
        <div class="workflow-status ${workflow.active ? 'active' : 'inactive'}">
          ${workflow.active ? 'Active' : 'Inactive'}
        </div>
      </div>
      <div class="workflow-meta">
        <span>Created: ${createdDate}</span>
        <span>ID: ${workflow.id}</span>
      </div>
    `;

        item.addEventListener('click', () => this.showWorkflowDetails(workflow));

        return item;
    },

    async showWorkflowDetails(workflow) {
        try {
            const details = await api.getWorkflow(workflow.id);

            // Show workflow details modal or expand inline
            const messagesContainer = document.getElementById('messages');

            // Switch to chat tab to show details
            document.querySelector('[data-tab="chat"]').click();

            Chat.addMessage('assistant', `
**Workflow: ${details.name}**

**Status:** ${details.active ? '✅ Active' : '⏸️ Inactive'}
**Nodes:** ${details.nodes.length}
**Created:** ${details.created_at ? new Date(details.created_at).toLocaleDateString() : 'Unknown'}

Want to modify this workflow? Just ask me what changes you'd like to make!
      `);
        } catch (error) {
            console.error('Failed to load workflow details:', error);
        }
    },

    async loadExecutions() {
        const container = document.getElementById('executionsList');
        container.innerHTML = '<div class="loading">Loading executions...</div>';

        try {
            const executions = await api.getExecutions();
            this.executions = executions;

            if (!executions || executions.length === 0) {
                container.innerHTML = `
          <div class="empty-state">
            <p>No executions yet.</p>
            <p class="hint">Execute some workflows to see history here!</p>
          </div>
        `;
                return;
            }

            container.innerHTML = '';
            executions.slice(0, 10).forEach(execution => {
                const item = this.createExecutionItem(execution);
                container.appendChild(item);
            });
        } catch (error) {
            console.error('Failed to load executions:', error);
            let errorMessage = error.message;
            
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage = 'Cannot connect to backend. Is it running?';
            }
            
            container.innerHTML = `
                <div class="error">
                    <p><strong>⚠️ Failed to load executions</strong></p>
                    <p>${errorMessage}</p>
                </div>
            `;
        }
    },

    createExecutionItem(execution) {
        const item = document.createElement('div');
        item.className = 'execution-item';

        const startedDate = execution.startedAt ? new Date(execution.startedAt).toLocaleString() : 'Unknown';
        const status = execution.finished ? (execution.success ? '✅ Success' : '❌ Failed') : '⏳ Running';

        item.innerHTML = `
      <div class="workflow-header">
        <div class="workflow-name">${execution.workflowName || 'Workflow'}</div>
        <div class="workflow-status">${status}</div>
      </div>
      <div class="workflow-meta">
        <span>${startedDate}</span>
        <span>ID: ${execution.id}</span>
      </div>
    `;

        return item;
    }
};
