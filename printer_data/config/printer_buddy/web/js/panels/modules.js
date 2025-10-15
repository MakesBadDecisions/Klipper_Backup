/**
 * Modules Panel Manager
 * 
 * Handles display and management of system modules.
 */

class ModulesPanel {
    constructor(api, state) {
        this.api = api;
        this.state = state;
        this.elements = {};
    }

    async initialize() {
        console.log('Initializing Modules Panel...');
        
        // Cache DOM elements
        this.elements = {
            modulesList: document.getElementById('modulesList')
        };

        // Subscribe to state changes
        this.setupStateSubscriptions();
        
        // Initial update
        this.updateDisplay();
        
        console.log('Modules Panel initialized');
    }

    setupStateSubscriptions() {
        // Modules state changes
        this.state.subscribe('modules', (modules) => {
            this.updateModulesList(modules);
        });
    }

    updateDisplay() {
        const modules = this.state.get('modules') || {};
        this.updateModulesList(modules);
    }

    updateModulesList(modules) {
        if (!this.elements.modulesList) return;

        // Clear current content
        this.elements.modulesList.innerHTML = '';

        const moduleEntries = Object.entries(modules);
        
        if (moduleEntries.length === 0) {
            this.showEmptyState();
            return;
        }

        // Create module items
        moduleEntries.forEach(([moduleId, moduleData]) => {
            const moduleElement = this.createModuleElement(moduleId, moduleData);
            this.elements.modulesList.appendChild(moduleElement);
        });
    }

    createModuleElement(moduleId, moduleData) {
        const moduleDiv = document.createElement('div');
        moduleDiv.className = 'module-item';
        moduleDiv.dataset.moduleId = moduleId;

        // Add status-specific styling
        const status = moduleData.status || 'unknown';
        if (status === 'error') {
            moduleDiv.classList.add('error');
        } else if (status === 'warning') {
            moduleDiv.classList.add('warning');
        }

        // Module info section
        const infoDiv = document.createElement('div');
        infoDiv.className = 'module-info';

        const nameEl = document.createElement('h3');
        nameEl.textContent = moduleData.name || moduleId;
        infoDiv.appendChild(nameEl);

        const detailsEl = document.createElement('p');
        const details = [];
        
        if (moduleData.version) {
            details.push(`v${moduleData.version}`);
        }
        
        if (moduleData.capabilities && moduleData.capabilities.length > 0) {
            details.push(`Capabilities: ${moduleData.capabilities.join(', ')}`);
        }
        
        detailsEl.textContent = details.join(' • ');
        infoDiv.appendChild(detailsEl);

        // Module status section
        const statusDiv = document.createElement('div');
        statusDiv.className = 'module-status';

        const statusDot = document.createElement('div');
        statusDot.className = `module-status-dot ${status}`;
        statusDiv.appendChild(statusDot);

        const statusText = document.createElement('span');
        statusText.textContent = this.formatModuleStatus(status);
        statusText.className = 'module-status-text';
        statusDiv.appendChild(statusText);

        // Assemble the module element
        moduleDiv.appendChild(infoDiv);
        moduleDiv.appendChild(statusDiv);

        // Add click handler for module details
        moduleDiv.addEventListener('click', () => {
            this.showModuleDetails(moduleId, moduleData);
        });

        return moduleDiv;
    }

    showEmptyState() {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'loading';
        emptyDiv.innerHTML = `
            <p>No modules detected</p>
            <small>Modules will appear here when the system is running</small>
        `;
        this.elements.modulesList.appendChild(emptyDiv);
    }

    showModuleDetails(moduleId, moduleData) {
        // Create modal or detailed view
        const details = this.formatModuleDetails(moduleId, moduleData);
        
        // For now, just log to console and show notification
        console.log('Module Details:', details);
        
        // You could extend this to show a modal dialog with detailed information
        const message = `${moduleData.name || moduleId}\nStatus: ${moduleData.status}\nVersion: ${moduleData.version}`;
        
        // Simple alert for now - could be replaced with a proper modal
        if (window.printerBuddyApp && window.printerBuddyApp.ui) {
            window.printerBuddyApp.ui.showNotification(
                `Module: ${moduleData.name || moduleId} - Status: ${moduleData.status}`,
                this.getNotificationType(moduleData.status)
            );
        }
    }

    formatModuleStatus(status) {
        const statusMap = {
            'uninitialized': 'Not Started',
            'initializing': 'Starting...',
            'ready': 'Ready',
            'active': 'Active',
            'error': 'Error',
            'disabled': 'Disabled',
            'unknown': 'Unknown'
        };
        
        return statusMap[status] || status;
    }

    formatModuleDetails(moduleId, moduleData) {
        return {
            id: moduleId,
            name: moduleData.name || 'Unknown',
            version: moduleData.version || 'Unknown',
            status: moduleData.status || 'Unknown',
            capabilities: moduleData.capabilities || [],
            description: moduleData.description || 'No description available',
            last_update: moduleData.last_update || null,
            error_message: moduleData.error_message || null
        };
    }

    getNotificationType(status) {
        switch (status) {
            case 'error':
                return 'error';
            case 'warning':
            case 'disabled':
                return 'warning';
            case 'ready':
            case 'active':
                return 'success';
            default:
                return 'info';
        }
    }

    // Manual refresh method
    async refresh() {
        try {
            const result = await this.api.getModules();
            if (result && result.modules) {
                this.state.updateModules(result.modules);
            }
        } catch (error) {
            console.error('Failed to refresh modules:', error);
            
            // Show error state
            if (this.elements.modulesList) {
                this.elements.modulesList.innerHTML = `
                    <div class="loading error">
                        <p>Failed to load modules</p>
                        <small>${error.message}</small>
                    </div>
                `;
            }
        }
    }

    // Get modules summary
    getModulesSummary() {
        const modules = this.state.get('modules') || {};
        const summary = {
            total: 0,
            ready: 0,
            active: 0,
            error: 0,
            disabled: 0
        };

        Object.values(modules).forEach(module => {
            summary.total++;
            
            const status = module.status || 'unknown';
            if (summary.hasOwnProperty(status)) {
                summary[status]++;
            }
        });

        return summary;
    }

    // Check if any critical modules have errors
    hasCriticalErrors() {
        const modules = this.state.get('modules') || {};
        
        return Object.values(modules).some(module => {
            const isCritical = module.capabilities && 
                module.capabilities.includes('safety_critical');
            const hasError = module.status === 'error';
            
            return isCritical && hasError;
        });
    }

    // Get list of modules by capability
    getModulesByCapability(capability) {
        const modules = this.state.get('modules') || {};
        
        return Object.entries(modules)
            .filter(([id, module]) => {
                return module.capabilities && 
                    module.capabilities.includes(capability);
            })
            .map(([id, module]) => ({ id, ...module }));
    }
}