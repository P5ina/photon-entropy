"""Base module class for all game modules."""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Optional, Any


class ModuleState(Enum):
    """Module states."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    SOLVED = "solved"
    FAILED = "failed"


class BaseModule(ABC):
    """Base class for all game modules."""

    def __init__(self, name: str, mock: bool = False):
        self.name = name
        self.mock = mock
        self._state = ModuleState.INACTIVE
        self._config: dict = {}

        # Callbacks
        self.on_solved: Optional[Callable[[], None]] = None
        self.on_strike: Optional[Callable[[str], None]] = None
        self.on_action: Optional[Callable[[str, Any], None]] = None

    @property
    def state(self) -> ModuleState:
        """Get module state."""
        return self._state

    @property
    def is_solved(self) -> bool:
        """Check if module is solved."""
        return self._state == ModuleState.SOLVED

    @property
    def is_active(self) -> bool:
        """Check if module is active."""
        return self._state == ModuleState.ACTIVE

    def configure(self, config: dict):
        """Configure module with game rules."""
        self._config = config

    @abstractmethod
    def setup(self):
        """Initialize hardware."""
        pass

    @abstractmethod
    def activate(self):
        """Activate the module for gameplay."""
        pass

    @abstractmethod
    def deactivate(self):
        """Deactivate the module."""
        pass

    @abstractmethod
    def reset(self):
        """Reset module to initial state."""
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up hardware resources."""
        pass

    def _report_action(self, action: str, data: Any = None):
        """Report an action to the game controller."""
        if self.on_action:
            self.on_action(action, data)

    def _report_solved(self):
        """Report module solved."""
        self._state = ModuleState.SOLVED
        if self.on_solved:
            self.on_solved()

    def _report_strike(self, reason: str):
        """Report a strike (mistake)."""
        if self.on_strike:
            self.on_strike(reason)
