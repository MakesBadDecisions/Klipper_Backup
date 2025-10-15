"""
Event Bus System for Printer Buddy Core

Provides pub/sub messaging between core modules and UI layers.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Event data structure"""
    type: str
    source: str
    data: Any
    timestamp: datetime
    priority: int = 0  # Higher = more urgent

class EventBus:
    """
    Event Bus for managing communication between modules
    
    Handles:
    - Module-to-module communication
    - Module-to-UI communication  
    - Emergency/priority events
    - Event persistence for debugging
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._priority_threshold = 5  # Emergency events
        
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event type: {event_type}")
        
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from event type: {event_type}")
            except ValueError:
                logger.warning(f"Callback not found for event type: {event_type}")
                
    def publish(self, event_type: str, source: str, data: Any, priority: int = 0):
        """Publish an event to all subscribers"""
        event = Event(
            type=event_type,
            source=source,
            data=data,
            timestamp=datetime.now(),
            priority=priority
        )
        
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
            
        # Log high priority events
        if priority >= self._priority_threshold:
            logger.critical(f"PRIORITY EVENT: {event_type} from {source} - {data}")
        else:
            logger.debug(f"Event: {event_type} from {source}")
            
        # Notify subscribers
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback for {event_type}: {e}")
                    
    def get_recent_events(self, count: int = 50) -> List[Event]:
        """Get recent events for debugging"""
        return self._event_history[-count:]
        
    def clear_history(self):
        """Clear event history"""
        self._event_history.clear()
        logger.info("Event history cleared")
        
    def get_event_stats(self) -> Dict[str, int]:
        """Get statistics about event types"""
        stats = {}
        for event in self._event_history:
            if event.type not in stats:
                stats[event.type] = 0
            stats[event.type] += 1
        return stats