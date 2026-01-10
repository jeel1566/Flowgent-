/**
 * Chat functionality for Flowgent
 */

const Chat = {
    messages: [],
    isTyping: false,

    init() {
        const input = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');

        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = input.scrollHeight + 'px';
        });

        // Send on Enter (Shift+Enter for new line)
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        sendButton.addEventListener('click', () => this.sendMessage());

        // Check for stored AI context
        this.checkForContext();
    },

    async checkForContext() {
        try {
            const { aiContext } = await chrome.storage.local.get('aiContext');
            if (aiContext && aiContext.nodeType) {
                // There's context from Information Hand
                const timeSince = Date.now() - (aiContext.timestamp || 0);
                
                // Only use context if less than 5 minutes old
                if (timeSince < 5 * 60 * 1000) {
                    const input = document.getElementById('chatInput');
                    const contextMessage = `Can you help me with the ${aiContext.nodeType} node? I want to understand how to use it.`;
                    input.value = contextMessage;
                    input.style.height = 'auto';
                    input.style.height = input.scrollHeight + 'px';
                    
                    // Clear the context
                    await chrome.storage.local.remove('aiContext');
                }
            }
        } catch (error) {
            console.error('Error checking context:', error);
        }
    },

    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message || this.isTyping) return;

        // Clear input
        input.value = '';
        input.style.height = 'auto';

        // Add user message
        this.addMessage('user', message);

        // Show typing indicator
        this.showTyping();

        try {
            // Send to backend
            const response = await api.chat(message);

            // Hide typing indicator
            this.hideTyping();

            // Add assistant response
            this.addMessage('assistant', response.response);

            // If workflow was created, show it
            if (response.workflow_data) {
                this.showWorkflowCreated(response.workflow_data);
            }
        } catch (error) {
            this.hideTyping();
            this.addMessage('assistant', `Sorry, I encountered an error: ${error.message}`);
        }
    },

    addMessage(role, content) {
        const messagesContainer = document.getElementById('messages');

        // Remove welcome message if it exists
        const welcome = messagesContainer.querySelector('.welcome-message');
        if (welcome) {
            welcome.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? 'U' : '✨';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Basic markdown support
        const formattedContent = this.formatMarkdown(content);
        contentDiv.innerHTML = formattedContent;

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);

        messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        this.messages.push({ role, content });
    },

    formatMarkdown(text) {
        // Basic markdown formatting
        let formatted = text
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');

        return formatted;
    },

    showTyping() {
        this.isTyping = true;
        const messagesContainer = document.getElementById('messages');

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant loading-message';
        typingDiv.id = 'typing-indicator';

        typingDiv.innerHTML = `
      <div class="message-avatar">✨</div>
      <div class="message-content">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    `;

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    },

    hideTyping() {
        this.isTyping = false;
        const typing = document.getElementById('typing-indicator');
        if (typing) {
            typing.remove();
        }
    },

    showWorkflowCreated(workflow) {
        const messagesContainer = document.getElementById('messages');

        const workflowDiv = document.createElement('div');
        workflowDiv.className = 'workflow-preview';
        workflowDiv.innerHTML = `
      <div class="workflow-created">
        <h4>✅ Workflow Created!</h4>
        <p><strong>${workflow.name || 'New Workflow'}</strong></p>
        <p>Nodes: ${workflow.nodes?.length || 0}</p>
        <button onclick="Dashboard.loadWorkflows()">View in Dashboard</button>
      </div>
    `;

        messagesContainer.appendChild(workflowDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
};
