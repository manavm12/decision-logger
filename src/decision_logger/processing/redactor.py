"""Secret redaction for timeline events"""

import re
from typing import List, Pattern, Tuple
from ..models.events import TimelineEvent, ShellCommandEvent, AIConversationEvent, GitCommitEvent


class SecretRedactor:
    """Redacts secrets and sensitive information from text"""

    # Comprehensive redaction patterns
    # Order matters! More specific patterns should come before generic ones
    PATTERNS: List[Tuple[str, Pattern, str]] = [
        # JWTs (check before generic token pattern)
        ("JWT", re.compile(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'), '[REDACTED_JWT]'),

        # GitHub tokens (check before generic token pattern)
        ("GitHub Token", re.compile(r'gh[pousr]_[A-Za-z0-9_]{36,}'), '[REDACTED_GITHUB_TOKEN]'),

        # AWS credentials
        ("AWS Access Key", re.compile(r'AKIA[0-9A-Z]{16}'), '[REDACTED_AWS_KEY]'),
        ("AWS Secret", re.compile(r'aws_secret_access_key\s*=\s*[^\s]+'), 'aws_secret_access_key=[REDACTED]'),

        # Bearer tokens
        ("Bearer Token", re.compile(r'Bearer\s+[A-Za-z0-9_\-\.]+'), 'Bearer [REDACTED_TOKEN]'),

        # Private keys
        ("Private Key", re.compile(r'-----BEGIN [A-Z]+ PRIVATE KEY-----.*?-----END [A-Z]+ PRIVATE KEY-----', re.DOTALL),
         '[REDACTED_PRIVATE_KEY]'),

        # Long base64 strings (likely encoded secrets)
        ("Base64 String", re.compile(r'\b[A-Za-z0-9+/]{64,}={0,2}\b'), '[REDACTED_BASE64]'),

        # API Keys and tokens (32+ chars)
        ("API Key", re.compile(r'\b[A-Za-z0-9_-]{32,}\b'), '[REDACTED_API_KEY]'),

        # URLs with credentials
        ("URL with auth", re.compile(r'(https?://)([^:@/\s]+):([^@/\s]+)@'), r'\1[REDACTED]:[REDACTED]@'),

        # Generic secrets in env vars or config (conservative - only match quoted strings or actual secret values)
        # Match assignment of quoted secret values or raw secrets (not code references like process.env.API_KEY)
        ("Secret/Password", re.compile(r'(secret|password|passwd|pwd|api_key|apikey|token)\s*[=:]\s*["\']([^"\']+)["\']', re.IGNORECASE),
         r'\1=[REDACTED]'),
    ]

    def __init__(self, custom_patterns: List[Tuple[str, str, str]] = None):
        """
        Initialize redactor with optional custom patterns.

        Args:
            custom_patterns: List of (name, regex_pattern, replacement) tuples
        """
        self.patterns = list(self.PATTERNS)

        if custom_patterns:
            for name, pattern_str, replacement in custom_patterns:
                self.patterns.append((name, re.compile(pattern_str), replacement))

    def redact(self, text: str) -> Tuple[str, List[str]]:
        """
        Redact secrets from text.

        Returns:
            Tuple of (redacted_text, list of redaction types applied)
        """
        if not text:
            return text, []

        redacted = text
        redactions_applied = []

        for name, pattern, replacement in self.patterns:
            if pattern.search(redacted):
                redacted = pattern.sub(replacement, redacted)
                if name not in redactions_applied:
                    redactions_applied.append(name)

        return redacted, redactions_applied

    def redact_event(self, event: TimelineEvent) -> TimelineEvent:
        """
        Redact an entire timeline event in-place.
        Handles different event types appropriately.

        Args:
            event: Timeline event to redact

        Returns:
            The same event object (modified in-place)
        """
        if isinstance(event, ShellCommandEvent):
            event.command, redactions = self.redact(event.command)
            if redactions:
                event.redacted = True

        elif isinstance(event, AIConversationEvent):
            event.content, redactions = self.redact(event.content)
            if redactions:
                event.redacted = True

        elif isinstance(event, GitCommitEvent):
            event.commit_message, redactions = self.redact(event.commit_message)
            event.diff_summary, diff_redactions = self.redact(event.diff_summary)
            if redactions or diff_redactions:
                event.redacted = True

        return event

    def redact_timeline(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """
        Redact all events in a timeline.

        Args:
            events: List of timeline events

        Returns:
            List of redacted events (modified in-place)
        """
        for event in events:
            self.redact_event(event)
        return events
