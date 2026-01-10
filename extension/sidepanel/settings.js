/**
 * Settings functionality for Flowgent
 */

const Settings = {
    init() {
        this.loadSettings();

        document.getElementById('saveSettings').addEventListener('click', () => this.saveSettings());
        document.getElementById('testConnection').addEventListener('click', () => this.testConnection());
    },

    async loadSettings() {
        const backendUrl = await Storage.getBackendUrl();
        document.getElementById('backendUrl').value = backendUrl;
    },

    async saveSettings() {
        const backendUrl = document.getElementById('backendUrl').value.trim();

        if (!backendUrl) {
            alert('Please enter a backend URL');
            return;
        }

        try {
            await Storage.setBackendUrl(backendUrl);
            await api.setBackendUrl(backendUrl);

            // Show success
            const button = document.getElementById('saveSettings');
            const originalText = button.textContent;
            button.textContent = '✓ Saved!';
            button.style.background = 'var(--success)';

            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = '';
            }, 2000);

            // Test connection after saving
            this.testConnection();
        } catch (error) {
            alert('Failed to save settings: ' + error.message);
        }
    },

    async testConnection() {
        const indicator = document.querySelector('.status-indicator');
        const infoText = document.getElementById('connectionInfo');
        const button = document.getElementById('testConnection');

        // Reset
        indicator.className = 'status-indicator';
        infoText.textContent = 'Testing...';
        button.disabled = true;

        try {
            const health = await api.checkHealth();

            if (health.status === 'healthy') {
                indicator.classList.add('connected');
                infoText.textContent = `Connected (v${health.version})`;

                // Update header status
                const headerStatus = document.getElementById('connectionStatus');
                headerStatus.className = 'connection-status connected';
                headerStatus.querySelector('.status-text').textContent = 'Connected';
            } else {
                throw new Error('Backend unhealthy');
            }
        } catch (error) {
            indicator.classList.add('error');
            infoText.textContent = `Connection failed: ${error.message}`;

            // Update header status
            const headerStatus = document.getElementById('connectionStatus');
            headerStatus.className = 'connection-status error';
            headerStatus.querySelector('.status-text').textContent = 'Disconnected';
        } finally {
            button.disabled = false;
        }
    }
};
