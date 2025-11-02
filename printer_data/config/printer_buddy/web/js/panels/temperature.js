/**
 * Temperature Panel Manager
 * 
 * Handles temperature controls and monitoring.
 */

class TemperaturePanel {
    constructor(api, state) {
        this.api = api;
        this.state = state;
        this.elements = {};
    }

    async initialize() {
        console.log('Initializing Temperature Panel...');
        
        // Cache DOM elements
        this.elements = {
            // Temperature controls
            bedTempToggle: document.getElementById('bedTempToggle'),
            bedTempSlider: document.getElementById('bedTempSlider'),
            bedTempCurrent: document.getElementById('bedTempCurrent'),
            bedTempTarget: document.getElementById('bedTempTarget'),
            
            extruderTempToggle: document.getElementById('extruderTempToggle'),
            extruderTempSlider: document.getElementById('extruderTempSlider'),
            extruderTempCurrent: document.getElementById('extruderTempCurrent'),
            extruderTempTarget: document.getElementById('extruderTempTarget')
        };

        // Setup event listeners
        this.setupEventListeners();
        
        // Subscribe to state changes
        this.setupStateSubscriptions();
        
        // Initial update
        this.updateDisplay();
        
        console.log('Temperature Panel initialized');
    }

    setupEventListeners() {
        // Temperature toggles
        this.elements.bedTempToggle.addEventListener('change', (e) => {
            this.handleTempToggle('bed', e.target.checked);
        });

        this.elements.extruderTempToggle.addEventListener('change', (e) => {
            this.handleTempToggle('extruder', e.target.checked);
        });

        // Temperature sliders
        this.elements.bedTempSlider.addEventListener('input', (e) => {
            this.handleTempSliderChange('bed', parseInt(e.target.value));
        });

        this.elements.extruderTempSlider.addEventListener('input', (e) => {
            this.handleTempSliderChange('extruder', parseInt(e.target.value));
        });

        // Slider release (apply temperature)
        this.elements.bedTempSlider.addEventListener('change', (e) => {
            this.applyTempTarget('bed', parseInt(e.target.value));
        });

        this.elements.extruderTempSlider.addEventListener('change', (e) => {
            this.applyTempTarget('extruder', parseInt(e.target.value));
        });
    }

    setupStateSubscriptions() {
        // Temperature changes
        this.state.subscribe('printer.temperatures', (temperatures) => {
            this.updateTemperatureDisplays(temperatures);
        });

        // Emergency stop state
        this.state.subscribe('system.emergency_stop', (emergencyStop) => {
            this.updateControlsAvailability(!emergencyStop);
        });

        // Printer status changes
        this.state.subscribe('system.status', (status) => {
            this.updateControlsAvailability(status !== 'error' && status !== 'emergency_stop');
        });
    }

    updateDisplay() {
        const temperatures = this.state.get('printer.temperatures') || {};
        this.updateTemperatureDisplays(temperatures);
        
        const emergencyStop = this.state.get('system.emergency_stop') || false;
        const systemStatus = this.state.get('system.status') || 'unknown';
        this.updateControlsAvailability(!emergencyStop && systemStatus !== 'error');
    }

    handleTempToggle(heater, enabled) {
        if (enabled) {
            // Turn on heater with current slider value
            const slider = heater === 'bed' ? this.elements.bedTempSlider : this.elements.extruderTempSlider;
            const target = parseInt(slider.value);
            this.applyTempTarget(heater, target);
        } else {
            // Turn off heater
            this.applyTempTarget(heater, 0);
        }
    }

    handleTempSliderChange(heater, value) {
        // Update target display in real-time
        const targetElement = heater === 'bed' ? this.elements.bedTempTarget : this.elements.extruderTempTarget;
        targetElement.textContent = `${value}°C`;
    }

    async applyTempTarget(heater, target) {
        try {
            console.log(`Setting ${heater} temperature to ${target}°C`);
            
            // Use Moonraker API to set temperature
            if (heater === 'bed') {
                await window.moonrakerAPI.setBedTemp(target);
            } else if (heater === 'extruder') {
                await window.moonrakerAPI.setExtruderTemp(target);
            }
            
            // Update toggle state based on target
            const toggle = heater === 'bed' ? this.elements.bedTempToggle : this.elements.extruderTempToggle;
            toggle.checked = target > 0;
            
            console.log(`Successfully set ${heater} temperature to ${target}°C`);
            
        } catch (error) {
            console.error(`Failed to set ${heater} temperature:`, error);
            // Show error to user via console panel
            if (window.consolePanel) {
                window.consolePanel.addConsoleMessage('error', `Failed to set ${heater} temperature: ${error.message}`);
            }
        }
    }

    updateTemperatureDisplays(temperatures) {
        // Update bed temperature
        if (temperatures.bed !== undefined) {
            if (temperatures.bed === null) {
                this.elements.bedTempCurrent.textContent = '--';
            } else {
                this.elements.bedTempCurrent.textContent = `${Math.round(temperatures.bed)}°C`;
            }
        }
        if (temperatures.bed_target !== undefined) {
            if (temperatures.bed_target === null) {
                this.elements.bedTempTarget.textContent = '--';
                this.elements.bedTempSlider.value = 0;
                this.elements.bedTempToggle.checked = false;
            } else {
                this.elements.bedTempTarget.textContent = `${Math.round(temperatures.bed_target)}°C`;
                this.elements.bedTempSlider.value = temperatures.bed_target;
                this.elements.bedTempToggle.checked = temperatures.bed_target > 0;
            }
        }

        // Update extruder temperature
        if (temperatures.extruder !== undefined) {
            if (temperatures.extruder === null) {
                this.elements.extruderTempCurrent.textContent = '--';
            } else {
                this.elements.extruderTempCurrent.textContent = `${Math.round(temperatures.extruder)}°C`;
            }
        }
        if (temperatures.extruder_target !== undefined) {
            if (temperatures.extruder_target === null) {
                this.elements.extruderTempTarget.textContent = '--';
                this.elements.extruderTempSlider.value = 0;
                this.elements.extruderTempToggle.checked = false;
            } else {
                this.elements.extruderTempTarget.textContent = `${Math.round(temperatures.extruder_target)}°C`;
                this.elements.extruderTempSlider.value = temperatures.extruder_target;
                this.elements.extruderTempToggle.checked = temperatures.extruder_target > 0;
            }
        }
    }

    updateControlsAvailability(available) {
        // Disable/enable all control elements based on system state
        const allControls = [
            this.elements.bedTempToggle,
            this.elements.bedTempSlider,
            this.elements.extruderTempToggle,
            this.elements.extruderTempSlider
        ];

        allControls.forEach(element => {
            if (element) {
                element.disabled = !available;
                if (!available) {
                    element.classList.add('disabled');
                } else {
                    element.classList.remove('disabled');
                }
            }
        });
    }
}

// Initialize the temperature panel when the DOM is loaded
window.temperaturePanel = null;