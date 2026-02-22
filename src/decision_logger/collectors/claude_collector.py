"""Claude Code conversation log collector"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .base import BaseCollector
from ..models.events import AIConversationEvent, TimelineEvent


class ClaudeCollector(BaseCollector):
    """Collects Claude Code conversation logs"""

    def is_available(self) -> bool:
        """Check if Claude logs directory exists"""
        logs_dir = self._get_logs_dir()
        return logs_dir is not None and logs_dir.exists()

    def _get_logs_dir(self) -> Optional[Path]:
        """Get Claude logs directory from config or auto-detect"""
        # Try config first
        if self.config.claude_logs_dir:
            return self.config.claude_logs_dir

        # Use config method for auto-detection
        return self.config.get_claude_logs_dir()

    def _find_session_files(self, logs_dir: Path) -> List[Path]:
        """Find all .jsonl session files in logs directory"""
        # Main session files are at root level
        session_files = list(logs_dir.glob('*.jsonl'))
        return session_files

    def _extract_content(self, message_content) -> str:
        """Extract text content from message content blocks"""
        if isinstance(message_content, str):
            return message_content

        if isinstance(message_content, list):
            text_parts = []
            for block in message_content:
                if isinstance(block, dict):
                    if block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                    elif block.get('type') == 'tool_use':
                        # Include tool use information
                        tool_name = block.get('name', 'unknown')
                        text_parts.append(f"[Tool: {tool_name}]")
                elif isinstance(block, str):
                    text_parts.append(block)
            return ' '.join(text_parts)

        return str(message_content)

    def collect(self,
                start_time: Optional[datetime] = None,
                end_time: Optional[datetime] = None) -> List[TimelineEvent]:
        """
        Collect Claude Code conversation events.

        Strategy:
        1. Find all session .jsonl files
        2. Parse each line as JSON
        3. Filter for user/assistant messages
        4. Extract timestamp, content, and metadata
        """
        logs_dir = self._get_logs_dir()
        if not logs_dir:
            return []

        events = []
        session_files = self._find_session_files(logs_dir)

        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)

                            # Parse timestamp
                            timestamp_str = entry.get('timestamp')
                            if not timestamp_str:
                                continue

                            # Convert ISO 8601 to datetime
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace('Z', '+00:00')
                            )

                            # Filter by time range
                            if start_time and timestamp < start_time:
                                continue
                            if end_time and timestamp > end_time:
                                continue

                            # Extract conversation events
                            entry_type = entry.get('type')

                            if entry_type in ['user', 'assistant']:
                                # Skip meta messages
                                if entry.get('isMeta', False):
                                    continue

                                message = entry.get('message', {})
                                content = self._extract_content(message.get('content', ''))

                                event = AIConversationEvent(
                                    timestamp=timestamp,
                                    role=entry_type,
                                    content=content,
                                    message_uuid=entry.get('uuid', ''),
                                    parent_uuid=entry.get('parentUuid'),
                                    session_id=entry.get('sessionId', ''),
                                    git_branch=entry.get('gitBranch', ''),
                                    working_directory=entry.get('cwd', ''),
                                    raw_data=entry
                                )
                                events.append(event)

                        except json.JSONDecodeError:
                            # Skip malformed lines
                            continue
                        except Exception:
                            # Skip lines that cause other errors
                            continue
            except Exception:
                # Skip files that can't be read
                continue

        # Sort by timestamp
        return sorted(events, key=lambda e: e.timestamp)
