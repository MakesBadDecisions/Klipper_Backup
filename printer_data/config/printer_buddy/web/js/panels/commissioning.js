/**
 * Commissioning Panel Manager - Clean Dynamic UI Implementation
 * 
 * Simple commissioning interface that fetches dynamic UI configs from Python tests.
 */

class CommissioningPanel {
    constructor(api, state) {
        this.api = api;
        this.state = state;
        this.elements = {};
        this.tests = [];
        this.selectedTest = null;
        this.currentRunId = null;
        this.pollInterval = null;
    }

    async initialize() {
        console.log('Initializing Commissioning Panel...');
        
        // Cache DOM elements
        this.elements = {
            testDropdown: document.getElementById('testDropdown'),
            selectedTestContainer: document.getElementById('selectedTestContainer'),
            selectedTestName: document.getElementById('selectedTestName')
        };
        
        // Debug: Check if all elements were found
        for (const [key, element] of Object.entries(this.elements)) {
            if (!element) {
                console.error(`Missing element: ${key}`);
                return;
            }
        }

        // Set up event listeners
        this.elements.testDropdown.addEventListener('change', () => this.onTestSelected());

        // Load available tests
        await this.loadTests();
        
        // Populate dropdown
        this.populateTestDropdown();
        
        console.log('Commissioning Panel initialized');
    }

    async loadTests() {
        try {
            const response = await this.api.getCommissioningTests();
            
            if (response.tests) {
                this.tests = response.tests;
                console.log('Loaded tests:', this.tests);
            } else {
                console.error('Failed to load tests from API');
                this.tests = [];
            }
        } catch (error) {
            console.error('Error loading tests from API:', error);
            this.tests = [];
        }
    }

    populateTestDropdown() {
        // Clear existing options
        this.elements.testDropdown.innerHTML = '<option value="">Select a test...</option>';
        
        // Add test options
        this.tests.forEach(test => {
            const option = document.createElement('option');
            option.value = test.id;
            option.textContent = test.name;
            this.elements.testDropdown.appendChild(option);
        });
    }

    async onTestSelected() {
        const testId = this.elements.testDropdown.value;
        
        if (!testId) {
            this.elements.selectedTestContainer.style.display = 'none';
            this.selectedTest = null;
            this.stopPolling();
            return;
        }

        // Find the selected test
        this.selectedTest = this.tests.find(test => test.id === testId);
        if (!this.selectedTest) {
            console.error('Selected test not found:', testId);
            return;
        }

        console.log(`Selected test: ${this.selectedTest.name} (${this.selectedTest.id})`);

        // Show the container and load UI config immediately (without starting test)
        this.elements.selectedTestContainer.style.display = 'block';
        this.elements.selectedTestName.textContent = this.selectedTest.name;
        
        // Load the test UI config (before starting the test)
        await this.loadTestUIConfig(); 
    }

    async startTest() {
        if (!this.selectedTest) return;

        try {
            console.log(`Starting test: ${this.selectedTest.id}`);
            
            const response = await this.api.startCommissioningTest(this.selectedTest.id);
            
            if (response.success) {
                this.currentRunId = response.run_id;
                console.log(`Test started successfully. Run ID: ${this.currentRunId}`);
                
                // Show the container and start polling for UI updates
                this.elements.selectedTestContainer.style.display = 'block';
                this.elements.selectedTestName.textContent = `${this.selectedTest.name} - Running`;
                
                this.startPolling();
            } else {
                console.error('Failed to start test:', response.error);
                this.elements.selectedTestName.textContent = `${this.selectedTest.name} - Failed to Start`;
            }
            
        } catch (error) {
            console.error('Error starting test:', error);
            this.elements.selectedTestName.textContent = `${this.selectedTest.name} - Error`;
        }
    }

    startPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
        
        // Poll for UI config updates every 2 seconds
        this.pollInterval = setInterval(() => {
            this.updateDynamicUI();
        }, 2000);
        
        // Also update immediately
        this.updateDynamicUI();
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    async loadTestUIConfig() {
        if (!this.selectedTest) return;

        try {
            console.log(`Loading UI config for test: ${this.selectedTest.id}`);
            
            // Fetch UI configuration from the Python test
            const response = await fetch(`/api/commissioning/ui-config/${this.selectedTest.id}`);
            
            if (response.ok) {
                const uiConfig = await response.json();
                console.log('Received UI config:', uiConfig);
                this.renderDynamicPanel(uiConfig);
            } else {
                console.log('No UI config available for this test');
                // Show default state
                this.renderLoadingState();
            }
        } catch (error) {
            console.error('Error fetching UI config:', error);
            this.renderErrorState('Failed to load test UI');
        }
    }

    async updateDynamicUI() {
        // This method is called during polling to update running test UI
        if (!this.selectedTest || !this.currentRunId) return;

        // For now, just reload the UI config
        await this.loadTestUIConfig();
    }

    renderDynamicPanel(uiConfig) {
        console.log('Rendering dynamic panel:', uiConfig);
        
        const container = this.elements.selectedTestContainer;
        
        if (uiConfig.type === 'none') {
            this.renderLoadingState();
            return;
        }

        // Clear existing content
        container.innerHTML = '';

        // Create the panel
        const panel = document.createElement('div');
        panel.className = 'test-panel';

        // Add title
        if (uiConfig.title) {
            const title = document.createElement('h3');
            title.textContent = uiConfig.title;
            title.className = 'test-panel-title';
            panel.appendChild(title);
        }

        // Handle new section-based format
        if (uiConfig.content && uiConfig.content.sections) {
            console.log('Rendering sections-based UI config');
            uiConfig.content.sections.forEach(section => {
                this.renderSection(panel, section, uiConfig.run_id);
            });
        } else {
            // Handle legacy simple format
            console.log('Rendering legacy UI config format');
            
            // Add message
            if (uiConfig.message) {
                const message = document.createElement('div');
                message.className = 'test-panel-message';
                message.innerHTML = uiConfig.message.replace(/\n/g, '<br>');
                panel.appendChild(message);
            }

            // Add buttons
            if (uiConfig.buttons && uiConfig.buttons.length > 0) {
                this.renderButtonSection(panel, { buttons: uiConfig.buttons }, uiConfig.run_id);
            }
        }

        container.appendChild(panel);
    }

    renderSection(panel, section, runId) {
        console.log('Rendering section:', section.type);
        
        switch (section.type) {
            case 'info':
                this.renderInfoSection(panel, section);
                break;
            case 'checklist':
                this.renderChecklistSection(panel, section);
                break;
            case 'buttons':
                this.renderButtonSection(panel, section, runId);
                break;
            default:
                console.warn('Unknown section type:', section.type);
        }
    }

    renderInfoSection(panel, section) {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'test-section test-section-info';
        
        if (section.title) {
            const title = document.createElement('h4');
            title.textContent = section.title;
            title.className = 'test-section-title';
            sectionDiv.appendChild(title);
        }
        
        if (section.content) {
            const content = document.createElement('div');
            content.className = 'test-section-content';
            content.innerHTML = section.content.replace(/\n/g, '<br>');
            sectionDiv.appendChild(content);
        }
        
        panel.appendChild(sectionDiv);
    }

    renderChecklistSection(panel, section) {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'test-section test-section-checklist';
        
        if (section.title) {
            const title = document.createElement('h4');
            title.textContent = section.title;
            title.className = 'test-section-title';
            sectionDiv.appendChild(title);
        }
        
        if (section.items && section.items.length > 0) {
            const list = document.createElement('ul');
            list.className = 'test-checklist';
            
            section.items.forEach(item => {
                const listItem = document.createElement('li');
                listItem.className = `test-checklist-item test-checklist-${item.status || 'pending'}`;
                
                const checkbox = document.createElement('span');
                checkbox.className = 'test-checklist-checkbox';
                checkbox.textContent = item.status === 'completed' ? '✓' : '○';
                
                const text = document.createElement('span');
                text.className = 'test-checklist-text';
                text.textContent = item.text;
                
                listItem.appendChild(checkbox);
                listItem.appendChild(text);
                list.appendChild(listItem);
            });
            
            sectionDiv.appendChild(list);
        }
        
        panel.appendChild(sectionDiv);
    }

    renderButtonSection(panel, section, runId) {
        if (section.buttons && section.buttons.length > 0) {
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'test-panel-buttons';

            section.buttons.forEach(button => {
                const btn = document.createElement('button');
                btn.textContent = button.text;
                btn.className = `btn btn-${button.style || 'secondary'}`;
                btn.onclick = () => this.handleButtonClick(button, runId);
                buttonContainer.appendChild(btn);
            });

            panel.appendChild(buttonContainer);
        }
    }

    renderLoadingState() {
        const container = this.elements.selectedTestContainer;
        container.innerHTML = '<div class="test-panel loading">Test is running...</div>';
    }

    renderErrorState(message) {
        const container = this.elements.selectedTestContainer;
        container.innerHTML = `<div class="test-panel error">Error: ${message}</div>`;
    }

    async handleButtonClick(button, runId) {
        console.log('Button clicked:', button);

        try {
            let response;
            
            if (button.action === 'acknowledge') {
                response = { response: 'acknowledged' };
            } else if (button.action === 'choice') {
                response = { response: button.value };
            } else {
                response = { response: button.id };
            }

            // Send response to API
            const result = await this.api.respondToCommissioningTest(runId, response.response);
            
            if (result.success) {
                console.log('Response sent successfully');
                // Continue polling to get next UI state
            } else {
                console.error('Failed to send response:', result.error);
            }

        } catch (error) {
            console.error('Error handling button click:', error);
        }
    }

    // Cleanup method
    destroy() {
        this.stopPolling();
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CommissioningPanel;
}

