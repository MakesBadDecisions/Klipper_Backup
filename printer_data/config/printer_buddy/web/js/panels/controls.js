/**
 * Controls Panel Manager
 * 
 * Handles manual jog controls and homing controls.
 */

class ControlsPanel {
    constructor(api, state) {
        this.api = api;
        this.state = state;
        this.elements = {};
        this.currentDistance = 0.01; // Default jog distance
        this.jogInProgress = false;
        this.homeInProgress = false;
    }

    async initialize() {
        console.log('Initializing Controls Panel...');
        
        // Cache DOM elements
        this.elements = {
            // Jog controls
            distanceButtons: document.querySelectorAll('.distance-btn'),
            movementButtons: document.querySelectorAll('.movement-btn'),
            
            // Home controls
            homeButtons: document.querySelectorAll('.home-btn'),
            homeIndividualButtons: document.querySelectorAll('.home-btn-small')
        };

        // Setup event listeners
        this.setupEventListeners();
        
        // Subscribe to state changes
        this.setupStateSubscriptions();
        
        // Initial update
        this.updateDisplay();
        
        console.log('Controls Panel initialized');
    }

    setupEventListeners() {
        // Distance button selection
        this.elements.distanceButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectDistance(parseFloat(e.target.dataset.distance));
            });
        });

        // Movement button clicks  
        this.elements.movementButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleJogCommand(e.currentTarget.dataset.axis, e.currentTarget.dataset.direction);
            });
        });

        // Home button clicks
        this.elements.homeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleHomeCommand(e.target.dataset.axes);
            });
        });

        this.elements.homeIndividualButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleHomeCommand(e.target.dataset.axes);
            });
        });
    }

    setupStateSubscriptions() {
        // Emergency stop state
        this.state.subscribe('system.emergency_stop', (emergencyStop) => {
            this.updateControlsAvailability(!emergencyStop);
        });

        // Printer status changes
        this.state.subscribe('system.status', (status) => {
            this.updateControlsAvailability(status !== 'error' && status !== 'emergency_stop');
        });

        // Homed axes changes
        this.state.subscribe('printer.homed', (homed) => {
            this.updateHomedStatus(homed);
        });
    }

    updateDisplay() {
        const emergencyStop = this.state.get('system.emergency_stop') || false;
        const systemStatus = this.state.get('system.status') || 'unknown';
        this.updateControlsAvailability(!emergencyStop && systemStatus !== 'error');
        
        const homed = this.state.get('printer.homed') || {};
        this.updateHomedStatus(homed);
    }

    selectDistance(distance) {
        this.currentDistance = distance;
        
        // Update button styling
        this.elements.distanceButtons.forEach(btn => {
            btn.classList.remove('active');
            if (parseFloat(btn.dataset.distance) === distance) {
                btn.classList.add('active');
            }
        });
    }

    async handleJogCommand(axis, direction) {
        if (this.jogInProgress) {
            console.log('Jog already in progress, ignoring command');
            return;
        }

        // Parse direction
        const movements = this.parseJogDirection(direction, this.currentDistance);
        if (!movements) {
            console.error('Invalid jog direction:', direction);
            return;
        }

        try {
            this.jogInProgress = true;
            this.updateJogButtonsState(false);

            // Send jog command via API
            await this.sendJogCommand(movements);
            
            console.log(`Jog command sent: ${JSON.stringify(movements)}`);

        } catch (error) {
            console.error('Jog command failed:', error);
            // TODO: Show error to user
        } finally {
            this.jogInProgress = false;
            this.updateJogButtonsState(true);
        }
    }

    parseJogDirection(direction, distance) {
        const movements = {};
        
        // Parse the direction string (e.g., "+x", "-y", "+x+y", etc.)
        if (direction.includes('+x')) movements.x = distance;
        if (direction.includes('-x')) movements.x = -distance;
        if (direction.includes('+y')) movements.y = distance;
        if (direction.includes('-y')) movements.y = -distance;
        if (direction.includes('+z')) movements.z = distance;
        if (direction.includes('-z')) movements.z = -distance;

        return Object.keys(movements).length > 0 ? movements : null;
    }

    async sendJogCommand(movements) {
        console.log('Sending jog command:', movements);
        
        // Convert movements to G-code commands
        const gcode = [];
        
        // Use relative positioning
        gcode.push('G91');
        
        // Build movement command
        const moveCmd = ['G1'];
        if (movements.x !== undefined) moveCmd.push(`X${movements.x}`);
        if (movements.y !== undefined) moveCmd.push(`Y${movements.y}`);
        if (movements.z !== undefined) moveCmd.push(`Z${movements.z}`);
        moveCmd.push('F3000'); // 50mm/s feed rate
        
        gcode.push(moveCmd.join(' '));
        
        // Return to absolute positioning
        gcode.push('G90');
        
        // Send to Moonraker
        await window.moonrakerAPI.executeGcode(gcode.join('\n'));
    }

    updateJogButtonsState(enabled) {
        this.elements.movementButtons.forEach(btn => {
            btn.disabled = !enabled;
        });
    }

    async handleHomeCommand(axes) {
        if (this.homeInProgress) {
            console.log('Homing already in progress, ignoring command');
            return;
        }

        try {
            this.homeInProgress = true;
            this.updateHomeButtonsState(false);

            // Send home command via API
            await this.sendHomeCommand(axes);
            
            console.log(`Home command sent for axes: ${axes}`);

        } catch (error) {
            console.error('Home command failed:', error);
            // TODO: Show error to user
        } finally {
            this.homeInProgress = false;
            this.updateHomeButtonsState(true);
        }
    }

    async sendHomeCommand(axes) {
        console.log('Sending home command for axes:', axes);
        
        // Convert axes to G-code home command
        let gcode;
        if (axes === 'all' || axes === 'xyz') {
            gcode = 'G28'; // Home all axes
        } else {
            gcode = `G28 ${axes.toUpperCase()}`; // Home specific axes
        }
        
        // Send to Moonraker
        await window.moonrakerAPI.executeGcode(gcode);
    }

    updateHomeButtonsState(enabled) {
        [...this.elements.homeButtons, ...this.elements.homeIndividualButtons].forEach(btn => {
            btn.disabled = !enabled;
        });
    }

    updateHomedStatus(homed) {
        // Update visual feedback for homed axes
        // Could add visual indicators to show which axes are homed
        console.log('Homed axes status:', homed);
    }

    updateControlsAvailability(available) {
        // Disable/enable all control elements based on system state
        const allControls = [
            ...this.elements.distanceButtons,
            ...this.elements.movementButtons,
            ...this.elements.homeButtons,
            ...this.elements.homeIndividualButtons
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

// Initialize the controls panel when the DOM is loaded
window.controlsPanel = null;