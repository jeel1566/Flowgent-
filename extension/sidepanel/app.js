/**
 * Main application logic for Flowgent side panel
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize all components
    Chat.init();
    Dashboard.init();
    Settings.init();

    // Tab switching
    setupTabs();

    // Check connection status on load
    checkConnectionStatus();
});

function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Update active states
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });
}

async function checkConnectionStatus() {
    const statusElement = document.getElementById('connectionStatus');

    try {
        const health = await api.checkHealth();

        if (health.status === 'healthy') {
            statusElement.className = 'connection-status connected';
            statusElement.querySelector('.status-text').textContent = 'Connected';

            // Show MCP status if available
            if (health.mcp_connected) {
                statusElement.title = 'Backend and n8n MCP connected';
            } else {
                statusElement.title = 'Backend connected, MCP disconnected';
            }
        } else {
            throw new Error('Unhealthy');
        }
    } catch (error) {
        statusElement.className = 'connection-status error';
        statusElement.querySelector('.status-text').textContent = 'Disconnected';
        statusElement.title = 'Cannot connect to backend';
    }
}

// Check connection every 30 seconds
setInterval(checkConnectionStatus, 30000);
