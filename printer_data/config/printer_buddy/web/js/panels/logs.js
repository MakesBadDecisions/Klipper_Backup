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
        // This will be implemented to connect to Moonraker WebSocket
        // For now, we'll use polling or mock data
        console.log('WebSocket connection for console would be established here');
        
        // Simulate some console messages for testing
        setTimeout(() => {
            this.addConsoleMessage('info', 'Printer Buddy Console initialized');
            this.addConsoleMessage('info', 'Connected to Klipper');
        }, 1000);
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
            
            const response = await fetch('/api/gcode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ command: command })
            });

            const data = await response.json();
            
            if (data.success) {
                // Response will come through WebSocket, but show confirmation
                this.addConsoleMessage('info', 'Command sent');
            } else {
                this.addConsoleMessage('error', `Command failed: ${data.error}`);
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

    addLog(level, message, timestamp = null) {
        const logEntry = {
            timestamp: timestamp || new Date(),
            level: level.toLowerCase(),
            message: message
        };

        // Add to internal logs array
        this.logs.push(logEntry);
        
        // Maintain max logs limit
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }

        // Update display
        this.updateLogDisplay();
        
        // Auto-scroll if enabled
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }

    updateLogDisplay() {
        if (!this.elements.logContainer) return;

        // Clear container
        this.elements.logContainer.innerHTML = '';

        // Add log entries
        this.logs.forEach(log => {
            const logElement = this.createLogElement(log);
            this.elements.logContainer.appendChild(logElement);
        });
    }

    createLogElement(log) {
        const logDiv = document.createElement('div');
        logDiv.className = 'log-entry';

        // Timestamp
        const timeEl = document.createElement('span');
        timeEl.className = 'log-time';
        timeEl.textContent = this.formatTimestamp(log.timestamp);
        logDiv.appendChild(timeEl);

        // Level
        const levelEl = document.createElement('span');
        levelEl.className = `log-level ${log.level}`;
        levelEl.textContent = log.level.toUpperCase().padEnd(5);
        logDiv.appendChild(levelEl);

        // Message
        const messageEl = document.createElement('span');
        messageEl.className = 'log-message';
        messageEl.textContent = log.message;
        logDiv.appendChild(messageEl);

        // Add click handler for copying log entry
        logDiv.addEventListener('click', () => {
            this.copyLogEntry(log);
        });

        logDiv.title = 'Click to copy log entry';

        return logDiv;
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    copyLogEntry(log) {
        const logText = `${this.formatTimestamp(log.timestamp)} [${log.level.toUpperCase()}] ${log.message}`;
        
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(logText).then(() => {
                this.showCopyNotification();
            }).catch(err => {
                console.error('Failed to copy log entry:', err);
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = logText;
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                this.showCopyNotification();
            } catch (err) {
                console.error('Failed to copy log entry:', err);
            }
            
            document.body.removeChild(textArea);
        }
    }

    showCopyNotification() {
        // Show temporary notification
        if (window.printerBuddyApp && window.printerBuddyApp.ui) {
            window.printerBuddyApp.ui.showNotification('Log entry copied to clipboard', 'info', 2000);
        }
    }

    clearLogs() {
        this.logs = [];
        this.updateLogDisplay();
        this.addLog('info', 'Logs cleared');
    }

    scrollToBottom() {
        if (this.elements.logContainer) {
            this.elements.logContainer.scrollTop = this.elements.logContainer.scrollHeight;
        }
    }

    // Filter logs by level
    filterByLevel(level) {
        const filteredLogs = this.logs.filter(log => log.level === level.toLowerCase());
        
        // Temporarily display filtered logs
        this.displayFilteredLogs(filteredLogs);
    }

    displayFilteredLogs(filteredLogs) {
        if (!this.elements.logContainer) return;

        // Clear container
        this.elements.logContainer.innerHTML = '';

        if (filteredLogs.length === 0) {
            const noLogsEl = document.createElement('div');
            noLogsEl.className = 'log-entry';
            noLogsEl.innerHTML = `
                <span class="log-time">--:--:--</span>
                <span class="log-level info">INFO</span>
                <span class="log-message">No logs match the current filter</span>
            `;
            this.elements.logContainer.appendChild(noLogsEl);
            return;
        }

        // Add filtered log entries
        filteredLogs.forEach(log => {
            const logElement = this.createLogElement(log);
            this.elements.logContainer.appendChild(logElement);
        });
    }

    // Reset filter and show all logs
    clearFilter() {
        this.updateLogDisplay();
    }

    // Search logs by message content
    searchLogs(searchTerm) {
        const filteredLogs = this.logs.filter(log => 
            log.message.toLowerCase().includes(searchTerm.toLowerCase())
        );
        
        this.displayFilteredLogs(filteredLogs);
    }

    // Export logs as text
    exportLogs() {
        const logText = this.logs.map(log => 
            `${log.timestamp.toISOString()} [${log.level.toUpperCase()}] ${log.message}`
        ).join('\n');

        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `printer-buddy-logs-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        
        this.addLog('info', 'Logs exported to file');
    }

    // Get log statistics
    getLogStats() {
        const stats = {
            total: this.logs.length,
            debug: 0,
            info: 0,
            warning: 0,
            error: 0
        };

        this.logs.forEach(log => {
            if (stats.hasOwnProperty(log.level)) {
                stats[log.level]++;
            }
        });

        return stats;
    }

    // Check for recent errors
    hasRecentErrors(minutesBack = 5) {
        const cutoffTime = new Date(Date.now() - minutesBack * 60 * 1000);
        
        return this.logs.some(log => 
            log.level === 'error' && log.timestamp > cutoffTime
        );
    }

    // Get recent logs
    getRecentLogs(count = 10) {
        return this.logs.slice(-count);
    }

    // Add system event log
    logSystemEvent(event, details = {}) {
        const message = `${event}: ${JSON.stringify(details)}`;
        this.addLog('info', message);
    }

    // Add error log with stack trace
    logError(error, context = '') {
        let message = context ? `${context}: ${error.message}` : error.message;
        
        if (error.stack) {
            message += `\nStack: ${error.stack}`;
        }
        
        this.addLog('error', message);
    }

    // Set auto-scroll behavior
    setAutoScroll(enabled) {
        this.autoScroll = enabled;
    }

    // Get current auto-scroll state
    isAutoScrollEnabled() {
        return this.autoScroll;
    }
}