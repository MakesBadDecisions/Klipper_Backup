"""
Base Test Class

All printer tests inherit from this base class which provides:
- Common test lifecycle methods
- Progress reporting
- Result tracking
- Configuration access
- Printer communication interface
"""

import time
import logging
import asyncio
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable

class TestStatus:
    """Test status constants"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    WAITING_USER = "waiting_user"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

class UserPromptType:
    """User prompt types"""
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_INPUT = "text_input"
    CONFIRMATION = "confirmation"
    INSTRUCTION = "instruction"

class BaseTest(ABC):
    """Base class for all printer tests"""
    
    def __init__(self, printer_manager, config_parser, progress_callback=None, status_callback=None, user_prompt_callback=None):
        self.printer_manager = printer_manager
        self.config_parser = config_parser
        self.progress_callback = progress_callback or self._default_progress_callback
        self.status_callback = status_callback or self._default_status_callback
        self.user_prompt_callback = user_prompt_callback or self._default_user_prompt_callback
        
        self.status = TestStatus.NOT_STARTED
        self.progress = 0
        self.error_message = None
        self.results = {}
        self.start_time = None
        self.end_time = None
        
        # User interaction state
        self.pending_prompt = None
        self.user_response_event = threading.Event()
        self.user_response_value = None
        
        self.logger = logging.getLogger(f"printer_tests.{self.__class__.__name__}")
    
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Return human-readable test name"""
        pass
    
    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        """Return test description"""
        pass
    
    @classmethod
    def get_dependencies(cls) -> list:
        """Return list of test IDs that must pass before this test can run"""
        return []
    
    @classmethod
    def is_applicable(cls, config_parser) -> bool:
        """Return True if this test is applicable to the current printer config"""
        return True
    
    def get_ui_config(self) -> dict:
        """Return UI configuration for this test's panel
        
        This method should return a dictionary describing the UI elements
        to display for this test. Override in subclasses to customize.
        """
        return {
            'type': 'default_panel',
            'title': self.get_name(),
            'content': {
                'sections': [
                    {
                        'type': 'info',
                        'title': 'Test Information',
                        'content': self.get_description()
                    },
                    {
                        'type': 'buttons',
                        'buttons': [
                            {'id': 'start_test', 'text': 'Start Test', 'style': 'primary'}
                        ]
                    }
                ]
            }
        }
    
    def _default_progress_callback(self, progress: int, message: str = ""):
        """Default progress callback"""
        self.logger.info(f"Progress: {progress}% - {message}")
    
    def _default_status_callback(self, status: str, message: str = ""):
        """Default status callback"""
        self.logger.info(f"Status: {status} - {message}")
    
    def _default_user_prompt_callback(self, prompt_data: Dict[str, Any]) -> None:
        """Default user prompt callback - just logs the prompt"""
        self.logger.info(f"User prompt: {prompt_data.get('message', 'No message')}")
        # In a real implementation, this would send the prompt to the UI
        # For now, just auto-respond with a default
        if prompt_data.get('type') == UserPromptType.YES_NO:
            # Auto-respond with 'yes' for testing
            self.submit_user_response({'response': 'yes'})
        elif prompt_data.get('type') == UserPromptType.CONFIRMATION:
            self.submit_user_response({'response': 'confirmed'})
    
    def update_progress(self, progress: int, message: str = ""):
        """Update test progress"""
        self.progress = max(0, min(100, progress))
        self.progress_callback(self.progress, message)
    
    def update_status(self, status: str, message: str = ""):
        """Update test status"""
        self.status = status
        self.status_callback(status, message)
    
    def set_error(self, error_message: str):
        """Set test error state"""
        self.error_message = error_message
        self.status = TestStatus.ERROR
        self.update_status(TestStatus.ERROR, error_message)
        self.logger.error(f"Test error: {error_message}")
    
    async def prompt_user(self, message: str, prompt_type: str, options: Optional[Dict] = None, timeout: Optional[int] = None) -> Any:
        """Prompt user for input and wait for response"""
        prompt_data = {
            'type': prompt_type,
            'message': message,
            'options': options or {},
            'timeout': timeout,
            'test_name': self.get_name()
        }
        
        # Store the prompt and prepare for response
        self.pending_prompt = prompt_data
        self.user_response_event.clear()  # Reset the event
        self.user_response_value = None   # Clear previous response
        
        # Update status to waiting for user
        self.status = TestStatus.WAITING_USER
        self.update_status(TestStatus.WAITING_USER, f"Waiting for user: {message}")
        
        # Send prompt to UI via callback
        self.user_prompt_callback(prompt_data)
        
        # Wait for user response (with timeout if specified)
        try:
            # Use a loop to wait for the event with timeout support
            if timeout:
                if not self.user_response_event.wait(timeout=timeout):
                    self.status = TestStatus.FAILED
                    self.update_status(TestStatus.FAILED, f"User response timeout after {timeout} seconds")
                    raise Exception(f"User response timeout after {timeout} seconds")
            else:
                self.user_response_event.wait()
            
            # Get the response value
            response = self.user_response_value
            
            # Resume running status
            self.status = TestStatus.RUNNING
            self.update_status(TestStatus.RUNNING, "Continuing test...")
            
            return response
            
        finally:
            self.pending_prompt = None
    
    async def _handle_user_response(self, response_data: Dict[str, Any]):
        """Handle user response from UI"""
        if self.pending_prompt:  # Check if we have a pending prompt
            self.user_response_value = response_data.get('response')
            self.user_response_event.set()  # Signal that response is ready
    
    async def prompt_yes_no(self, message: str, timeout: Optional[int] = None) -> bool:
        """Prompt user for yes/no response"""
        response = await self.prompt_user(message, UserPromptType.YES_NO, timeout=timeout)
        if isinstance(response, bool):
            return response
        elif isinstance(response, str):
            return response.lower() in ['yes', 'y', 'true', '1']
        else:
            return bool(response)
    
    async def prompt_confirmation(self, message: str, button_text: str = "Continue", timeout: Optional[int] = None) -> bool:
        """Prompt user to confirm an action"""
        options = {'button_text': button_text}
        response = await self.prompt_user(message, UserPromptType.CONFIRMATION, options=options, timeout=timeout)
        return response == 'confirmed'
    
    async def prompt_multiple_choice(self, message: str, choices: list, timeout: Optional[int] = None) -> str:
        """Prompt user to select from multiple choices"""
        options = {'choices': choices}
        response = await self.prompt_user(message, UserPromptType.MULTIPLE_CHOICE, options=options, timeout=timeout)
        return response
    
    async def show_instruction(self, message: str, button_text: str = "Done") -> bool:
        """Show instruction to user and wait for acknowledgment"""
        options = {'button_text': button_text}
        response = await self.prompt_user(message, UserPromptType.INSTRUCTION, options=options)
        return response == 'acknowledged'
    
    async def show_instruction(self, message: str, acknowledge_text: str = "Continue") -> bool:
        """Show an instruction to the user and wait for acknowledgment"""
        response = await self.prompt_user(message, UserPromptType.INSTRUCTION, options={'acknowledge': acknowledge_text})
        return response == 'acknowledged'
    
    async def prompt_multiple_choice(self, message: str, choices: Dict[str, str], timeout: Optional[int] = None) -> str:
        """Prompt user with multiple choice options"""
        response = await self.prompt_user(message, UserPromptType.MULTIPLE_CHOICE, options=choices, timeout=timeout)
        return response
    
    async def run(self) -> Dict[str, Any]:
        """Run the test and return results"""
        self.start_time = time.time()
        self.status = TestStatus.RUNNING
        self.progress = 0
        self.error_message = None
        self.results = {}
        
        try:
            self.update_status(TestStatus.RUNNING, "Starting test...")
            self.update_progress(0, "Initializing...")
            
            # Run the actual test
            await self._run_test()
            
            if self.status != TestStatus.FAILED and self.status != TestStatus.ERROR:
                self.status = TestStatus.PASSED
                self.update_status(TestStatus.PASSED, "Test completed successfully")
                self.update_progress(100, "Complete")
            
        except Exception as e:
            self.set_error(f"Unexpected error: {str(e)}")
            self.logger.exception("Test failed with exception")
        
        finally:
            self.end_time = time.time()
        
        return self.get_results()
    
    @abstractmethod
    async def _run_test(self):
        """Implement the actual test logic"""
        pass
    
    def get_results(self) -> Dict[str, Any]:
        """Get test results"""
        duration = None
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
        
        return {
            'test_name': self.get_name(),
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'duration': duration,
            'results': self.results.copy(),
            'start_time': self.start_time,
            'end_time': self.end_time
        }
    
    def submit_user_response(self, response_data: Dict[str, Any]):
        """Submit user response from API/UI (synchronous method)"""
        if self.pending_prompt:  # Check if we have a pending prompt
            response = response_data.get('response')
            self.user_response_value = response
            self.user_response_event.set()  # Signal that response is ready
        else:
            self.logger.warning("Received user response but no prompt is pending")
    
    def get_pending_prompt(self) -> Optional[Dict[str, Any]]:
        """Get current pending user prompt"""
        return self.pending_prompt
    
    async def cleanup(self):
        """Cleanup after test completion (override if needed)"""
        # Cancel any pending user prompts
        if self.pending_prompt:
            self.user_response_value = None  # Clear any response
            self.user_response_event.set()   # Wake up any waiting threads
        pass