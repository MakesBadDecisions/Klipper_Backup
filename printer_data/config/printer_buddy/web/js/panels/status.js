/**
 * Status Panel Manager
 * 
 * Handles the system status display panel.
 */

class StatusPanel {
    constructor(api, state) {
        this.api = api;
        this.state = state;
        this.elements = {};
    }

    async initialize() {
        console.log('Initializing Status Panel...');
        
        // Cache DOM elements
        this.elements = {
            printerStatus: document.getElementById('printerStatus'),
            safetyStatus: document.getElementById('safetyStatus'),
            // Simple status bar elements
            xPositionSimple: document.getElementById('xPositionSimple'),
            yPositionSimple: document.getElementById('yPositionSimple'), 
            zPositionSimple: document.getElementById('zPositionSimple'),
            bedTempSimple: document.getElementById('bedTempSimple'),
            extruderTempSimple: document.getElementById('extruderTempSimple'),
            // Legacy elements (if they exist)
            currentPosition: document.getElementById('currentPosition'),
            temperature: document.getElementById('temperature')
        };

        // Subscribe to state changes
        this.setupStateSubscriptions();
        
        // Initial update
        this.updateDisplay();
        
        console.log('Status Panel initialized');
    }

    setupStateSubscriptions() {
        // System status changes
        this.state.subscribe('system.status', (status) => {
            this.updatePrinterStatus(status);
        });

        this.state.subscribe('system.emergency_stop', (emergencyStop) => {
            this.updateSafetyStatus(emergencyStop);
        });

        // Printer position changes
        this.state.subscribe('printer.position', (position) => {
            this.updatePosition(position);
        });

        // Temperature changes
        this.state.subscribe('printer.temperatures', (temperatures) => {
            this.updateTemperatures(temperatures);
        });
    }

    updateDisplay() {
        // Update all display elements with current state
        const systemStatus = this.state.get('system.status') || 'unknown';
        const emergencyStop = this.state.get('system.emergency_stop') || false;
        const position = this.state.get('printer.position') || { x: 0, y: 0, z: 0 };
        const temperatures = this.state.get('printer.temperatures') || {};

        this.updatePrinterStatus(systemStatus);
        this.updateSafetyStatus(emergencyStop);
        this.updatePosition(position);
        this.updateTemperatures(temperatures);
    }

    updatePrinterStatus(status) {
        if (!this.elements.printerStatus) return;

        const statusText = this.formatStatus(status);
        this.elements.printerStatus.textContent = statusText;
        
        // Update status styling
        this.elements.printerStatus.className = `status-value status-${status}`;
        
        // Update parent status item styling
        const statusItem = this.elements.printerStatus.closest('.status-item');
        if (statusItem) {
            statusItem.className = 'status-item';
            
            if (status === 'emergency_stop' || status === 'error') {
                statusItem.classList.add('status-error');
            } else if (status === 'warning') {
                statusItem.classList.add('status-warning');
            } else if (status === 'ready' || status === 'active') {
                statusItem.classList.add('status-ok');
            }
        }
    }

    updateSafetyStatus(emergencyStop) {
        if (!this.elements.safetyStatus) return;

        const safetyEnabled = this.state.get('system.safety_enabled') !== false;
        
        let statusText, statusClass;
        
        if (emergencyStop) {
            statusText = 'EMERGENCY STOP';
            statusClass = 'status-error';
        } else if (safetyEnabled) {
            statusText = 'Active';
            statusClass = 'status-ok';
        } else {
            statusText = 'Disabled';
            statusClass = 'status-warning';
        }

        this.elements.safetyStatus.textContent = statusText;
        this.elements.safetyStatus.className = `status-value ${statusClass}`;
    }

    updatePosition(position) {
        console.log('StatusPanel.updatePosition called with:', position);
        
        // Update simple status bar elements
        if (this.elements.xPositionSimple) {
            const x = (position && position.x !== null && position.x !== undefined) ? position.x.toFixed(1) : '--';
            this.elements.xPositionSimple.textContent = x;
        }
        if (this.elements.yPositionSimple) {
            const y = (position && position.y !== null && position.y !== undefined) ? position.y.toFixed(1) : '--';
            this.elements.yPositionSimple.textContent = y;
        }
        if (this.elements.zPositionSimple) {
            const z = (position && position.z !== null && position.z !== undefined) ? position.z.toFixed(2) : '--';
            this.elements.zPositionSimple.textContent = z;
        }
        
        // Legacy element (if it exists)
        if (this.elements.currentPosition) {
            if (position && position.x !== null && position.y !== null && position.z !== null) {
                const x = (position.x || 0).toFixed(1);
                const y = (position.y || 0).toFixed(1);
                const z = (position.z || 0).toFixed(2);
                this.elements.currentPosition.textContent = `X:${x} Y:${y} Z:${z}`;
            } else {
                this.elements.currentPosition.textContent = 'X:-- Y:-- Z:--';
            }
            
            // Update homing status if available
            const homed = this.state.get('printer.homed') || {};
            const homedStatus = Object.entries(homed)
                .map(([axis, isHomed]) => `${axis.toUpperCase()}:${isHomed ? '✓' : '✗'}`)
                .join(' ');
                
            if (homedStatus) {
                this.elements.currentPosition.title = `Homed status: ${homedStatus}`;
            }
        }
    }

    updateTemperatures(temperatures) {
        console.log('StatusPanel.updateTemperatures called with:', temperatures);
        
        // Update simple status bar elements
        if (this.elements.bedTempSimple) {
            if (temperatures && temperatures.bed !== undefined && temperatures.bed !== null) {
                const bedTemp = Math.round(temperatures.bed);
                const bedTarget = temperatures.bed_target ? Math.round(temperatures.bed_target) : null;
                this.elements.bedTempSimple.textContent = bedTarget ? `${bedTemp}/${bedTarget}°C` : `${bedTemp}°C`;
            } else {
                this.elements.bedTempSimple.textContent = '--';
            }
        }
        
        if (this.elements.extruderTempSimple) {
            if (temperatures && temperatures.extruder !== undefined && temperatures.extruder !== null) {
                const extruderTemp = Math.round(temperatures.extruder);
                const extruderTarget = temperatures.extruder_target ? Math.round(temperatures.extruder_target) : null;
                this.elements.extruderTempSimple.textContent = extruderTarget ? `${extruderTemp}/${extruderTarget}°C` : `${extruderTemp}°C`;
            } else {
                this.elements.extruderTempSimple.textContent = '--';
            }
        }
        
        // Legacy element (if it exists)
        if (!this.elements.temperature) return;

        const tempStrings = [];
        
        // Format different temperature sensors
        if (temperatures.bed !== undefined) {
            const bedTemp = Math.round(temperatures.bed);
            const bedTarget = temperatures.bed_target ? Math.round(temperatures.bed_target) : null;
            tempStrings.push(`Bed:${bedTemp}°C${bedTarget ? `/${bedTarget}°C` : ''}`);
        }
        
        if (temperatures.extruder !== undefined) {
            const extruderTemp = Math.round(temperatures.extruder);
            const extruderTarget = temperatures.extruder_target ? Math.round(temperatures.extruder_target) : null;
            tempStrings.push(`E:${extruderTemp}°C${extruderTarget ? `/${extruderTarget}°C` : ''}`);
        }
        
        // Handle multiple extruders
        for (let i = 0; i < 10; i++) {
            const extruderKey = `extruder${i}`;
            const targetKey = `extruder${i}_target`;
            
            if (temperatures[extruderKey] !== undefined) {
                const temp = Math.round(temperatures[extruderKey]);
                const target = temperatures[targetKey] ? Math.round(temperatures[targetKey]) : null;
                tempStrings.push(`E${i}:${temp}°C${target ? `/${target}°C` : ''}`);
            }
        }
        
        const displayText = tempStrings.length > 0 ? tempStrings.join(' ') : 'No sensors';
        this.elements.temperature.textContent = displayText;
        
        // Add temperature warning styling
        const hasHighTemp = Object.values(temperatures).some(temp => 
            typeof temp === 'number' && temp > 200
        );
        
        if (hasHighTemp) {
            this.elements.temperature.classList.add('temperature-warning');
        } else {
            this.elements.temperature.classList.remove('temperature-warning');
        }
    }

    formatStatus(status) {
        const statusMap = {
            'initializing': 'Initializing...',
            'ready': 'Ready',
            'active': 'Active',
            'busy': 'Busy',
            'printing': 'Printing',
            'paused': 'Paused',
            'error': 'Error',
            'emergency_stop': 'EMERGENCY STOP',
            'offline': 'Offline',
            'unknown': 'Unknown'
        };
        
        return statusMap[status] || status;
    }

    // Manual refresh method
    async refresh() {
        try {
            const status = await this.api.getStatus();
            if (status) {
                this.state.updateSystemStatus(status);
            }
        } catch (error) {
            console.error('Failed to refresh status:', error);
        }
    }

    // Get current status summary
    getStatusSummary() {
        return {
            printer_status: this.state.get('system.status'),
            emergency_stop: this.state.get('system.emergency_stop'),
            position: this.state.get('printer.position'),
            temperatures: this.state.get('printer.temperatures'),
            safety_enabled: this.state.get('system.safety_enabled')
        };
    }
}