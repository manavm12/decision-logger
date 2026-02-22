"""Timeline event data models"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class EventType(Enum):
    """Type of timeline event"""
    GIT_COMMIT = "git_commit"
    FILE_CHANGE = "file_change"
    SHELL_COMMAND = "shell_command"
    AI_CONVERSATION = "ai_conversation"
    AI_TOOL_CALL = "ai_tool_call"


@dataclass
class TimelineEvent:
    """Base class for all timeline events"""
    timestamp: Optional[datetime] = None
    event_type: Optional[EventType] = None
    source: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    redacted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary for JSON output"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'source': self.source,
            'redacted': self.redacted,
            **self._specific_data()
        }

    def _specific_data(self) -> Dict[str, Any]:
        """Override in subclasses to add type-specific data"""
        return {}


@dataclass
class GitCommitEvent(TimelineEvent):
    """Git commit event"""
    commit_hash: str = ""
    commit_message: str = ""
    author: str = ""
    files_changed: List[str] = field(default_factory=list)
    diff_summary: str = ""

    def __post_init__(self):
        if not self.event_type:
            self.event_type = EventType.GIT_COMMIT
        if not self.source:
            self.source = "git"

    def _specific_data(self) -> Dict[str, Any]:
        return {
            'commit_hash': self.commit_hash,
            'commit_message': self.commit_message,
            'author': self.author,
            'files_changed': self.files_changed,
            'diff_summary': self.diff_summary
        }


@dataclass
class ShellCommandEvent(TimelineEvent):
    """Shell command event"""
    command: str = ""
    duration: int = 0  # seconds
    working_directory: Optional[str] = None
    exit_code: Optional[int] = None

    def __post_init__(self):
        if not self.event_type:
            self.event_type = EventType.SHELL_COMMAND
        if not self.source:
            self.source = "shell"

    def _specific_data(self) -> Dict[str, Any]:
        return {
            'command': self.command,
            'duration': self.duration,
            'working_directory': self.working_directory,
            'exit_code': self.exit_code
        }


@dataclass
class AIToolCallEvent(TimelineEvent):
    """AI tool call event"""
    tool_name: str = ""
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_output: Optional[str] = None
    parent_message_uuid: str = ""

    def __post_init__(self):
        if not self.event_type:
            self.event_type = EventType.AI_TOOL_CALL
        if not self.source:
            self.source = "claude"

    def _specific_data(self) -> Dict[str, Any]:
        return {
            'tool_name': self.tool_name,
            'tool_input': self.tool_input,
            'tool_output': self.tool_output,
            'parent_message_uuid': self.parent_message_uuid
        }


@dataclass
class AIConversationEvent(TimelineEvent):
    """AI conversation event (user or assistant message)"""
    role: str = ""  # "user" or "assistant"
    content: str = ""
    message_uuid: str = ""
    parent_uuid: Optional[str] = None
    session_id: str = ""
    git_branch: str = ""
    working_directory: str = ""
    tool_calls: List[AIToolCallEvent] = field(default_factory=list)

    def __post_init__(self):
        if not self.event_type:
            self.event_type = EventType.AI_CONVERSATION
        if not self.source:
            self.source = "claude"

    def _specific_data(self) -> Dict[str, Any]:
        return {
            'role': self.role,
            'content': self.content,
            'message_uuid': self.message_uuid,
            'parent_uuid': self.parent_uuid,
            'session_id': self.session_id,
            'git_branch': self.git_branch,
            'working_directory': self.working_directory,
            'tool_calls': [tc.to_dict() for tc in self.tool_calls]
        }
