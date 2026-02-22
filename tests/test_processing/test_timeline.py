"""Tests for timeline builder"""

import pytest
from decision_logger.processing.timeline import TimelineBuilder
from decision_logger.models.events import EventType


def test_merge_events(sample_config, sample_git_events, sample_shell_events):
    """Test merging events from multiple sources"""
    builder = TimelineBuilder(sample_config)

    timeline = builder.merge_events(sample_git_events, sample_shell_events)

    # Should have 3 events total
    assert len(timeline) == 3

    # Should be sorted chronologically
    assert timeline[0].timestamp < timeline[1].timestamp < timeline[2].timestamp

    # Should have correct types
    assert timeline[0].event_type == EventType.GIT_COMMIT
    assert timeline[1].event_type == EventType.SHELL_COMMAND
    assert timeline[2].event_type == EventType.GIT_COMMIT


def test_group_by_proximity(sample_config, sample_git_events):
    """Test grouping events by time proximity"""
    builder = TimelineBuilder(sample_config)

    # Events are 1 hour apart, so with 5-minute threshold should be in separate groups
    groups = builder.group_by_proximity(sample_git_events, time_threshold_minutes=5)

    assert len(groups) == 2
    assert len(groups[0]) == 1
    assert len(groups[1]) == 1

    # With 120-minute threshold should be in same group
    groups = builder.group_by_proximity(sample_git_events, time_threshold_minutes=120)

    assert len(groups) == 1
    assert len(groups[0]) == 2
