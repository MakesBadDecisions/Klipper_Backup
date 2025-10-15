/**
 * API Client for Printer Buddy
 * 
 * Handles all communication with the Python backend API.
 */

class PrinterBuddyAPI {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.timeout = 5000;
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseUrl}/api${endpoint}`;
        
        const config = {
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            config.signal = controller.signal;
            
            const response = await fetch(url, config);
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }

    // System Status
    async getStatus() {
        return await this.makeRequest('/status');
    }

    // State Management
    async getState(key = null) {
        const params = key ? `?key=${encodeURIComponent(key)}` : '';
        return await this.makeRequest(`/state${params}`);
    }

    async setState(key, value) {
        return await this.makeRequest('/state', {
            method: 'POST',
            body: JSON.stringify({ key, value })
        });
    }

    // Modules
    async getModules() {
        return await this.makeRequest('/modules');
    }

    // Configuration
    async getConfig() {
        return await this.makeRequest('/config');
    }

    // Commands
    async executeCommand(command, params = {}) {
        return await this.makeRequest('/command', {
            method: 'POST',
            body: JSON.stringify({ command, params })
        });
    }

    // Emergency Stop
    async emergencyStop() {
        return await this.makeRequest('/emergency_stop', {
            method: 'POST'
        });
    }

    // Commissioning
    async getCommissioningTests() {
        return await this.makeRequest('/commissioning/tests');
    }

    async startCommissioningTest(testId) {
        const response = await this.makeRequest('/commissioning/start', {
            method: 'POST',
            body: JSON.stringify({ test_id: testId })
        });
        console.log('DEBUG: startCommissioningTest response:', response);
        return response;
    }

    async getCommissioningStatus(runId = null) {
        const url = runId ? `/commissioning/status?run_id=${runId}` : '/commissioning/status';
        return await this.makeRequest(url);
    }

    async respondToCommissioningPrompt(runId, response) {
        return await this.makeRequest('/commissioning/respond', {
            method: 'POST',
            body: JSON.stringify({ run_id: runId, response: response })
        });
    }

    async stopCommissioning() {
        return await this.makeRequest('/commissioning/stop', {
            method: 'POST'
        });
    }

    // Utility method for testing connectivity
    async ping() {
        try {
            await this.getStatus();
            return true;
        } catch (error) {
            return false;
        }
    }
}