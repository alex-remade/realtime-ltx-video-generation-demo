from abc import ABC, abstractmethod
from typing import Dict, Any


class Monitorable(ABC):
    """Simple interface for components that can be monitored"""
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return component status for monitoring"""
        pass
