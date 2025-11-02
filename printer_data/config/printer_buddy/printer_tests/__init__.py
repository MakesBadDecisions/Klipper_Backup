"""
Printer Tests Module

This module contains individual test classes for commissioning and validation
of printer components. Each test is a Python class that can be loaded and
executed by the printer_buddy manager.

Test Structure:
- Each test inherits from BaseTest
- Tests are discovered automatically by the manager
- Tests can have dependencies on other tests
- Tests report progress and results via callbacks
"""

from .base_test import BaseTest
from .safety_validation import SafetyValidationTest

