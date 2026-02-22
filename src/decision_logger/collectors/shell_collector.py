"""Shell history collector"""

import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .base import BaseCollector
from ..models.events import ShellCommandEvent, TimelineEvent


class ShellCollector(BaseCollector):
    """Collects shell command history"""

    # Regex for extended history format: : <timestamp>:<duration>;<command>
    EXTENDED_HISTORY_PATTERN = re.compile(r'^: (\d+):(\d+);(.*)$')

    def is_available(self) -> bool:
        """Check if shell history file exists"""
        history_path = self._get_history_path()
        return history_path is not None and history_path.exists()

    def _get_history_path(self) -> Optional[Path]:
        """Get shell history path from config or auto-detect"""
        # Try config first
        if self.config.shell_history_path:
            return self.config.shell_history_path

        # Use config method for auto-detection
        return self.config.get_shell_history_path()

    def _is_extended_history_enabled(self, history_path: Path) -> bool:
        """Check if first few lines have extended history format"""
        try:
            with open(history_path, 'r', errors='ignore') as f:
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    if self.EXTENDED_HISTORY_PATTERN.match(line):
                        return True
        except Exception:
            pass
        return False

    def collect(self,
                start_time: Optional[datetime] = None,
                end_time: Optional[datetime] = None) -> List[TimelineEvent]:
        """
        Collect shell commands from history.
        If extended history is not enabled, returns empty list with warning.
        """
        history_path = self._get_history_path()
        if not history_path:
            return []

        events = []
        has_extended_history = self._is_extended_history_enabled(history_path)

        if not has_extended_history:
            # Can't collect without timestamps
            return []

        try:
            with open(history_path, 'r', errors='ignore') as f:
                for line in f:
                    line = line.rstrip('\n')

                    match = self.EXTENDED_HISTORY_PATTERN.match(line)
                    if match:
                        timestamp_str, duration_str, command = match.groups()
                        timestamp = datetime.fromtimestamp(int(timestamp_str))
                        duration = int(duration_str)

                        # Filter by time range if specified
                        if start_time and timestamp < start_time:
                            continue
                        if end_time and timestamp > end_time:
                            continue

                        event = ShellCommandEvent(
                            timestamp=timestamp,
                            command=command,
                            duration=duration,
                            raw_data={'line': line}
                        )
                        events.append(event)
        except Exception:
            # If we can't read the file, return empty list
            return []

        return events
