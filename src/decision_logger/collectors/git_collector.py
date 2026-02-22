"""Git collector for commits and file changes"""

import subprocess
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .base import BaseCollector
from ..models.events import GitCommitEvent, TimelineEvent


class GitCollector(BaseCollector):
    """Collects git commits and file changes"""

    def is_available(self) -> bool:
        """Check if we're in a git repository"""
        try:
            subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                check=True,
                text=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_current_branch(self) -> Optional[str]:
        """Get current git branch name"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def get_branch_point(self, current_branch: str, base_branch: str) -> Optional[str]:
        """Find merge-base between current and base branch"""
        try:
            result = subprocess.run(
                ['git', 'merge-base', current_branch, base_branch],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def collect(self,
                start_time: Optional[datetime] = None,
                end_time: Optional[datetime] = None) -> List[TimelineEvent]:
        """
        Collect git commits on current branch since diverging from base.
        Uses git log with range base_branch..current_branch
        """
        events = []

        # Get current branch
        current_branch = self.config.current_branch
        if not current_branch:
            current_branch = self.get_current_branch()

        if not current_branch:
            return []

        # Build git log command
        # Format: timestamp|hash|author|subject
        log_format = '%ct|%H|%an|%s'
        cmd = [
            'git', 'log',
            f'{self.config.base_branch}..{current_branch}',
            f'--format={log_format}',
            '--reverse'  # Chronological order (oldest first)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError:
            # If base branch doesn't exist or other error, try getting all commits
            try:
                cmd = [
                    'git', 'log',
                    f'--format={log_format}',
                    '--reverse'
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError:
                return []

        # Parse each commit
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split('|', 3)
            if len(parts) < 4:
                continue

            timestamp_str, commit_hash, author, message = parts
            timestamp = datetime.fromtimestamp(int(timestamp_str))

            # Filter by time range if specified
            if start_time and timestamp < start_time:
                continue
            if end_time and timestamp > end_time:
                continue

            # Get files changed in this commit
            files_changed = self._get_files_changed(commit_hash)

            # Get abbreviated diff
            diff_summary = self._get_diff_summary(commit_hash)

            event = GitCommitEvent(
                timestamp=timestamp,
                commit_hash=commit_hash,
                commit_message=message,
                author=author,
                files_changed=files_changed,
                diff_summary=diff_summary,
                raw_data={
                    'full_log_line': line,
                    'diff_stat': diff_summary
                }
            )

            events.append(event)

        return events

    def _get_files_changed(self, commit_hash: str) -> List[str]:
        """Get list of files changed in a commit"""
        try:
            result = subprocess.run(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
                capture_output=True,
                text=True,
                check=True
            )
            files = [f for f in result.stdout.strip().split('\n') if f]
            return files
        except subprocess.CalledProcessError:
            return []

    def _get_diff_summary(self, commit_hash: str) -> str:
        """Get abbreviated diff summary for a commit"""
        try:
            result = subprocess.run(
                ['git', 'show', '--stat', '--format=%b', commit_hash],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""
