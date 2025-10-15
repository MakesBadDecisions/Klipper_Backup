/**
 * UI Manager for Printer Buddy Web Interface
 * 
 * Handles common UI operations and panel management.
 */

class UIManager {
    constructor() {
        this.panels = new Map();
        this.emergencyMode = false;
    }

    initialize() {
        console.log('Initializing UI Manager...');
        
        // Initialize panel states
        document.querySelectorAll('.panel').forEach(panel => {
            const panelId = panel.id.replace('Panel', '');
            this.panels.set(panelId, {
                element: panel,
                visible: true,
                collapsed: false
            });
        });

        // Setup panel toggle functionality
        this.setupPanelToggles();
        
        console.log('UI Manager initialized');
    }

    setupPanelToggles() {
        document.querySelectorAll('.panel-toggle').forEach(button => {
            button.addEventListener('click', (e) => {
                const panelName = e.target.dataset.panel;
                if (panelName) {
                    this.togglePanelCollapse(panelName);
                }
            });
        });
    }

    togglePanel(panelName) {
        const panel = this.panels.get(panelName);
        if (!panel) return;

        panel.visible = !panel.visible;
        panel.element.style.display = panel.visible ? 'block' : 'none';
        
        console.log(`Panel ${panelName} ${panel.visible ? 'shown' : 'hidden'}`);
    }

    togglePanelCollapse(panelName) {
        const panel = this.panels.get(panelName);
        if (!panel) return;

        const content = panel.element.querySelector('.panel-content');
        const toggle = panel.element.querySelector('.panel-toggle');
        
        if (!content || !toggle) return;

        panel.collapsed = !panel.collapsed;
        
        if (panel.collapsed) {
            content.style.display = 'none';
            toggle.textContent = '+';
            panel.element.classList.add('collapsed');
        } else {
            content.style.display = 'block';
            toggle.textContent = '−';
            panel.element.classList.remove('collapsed');
        }
        
        console.log(`Panel ${panelName} ${panel.collapsed ? 'collapsed' : 'expanded'}`);
    }

    showPanel(panelName) {
        const panel = this.panels.get(panelName);
        if (panel && !panel.visible) {
            this.togglePanel(panelName);
        }
    }

    hidePanel(panelName) {
        const panel = this.panels.get(panelName);
        if (panel && panel.visible) {
            this.togglePanel(panelName);
        }
    }

    setEmergencyMode(active) {
        this.emergencyMode = active;
        
        const body = document.body;
        const emergencyBtn = document.getElementById('emergencyStop');
        
        if (active) {
            body.classList.add('emergency-mode');
            if (emergencyBtn) {
                emergencyBtn.classList.add('activated');
                emergencyBtn.innerHTML = '<span class="emergency-icon">⚠</span> EMERGENCY STOP ACTIVE';
            }
            
            // Disable non-critical UI elements
            this.disableControls(true);
            
        } else {
            body.classList.remove('emergency-mode');
            if (emergencyBtn) {
                emergencyBtn.classList.remove('activated');
                emergencyBtn.innerHTML = '<span class="emergency-icon">⚠</span> Emergency Stop';
            }
            
            // Re-enable controls
            this.disableControls(false);
        }
        
        console.log(`Emergency mode ${active ? 'activated' : 'deactivated'}`);
    }

    disableControls(disable) {
        // Disable commissioning controls
        const commissioningControls = document.querySelectorAll('#commissioningPanel button, #commissioningPanel select');
        commissioningControls.forEach(control => {
            control.disabled = disable;
        });
        
        // Add visual indicator
        const panels = document.querySelectorAll('.panel');
        panels.forEach(panel => {
            if (disable) {
                panel.classList.add('disabled');
            } else {
                panel.classList.remove('disabled');
            }
        });
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '1rem 1.5rem',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '500',
            zIndex: '9999',
            maxWidth: '400px',
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.3)',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        // Set background color based on type
        const colors = {
            info: '#3498db',
            success: '#27ae60',
            warning: '#f39c12',
            error: '#e74c3c'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
        
        console.log(`Notification: [${type.toUpperCase()}] ${message}`);
    }

    updateStatusIndicator(element, status, text = null) {
        if (!element) return;
        
        // Remove existing status classes
        element.classList.remove('status-online', 'status-offline', 'status-warning', 'status-error');
        
        // Add new status class
        element.classList.add(`status-${status}`);
        
        // Update text if provided
        if (text !== null) {
            element.textContent = text;
        }
    }

    createProgressBar(container, initialValue = 0) {
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        
        const progressFill = document.createElement('div');
        progressFill.className = 'progress-fill';
        progressFill.style.width = `${initialValue}%`;
        
        progressBar.appendChild(progressFill);
        container.appendChild(progressBar);
        
        return {
            element: progressBar,
            update: (value) => {
                const clampedValue = Math.max(0, Math.min(100, value));
                progressFill.style.width = `${clampedValue}%`;
            }
        };
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return 'Never';
        
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }

    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    // Utility method to safely update text content
    updateTextContent(selector, text) {
        const element = document.querySelector(selector) || document.getElementById(selector);
        if (element) {
            element.textContent = text;
        }
    }

    // Utility method to safely add HTML content
    updateHTMLContent(selector, html) {
        const element = document.querySelector(selector) || document.getElementById(selector);
        if (element) {
            element.innerHTML = html;
        }
    }

    // Get panel element by name
    getPanel(panelName) {
        return this.panels.get(panelName)?.element;
    }

    // Check if panel is visible
    isPanelVisible(panelName) {
        return this.panels.get(panelName)?.visible || false;
    }

    // Reset UI to initial state
    reset() {
        this.setEmergencyMode(false);
        
        // Reset all panels to visible and expanded
        this.panels.forEach((panel, name) => {
            panel.visible = true;
            panel.collapsed = false;
            panel.element.style.display = 'block';
            
            const content = panel.element.querySelector('.panel-content');
            const toggle = panel.element.querySelector('.panel-toggle');
            
            if (content) content.style.display = 'block';
            if (toggle) toggle.textContent = '−';
            
            panel.element.classList.remove('collapsed', 'disabled');
        });
        
        console.log('UI reset to initial state');
    }
}