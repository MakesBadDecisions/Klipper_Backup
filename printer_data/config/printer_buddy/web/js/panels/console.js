// Console Panel for Printer Buddy
// Handles display of system logs and real-time Klipper console output

class ConsolePanel {
    constructor() {
        this.maxLines = 1000; // Keep last 1000 lines in memory
        this.consoleLines = [];
        this.logFiles = [];
        this.activeLogFile = null;
        this.autoScroll = true;
        this.filterLevel = 'all'; // all, info, warning, error
        
        this.init();
    }

    init() {
        this.createPanelHTML();
        this.bindEvents();
        this.loadLogFiles();
        this.connectWebSocket();
    }

    createPanelHTML() {
        const panelHTML = `
            <div class="panel-header">
                <h3>Console & Logs</h3>
                <div class="console-controls">
                    <select id="logFileSelect">
                        <option value="console">Live Console</option>
                    </select>
                    <select id="logLevelFilter">
                        <option value="all">All Messages</option>
                        <option value="info">Info & Above</option>
                        <option value="warning">Warning & Above</option>
                        <option value="error">Errors Only</option>
                    </select>
                    <button id="clearConsole" class="btn-secondary">Clear</button>
                    <button id="toggleAutoScroll" class="btn-secondary active">Auto-scroll</button>
                </div>
            </div>
            <div class="console-container">
                <div id="consoleOutput" class="console-output"></div>
            </div>
            <div class="console-input">
                <input type="text" id="gcodeInput" placeholder="Enter G-code command..." />
                <button id="sendGcode" class="btn-primary">Send</button>
            </div>
        `;

        const panel = document.createElement('div');
        panel.className = 'panel console-panel';
        panel.id = 'consolePanel';
        panel.innerHTML = panelHTML;

        // Add to main container
        const mainContainer = document.querySelector('.main-content');
        if (mainContainer) {
            mainContainer.appendChild(panel);
        }
    }

    bindEvents() {
        // Clear console
        document.getElementById('clearConsole').addEventListener('click', () => {
            this.clearConsole();
        });

        // Toggle auto-scroll
        document.getElementById('toggleAutoScroll').addEventListener('click', (e) => {
            this.autoScroll = !this.autoScroll;
            e.target.textContent = this.autoScroll ? 'Auto-scroll' : 'Manual';
            e.target.classList.toggle('active', this.autoScroll);
        });

        // Log file selection
        document.getElementById('logFileSelect').addEventListener('change', (e) => {
            if (e.target.value === 'console') {
                this.showLiveConsole();
            } else {
                this.loadLogFile(e.target.value);
            }
        });

        // Filter level
        document.getElementById('logLevelFilter').addEventListener('change', (e) => {
            this.filterLevel = e.target.value;
            this.refreshDisplay();
        });

        // G-code input
        document.getElementById('gcodeInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendGcode();
            }
        });

        document.getElementById('sendGcode').addEventListener('click', () => {
            this.sendGcode();
        });

        // Manual scroll detection
        const consoleOutput = document.getElementById('consoleOutput');
        if (consoleOutput) {
            consoleOutput.addEventListener('scroll', () => {
                const isAtBottom = consoleOutput.scrollTop + consoleOutput.clientHeight >= consoleOutput.scrollHeight - 10;
                if (!isAtBottom && this.autoScroll) {
                    // User scrolled up, temporarily disable auto-scroll
                    this.autoScroll = false;
                    const toggleBtn = document.getElementById('toggleAutoScroll');
                    toggleBtn.textContent = 'Manual';
                    toggleBtn.classList.remove('active');
                }
            });
        }
    }

    async loadLogFiles() {
        try {
            const response = await fetch('/api/logs/list');
            const data = await response.json();
            
            if (data.success) {
                this.logFiles = data.files;
                this.updateLogFileSelect();
            }
        } catch (error) {
            console.error('Failed to load log files:', error);
        }
    }

    updateLogFileSelect() {
        const select = document.getElementById('logFileSelect');
        if (!select) return;
        
        // Clear existing options except console
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }

        // Add log files
        this.logFiles.forEach(file => {
            const option = document.createElement('option');
            option.value = file.path;
            option.textContent = file.name;
            select.appendChild(option);
        });
    }

    async loadLogFile(filePath) {
        try {
            const response = await fetch(`/api/logs/file?path=${encodeURIComponent(filePath)}`);
            const data = await response.json();
            
            if (data.success) {
                this.activeLogFile = filePath;
                this.displayLogContent(data.content);
            }
        } catch (error) {
            console.error('Failed to load log file:', error);
            this.addConsoleMessage('error', `Failed to load log file: ${filePath}`);
        }
    }

    displayLogContent(content) {
        const consoleOutput = document.getElementById('consoleOutput');
        if (!consoleOutput) return;
        
        consoleOutput.innerHTML = '';
        
        const lines = content.split('\n');
        lines.forEach(line => {
            if (line.trim()) {
                this.addLogLine(line);
            }
        });
        
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }

    showLiveConsole() {
        this.activeLogFile = null;
        this.refreshDisplay();
    }

    connectWebSocket() {
        // For now, use polling to get log messages from core API
        console.log('Setting up log polling from core API...');
        
        // Initial message
        setTimeout(() => {
            this.addConsoleMessage('info', 'Printer Buddy Console initialized');
        }, 1000);
        
        // Start polling for log messages
        this.startLogPolling();
        
        // Keep simulation for Moonraker messages
        this.simulateConsoleMessages();
    }
    
    startLogPolling() {
        let lastTimestamp = 0;
        
        const pollLogs = async () => {
            try {
                const response = await fetch(`/api/logs/stream?since=${lastTimestamp}`);
                const data = await response.json();
                
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        this.addConsoleMessage(msg.level, msg.message, new Date(msg.timestamp * 1000));
                        lastTimestamp = Math.max(lastTimestamp, msg.timestamp);
                    });
                }
            } catch (error) {
                console.error('Error polling logs:', error);
            }
        };
        
        // Poll every 2 seconds
        setInterval(pollLogs, 2000);
        
        // Initial poll
        pollLogs();
    }
    
    simulateConsoleMessages() {
        const messages = [
            { level: 'info', text: 'Printer Buddy Console initialized' },
            { level: 'info', text: '// Waiting for printer data...' },
            { level: 'info', text: '// Enter G-code commands below' }
        ];
        
        let messageIndex = 0;
        setInterval(() => {
            if (!this.activeLogFile) { // Only show if on live console
                const message = messages[messageIndex % messages.length];
                this.addConsoleMessage(message.level, message.text);
                messageIndex++;
            }
        }, 8000); // New message every 8 seconds
    }

    addConsoleMessage(level, message, timestamp = null) {
        if (!timestamp) {
            timestamp = new Date();
        }

        const logEntry = {
            timestamp: timestamp,
            level: level,
            message: message,
            source: 'console'
        };

        this.consoleLines.push(logEntry);
        
        // Keep only the last maxLines
        if (this.consoleLines.length > this.maxLines) {
            this.consoleLines = this.consoleLines.slice(-this.maxLines);
        }

        // Only display if we're showing live console
        if (!this.activeLogFile) {
            this.displayLogEntry(logEntry);
        }
    }

    addLogLine(line) {
        // Parse log line and determine level
        let level = 'info';
        if (line.includes('ERROR') || line.includes('Error')) {
            level = 'error';
        } else if (line.includes('WARNING') || line.includes('Warning')) {
            level = 'warning';
        }

        const logEntry = {
            timestamp: this.parseTimestamp(line),
            level: level,
            message: line,
            source: 'log'
        };

        this.displayLogEntry(logEntry);
    }

    displayLogEntry(entry) {
        if (!this.shouldShowEntry(entry)) {
            return;
        }

        const consoleOutput = document.getElementById('consoleOutput');
        if (!consoleOutput) return;
        
        const logElement = document.createElement('div');
        logElement.className = `console-line console-${entry.level}`;
        
        const timestamp = entry.timestamp.toLocaleTimeString();
        logElement.innerHTML = `
            <span class="console-timestamp">${timestamp}</span>
            <span class="console-message">${this.escapeHtml(entry.message)}</span>
        `;

        consoleOutput.appendChild(logElement);

        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }

    shouldShowEntry(entry) {
        if (this.filterLevel === 'all') return true;
        if (this.filterLevel === 'error') return entry.level === 'error';
        if (this.filterLevel === 'warning') return entry.level === 'warning' || entry.level === 'error';
        if (this.filterLevel === 'info') return true; // info includes everything
        return true;
    }

    refreshDisplay() {
        const consoleOutput = document.getElementById('consoleOutput');
        if (!consoleOutput) return;
        
        consoleOutput.innerHTML = '';

        if (this.activeLogFile) {
            // Re-load the active log file
            this.loadLogFile(this.activeLogFile);
        } else {
            // Show live console
            this.consoleLines.forEach(entry => {
                this.displayLogEntry(entry);
            });
        }
    }

    clearConsole() {
        if (this.activeLogFile) {
            // Clear display only
            const consoleOutput = document.getElementById('consoleOutput');
            if (consoleOutput) {
                consoleOutput.innerHTML = '';
            }
        } else {
            // Clear console history
            this.consoleLines = [];
            const consoleOutput = document.getElementById('consoleOutput');
            if (consoleOutput) {
                consoleOutput.innerHTML = '';
            }
        }
    }

    async sendGcode() {
        const input = document.getElementById('gcodeInput');
        if (!input) return;
        
        const command = input.value.trim();
        
        if (!command) return;

        try {
            // Show the command being sent
            this.addConsoleMessage('info', `> ${command}`);
            
            // Send directly to Moonraker
            const response = await window.moonrakerAPI.executeGcode(command);
            
            if (response.result === 'ok') {
                this.addConsoleMessage('success', 'Command executed successfully');
            } else {
                this.addConsoleMessage('warning', `Command response: ${response.result || 'Unknown'}`);
            }

            input.value = '';
        } catch (error) {
            console.error('Failed to send G-code:', error);
            this.addConsoleMessage('error', `Failed to send command: ${error.message}`);
        }
    }

    scrollToBottom() {
        const consoleOutput = document.getElementById('consoleOutput');
        if (consoleOutput) {
            consoleOutput.scrollTop = consoleOutput.scrollHeight;
        }
    }

    parseTimestamp(line) {
        // Try to parse timestamp from log line
        // This is a simple implementation, may need refinement
        const timestampMatch = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);
        if (timestampMatch) {
            return new Date(timestampMatch[1]);
        }
        return new Date();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Method to be called by WebSocket handler
    handleGcodeResponse(message) {
        // Handle notify_gcode_response from Moonraker
        let level = 'info';
        if (message.startsWith('!!')) {
            level = 'error';
        } else if (message.startsWith('//')) {
            level = 'info';
        }

        this.addConsoleMessage(level, message);
    }

    // Method to handle printer status updates
    handleStatusUpdate(status) {
        // Could show important status changes in console
        if (status.print_stats && status.print_stats.state) {
            const state = status.print_stats.state;
            if (state === 'printing') {
                this.addConsoleMessage('info', 'Print started');
            } else if (state === 'complete') {
                this.addConsoleMessage('info', 'Print completed');
            } else if (state === 'error') {
                this.addConsoleMessage('error', 'Print error occurred');
            }
        }
    }
}

// Initialize console panel when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.consolePanel = new ConsolePanel();
    });
} else {
    window.consolePanel = new ConsolePanel();
}