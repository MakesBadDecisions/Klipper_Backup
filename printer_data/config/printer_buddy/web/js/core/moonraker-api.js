/**
 * Moonraker API Client
 * 
 * Direct communication with Moonraker API (port 7125).
 * Replaces the Printer Buddy API proxy.
 */

class MoonrakerAPI {
    constructor(baseUrl = null) {
        // Auto-detect Moonraker URL based on current page location
        if (!baseUrl) {
            const currentHost = window.location.hostname;
            const currentPort = window.location.port;
            
            // If we're being served from the Pi (like :8080), use same host for Moonraker
            if (currentHost !== 'localhost' && currentHost !== '' && currentHost !== '127.0.0.1') {
                this.baseUrl = `http://${currentHost}:7125`;
            } else {
                // Fallback to localhost for local development
                this.baseUrl = 'http://localhost:7125';
            }
        } else {
            this.baseUrl = baseUrl;
        }
        
        this.timeout = 5000;
        console.log(`Moonraker API initialized with base URL: ${this.baseUrl}`);
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
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

    // Printer Status and Info
    async getPrinterInfo() {
        return await this.makeRequest('/printer/info');
    }

    async getPrinterObjects(objects = null) {
        const url = objects ? 
            `/printer/objects/query?${objects.map(o => `${o}`).join('&')}` :
            '/printer/objects/list';
        return await this.makeRequest(url);
    }

    async getPrinterStatus() {
        // Get essential printer status objects using correct Moonraker format
        const objects = [
            'toolhead',
            'extruder', 
            'heater_bed',
            'fan',
            'print_stats',
            'display_status',
            'virtual_sdcard'
        ];
        const query = objects.join('&');
        console.log(`Requesting printer status: /printer/objects/query?${query}`);
        return await this.makeRequest(`/printer/objects/query?${query}`);
    }

    // G-code Commands
    async executeGcode(script) {
        return await this.makeRequest('/printer/gcode/script', {
            method: 'POST',
            body: JSON.stringify({ script })
        });
    }

    // Temperature Control
    async setExtruderTemp(temp, extruder = 'extruder') {
        return await this.executeGcode(`SET_HEATER_TEMPERATURE HEATER=${extruder} TARGET=${temp}`);
    }

    async setBedTemp(temp) {
        return await this.executeGcode(`SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET=${temp}`);
    }

    // Fan Control
    async setFanSpeed(speed, fan = 'fan') {
        const value = Math.max(0, Math.min(1, speed)); // Clamp 0-1
        return await this.executeGcode(`SET_FAN_SPEED FAN=${fan} SPEED=${value}`);
    }

    // Movement
    async homeAll() {
        return await this.executeGcode('G28');
    }

    async homeAxis(axis) {
        return await this.executeGcode(`G28 ${axis.toUpperCase()}`);
    }

    async moveAxis(axis, position, feedrate = null) {
        const f = feedrate ? ` F${feedrate}` : '';
        return await this.executeGcode(`G1 ${axis.toUpperCase()}${position}${f}`);
    }

    // Emergency Stop
    async emergencyStop() {
        return await this.executeGcode('M112');
    }

    // Utility method for testing connectivity
    async ping() {
        try {
            console.log(`Testing connection to ${this.baseUrl}/printer/info`);
            const result = await this.getPrinterInfo();
            console.log('Moonraker connection successful:', result);
            return true;
        } catch (error) {
            console.error('Moonraker ping failed:', error.message);
            console.error('Full error:', error);
            return false;
        }
    }

    // Connection status helper
    async getConnectionStatus() {
        try {
            console.log(`Checking connection status with ${this.baseUrl}`);
            const info = await this.getPrinterInfo();
            const status = await this.getPrinterStatus();
            
            const connectionStatus = {
                connected: true,
                klippy_connected: info.result?.klippy_connected || false,
                klippy_state: info.result?.klippy_state || 'unknown',
                printer_state: status.result?.print_stats?.state || 'unknown'
            };
            
            console.log('Connection status:', connectionStatus);
            return connectionStatus;
        } catch (error) {
            console.error('Connection status check failed:', error);
            return {
                connected: false,
                error: error.message,
                klippy_connected: false,
                klippy_state: 'error',
                printer_state: 'error'
            };
        }
    }
}

// Create global instance
window.moonrakerAPI = new MoonrakerAPI();