/**
 * State Manager for Web UI
 * 
 * Manages application state and notifies components of changes.
 */

class StateManager {
    constructor() {
        this.state = {
            system: {
                status: 'initializing',
                emergency_stop: false,
                safety_enabled: true,
                version: '2.0.0'
            },
            printer: {
                position: { x: 0, y: 0, z: 0 },
                homed: { x: false, y: false, z: false },
                temperatures: {},
                config_loaded: false
            },
            modules: {},
            commissioning: {
                active: false,
                current_test: null,
                progress: 0,
                results: []
            },
            ui: {
                panels: {
                    status: true,
                    commissioning: true,
                    modules: true,
                    logs: true
                }
            }
        };
        
        this.listeners = new Map();
    }

    // Subscribe to state changes
    subscribe(path, callback) {
        if (!this.listeners.has(path)) {
            this.listeners.set(path, new Set());
        }
        this.listeners.get(path).add(callback);
        
        // Return unsubscribe function
        return () => {
            const callbacks = this.listeners.get(path);
            if (callbacks) {
                callbacks.delete(callback);
            }
        };
    }

    // Notify listeners of state changes
    notify(path, newValue, oldValue) {
        const callbacks = this.listeners.get(path);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(newValue, oldValue, path);
                } catch (error) {
                    console.error('Error in state listener:', error);
                }
            });
        }
        
        // Also notify wildcard listeners
        const wildcardCallbacks = this.listeners.get('*');
        if (wildcardCallbacks) {
            wildcardCallbacks.forEach(callback => {
                try {
                    callback(newValue, oldValue, path);
                } catch (error) {
                    console.error('Error in wildcard state listener:', error);
                }
            });
        }
    }

    // Get state value by path
    get(path) {
        const keys = path.split('.');
        let current = this.state;
        
        for (const key of keys) {
            if (current === null || current === undefined) {
                return undefined;
            }
            current = current[key];
        }
        
        return current;
    }

    // Set state value by path
    set(path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        let current = this.state;
        
        // Navigate to parent object
        for (const key of keys) {
            if (!(key in current)) {
                current[key] = {};
            }
            current = current[key];
        }
        
        const oldValue = current[lastKey];
        current[lastKey] = value;
        
        // Notify listeners
        this.notify(path, value, oldValue);
    }

    // Update multiple values
    update(updates) {
        for (const [path, value] of Object.entries(updates)) {
            this.set(path, value);
        }
    }

    // Merge object into state
    merge(path, object) {
        const current = this.get(path) || {};
        const merged = { ...current, ...object };
        this.set(path, merged);
    }

    // System status methods
    updateSystemStatus(status) {
        this.merge('system', status);
    }

    setEmergencyStop(active) {
        this.set('system.emergency_stop', active);
        this.set('system.status', active ? 'emergency_stop' : 'ready');
    }

    // Printer methods
    updatePosition(position) {
        this.merge('printer.position', position);
    }

    updateTemperatures(temperatures) {
        this.merge('printer.temperatures', temperatures);
    }

    updateHomedStatus(homed) {
        this.merge('printer.homed', homed);
    }

    // Module methods
    updateModules(modules) {
        this.set('modules', modules);
    }

    updateModuleStatus(moduleId, status) {
        this.set(`modules.${moduleId}.status`, status);
    }

    // Commissioning methods
    setCommissioningActive(active) {
        this.set('commissioning.active', active);
    }

    setCurrentTest(testType) {
        this.set('commissioning.current_test', testType);
    }

    setCommissioningProgress(progress) {
        this.set('commissioning.progress', Math.max(0, Math.min(100, progress)));
    }

    addCommissioningResult(result) {
        const results = this.get('commissioning.results') || [];
        results.push({
            ...result,
            timestamp: new Date().toISOString()
        });
        this.set('commissioning.results', results);
    }

    // UI methods
    setPanelVisible(panel, visible) {
        this.set(`ui.panels.${panel}`, visible);
    }

    togglePanel(panel) {
        const current = this.get(`ui.panels.${panel}`);
        this.setPanelVisible(panel, !current);
    }

    // Configuration methods
    updateConfig(config) {
        this.merge('config', config);
    }

    // Utility methods
    getAll() {
        return JSON.parse(JSON.stringify(this.state));
    }

    reset() {
        const oldState = this.state;
        this.state = {
            system: { status: 'initializing', emergency_stop: false },
            printer: { position: { x: 0, y: 0, z: 0 }, temperatures: {} },
            modules: {},
            commissioning: { active: false, progress: 0, results: [] },
            ui: { panels: { status: true, commissioning: true, modules: true, logs: true } }
        };
        
        this.notify('*', this.state, oldState);
    }

    // Debug methods
    dump() {
        console.log('Current State:', this.getAll());
    }

    getListenerCount() {
        let total = 0;
        for (const callbacks of this.listeners.values()) {
            total += callbacks.size;
        }
        return total;
    }
}