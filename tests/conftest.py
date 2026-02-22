"""Pytest configuration and fixtures"""

import pytest
from pathlib import Path
from datetime import datetime
from decision_logger.config import DecisionLogConfig
from decision_logger.models.events import GitCommitEvent, ShellCommandEvent


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample configuration for testing"""
    return DecisionLogConfig(
        output_dir=tmp_path / ".decision-log",
        base_branch="main",
        openai_model="gpt-4o-mini",
        temperature=0.0
    )


@pytest.fixture
def sample_git_events():
    """Create sample git commit events"""
    return [
        GitCommitEvent(
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            commit_hash="abc123",
            commit_message="Initial commit",
            author="Test Author",
            files_changed=["file1.py"],
            diff_summary="Added file1.py",
            raw_data={}
        ),
        GitCommitEvent(
            timestamp=datetime(2024, 1, 15, 11, 0, 0),
            commit_hash="def456",
            commit_message="Add feature",
            author="Test Author",
            files_changed=["file2.py"],
            diff_summary="Added file2.py",
            raw_data={}
        )
    ]


@pytest.fixture
def sample_shell_events():
    """Create sample shell command events"""
    return [
        ShellCommandEvent(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            command="npm install lodash",
            duration=5,
            raw_data={}
        )
    ]
