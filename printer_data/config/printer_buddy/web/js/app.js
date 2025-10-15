/**
 * Main Application Entry Point
 * 
 * Initializes the Printer Buddy web interface and coordinates all modules.
 */

class PrinterBuddyApp {
    constructor() {
        this.api = new PrinterBuddyAPI();
        this.state = new StateManager();
        this.ui = new UIManager();
        
        // Panel managers
        this.statusPanel = new StatusPanel(this.api, this.state);
        this.commissioningPanel = new CommissioningPanel(this.api, this.state);
        this.controlsPanel = new ControlsPanel(this.api, this.state);
        this.temperaturePanel = new TemperaturePanel(this.api, this.state);
        
        this.updateInterval = null;
        this.isConnected = false;
    }

    async initialize() {
        console.log('Initializing Printer Buddy App...');
        
        try {
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize UI components
            this.ui.initialize();
            
            // Initialize panels
            await this.statusPanel.initialize();
            await this.commissioningPanel.initialize();
            await this.controlsPanel.initialize();
            await this.temperaturePanel.initialize();
            
            // Start periodic updates
            this.startPeriodicUpdates();
            
            // Initial data load
            await this.loadInitialData();
            
            this.log('info', 'Printer Buddy App initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.log('error', `Initialization failed: ${error.message}`);
        }
    }

    setupEventListeners() {
        // Emergency stop button
        const emergencyStopBtn = document.getElementById('emergencyStop');
        if (emergencyStopBtn) {
            emergencyStopBtn.addEventListener('click', () => this.handleEmergencyStop());
        }

        // Panel toggles
        document.querySelectorAll('.panel-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const panelId = e.target.dataset.panel;
                this.ui.togglePanel(panelId);
            });
        });

        // Window events
        window.addEventListener('beforeunload', () => this.cleanup());
        window.addEventListener('online', () => this.handleConnectionChange(true));
        window.addEventListener('offline', () => this.handleConnectionChange(false));
    }

    async loadInitialData() {
        try {
            // Load printer status from Moonraker
            const connectionStatus = await window.moonrakerAPI.getConnectionStatus();
            
            if (connectionStatus.connected) {
                const printerStatus = await window.moonrakerAPI.getPrinterStatus();
                console.log('Raw printer status response:', printerStatus);
                
                if (printerStatus.result) {
                    const result = printerStatus.result.status;
                    console.log('Parsed printer status result:', result);
                    
                    // Update temperatures
                    const temperatures = {};
                    if (result.extruder) {
                        temperatures.extruder = result.extruder.temperature;
                        temperatures.extruder_target = result.extruder.target;
                    }
                    if (result.heater_bed) {
                        temperatures.bed = result.heater_bed.temperature;
                        temperatures.bed_target = result.heater_bed.target;
                    }
                    console.log('Initial load - Updating temperatures:', temperatures);
                    this.state.updateTemperatures(temperatures);
                    
                    // Update position
                    if (result.toolhead) {
                        const position = {
                            x: result.toolhead.position[0],
                            y: result.toolhead.position[1],
                            z: result.toolhead.position[2],
                            e: result.toolhead.position[3]
                        };
                        console.log('Initial load - Updating position:', position);
                        this.state.updatePosition(position);
                        
                        // Update homing status
                        const homed = {
                            x: result.toolhead.homed_axes.includes('x'),
                            y: result.toolhead.homed_axes.includes('y'),
                            z: result.toolhead.homed_axes.includes('z')
                        };
                        console.log('Initial load - Updating homed status:', homed, 'from homed_axes:', result.toolhead.homed_axes);
                        this.state.updateHomedStatus(homed);
                    }
                    
                    // Update printer state
                    if (result.print_stats) {
                        this.state.set('system.status', result.print_stats.state);
                    }
                }
                
                this.updateConnectionStatus(true);
            } else {
                this.updateConnectionStatus(false);
                this.log('warning', 'Moonraker not connected');
            }

            // Load configuration
            const config = await this.api.getConfig();
            if (config) {
                this.state.updateConfig(config);
            }

        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.updateConnectionStatus(false);
            this.log('error', `Failed to load initial data: ${error.message}`);
        }
    }

    startPeriodicUpdates() {
        // Update every 2 seconds
        this.updateInterval = setInterval(async () => {
            await this.updateData();
        }, 2000);
    }

    async updateData() {
        try {
            // Get current status from Moonraker
            const connectionStatus = await window.moonrakerAPI.getConnectionStatus();
            
            if (connectionStatus.connected) {
                const printerStatus = await window.moonrakerAPI.getPrinterStatus();
                console.log('Periodic update - Raw printer status response:', printerStatus);
                
                if (printerStatus.result) {
                    const result = printerStatus.result.status;
                    console.log('Periodic update - Parsed printer status result:', result);
                    
                    // Update temperatures
                    const temperatures = {};
                    if (result.extruder) {
                        temperatures.extruder = result.extruder.temperature;
                        temperatures.extruder_target = result.extruder.target;
                    }
                    if (result.heater_bed) {
                        temperatures.bed = result.heater_bed.temperature;
                        temperatures.bed_target = result.heater_bed.target;
                    }
                    this.state.updateTemperatures(temperatures);
                    
                    // Update position
                    if (result.toolhead) {
                        const position = {
                            x: result.toolhead.position[0],
                            y: result.toolhead.position[1],
                            z: result.toolhead.position[2],
                            e: result.toolhead.position[3]
                        };
                        this.state.updatePosition(position);
                        
                        // Update homing status
                        const homed = {
                            x: result.toolhead.homed_axes.includes('x'),
                            y: result.toolhead.homed_axes.includes('y'),
                            z: result.toolhead.homed_axes.includes('z')
                        };
                        this.state.updateHomedStatus(homed);
                    }
                    
                    // Update printer state
                    if (result.print_stats) {
                        this.state.set('system.status', result.print_stats.state);
                    }
                }
                
                this.updateConnectionStatus(true);
                
                // Update last update time
                const now = new Date().toLocaleTimeString();
                const lastUpdateEl = document.getElementById('lastUpdate');
                if (lastUpdateEl) {
                    lastUpdateEl.textContent = `Last Update: ${now}`;
                }
            } else {
                this.updateConnectionStatus(false);
            }

        } catch (error) {
            console.error('Update failed:', error);
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(connected) {
        this.isConnected = connected;
        
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        const connectionInfo = document.getElementById('connectionInfo');
        
        if (connected) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Connected';
            if (connectionInfo) {
                connectionInfo.textContent = 'API: Connected';
            }
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Disconnected';
            if (connectionInfo) {
                connectionInfo.textContent = 'API: Disconnected';
            }
        }
    }

    async handleEmergencyStop() {
        try {
            this.log('warning', 'Emergency stop activated by user');
            
            // Disable emergency stop button temporarily
            const btn = document.getElementById('emergencyStop');
            if (btn) {
                btn.disabled = true;
                btn.textContent = 'Stopping...';
            }

            // Send emergency stop command directly to Moonraker
            await window.moonrakerAPI.emergencyStop();
            
            this.log('error', 'EMERGENCY STOP ACTIVATED');
            this.state.setEmergencyStop(true);
            
            // Update UI to reflect emergency state
            this.ui.setEmergencyMode(true);

        } catch (error) {
            console.error('Emergency stop failed:', error);
            this.log('error', `Emergency stop failed: ${error.message}`);
        } finally {
            // Re-enable button
            const btn = document.getElementById('emergencyStop');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<span class="emergency-icon">⚠</span> Emergency Stop';
            }
        }
    }

    handleConnectionChange(online) {
        if (online) {
            this.log('info', 'Network connection restored');
            // Attempt to reconnect
            setTimeout(() => this.loadInitialData(), 1000);
        } else {
            this.log('warning', 'Network connection lost');
            this.updateConnectionStatus(false);
        }
    }

    log(level, message) {
        // Add to console panel if available
        if (window.consolePanel) {
            window.consolePanel.addConsoleMessage(level, message);
        }
        
        // Console log
        console[level === 'error' ? 'error' : 'log'](`[${level.toUpperCase()}] ${message}`);
    }

    cleanup() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        console.log('Printer Buddy App cleaned up');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    window.printerBuddyApp = new PrinterBuddyApp();
    await window.printerBuddyApp.initialize();
});