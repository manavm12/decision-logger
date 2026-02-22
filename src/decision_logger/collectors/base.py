"""Base collector interface"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from ..models.events import TimelineEvent


class BaseCollector(ABC):
    """Abstract base class for all signal collectors"""

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def collect(self,
                start_time: Optional[datetime] = None,
                end_time: Optional[datetime] = None) -> List[TimelineEvent]:
        """
        Collect events within the specified time range.
        If start_time is None, collect from beginning of current branch.
        If end_time is None, collect until now.

        Returns:
            List of TimelineEvent objects
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this collector can run (data source exists)"""
        pass
