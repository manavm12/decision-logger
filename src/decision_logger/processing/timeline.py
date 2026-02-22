"""Timeline correlation and building"""

from typing import List
from datetime import datetime
from ..models.events import TimelineEvent


class TimelineBuilder:
    """Builds chronological timeline from multiple signal sources"""

    def __init__(self, config):
        self.config = config

    def merge_events(self, *event_lists: List[List[TimelineEvent]]) -> List[TimelineEvent]:
        """
        Merge multiple event lists into single chronological timeline.

        Algorithm:
        1. Flatten all event lists
        2. Sort by timestamp
        3. Handle events with missing timestamps (put at end with warning)
        4. Return sorted unified timeline
        """
        all_events = []
        events_without_timestamp = []

        for event_list in event_lists:
            for event in event_list:
                if event.timestamp:
                    all_events.append(event)
                else:
                    events_without_timestamp.append(event)

        # Sort by timestamp — normalize tz-aware to naive UTC so they compare cleanly
        def _sort_key(e):
            ts = e.timestamp
            if ts.tzinfo is not None:
                ts = ts.replace(tzinfo=None)
            return ts

        sorted_events = sorted(all_events, key=_sort_key)

        # Add events without timestamps at the end
        sorted_events.extend(events_without_timestamp)

        return sorted_events

    def group_by_proximity(self,
                          events: List[TimelineEvent],
                          time_threshold_minutes: int = 5) -> List[List[TimelineEvent]]:
        """
        Group events that are close in time together.
        Useful for identifying related activities.

        Args:
            events: List of timeline events (should be sorted)
            time_threshold_minutes: Maximum time gap between events in same group

        Returns:
            List of event groups
        """
        if not events:
            return []

        groups = []
        current_group = [events[0]]

        for event in events[1:]:
            if event.timestamp and current_group[-1].timestamp:
                time_diff = (event.timestamp - current_group[-1].timestamp).total_seconds() / 60

                if time_diff <= time_threshold_minutes:
                    current_group.append(event)
                else:
                    groups.append(current_group)
                    current_group = [event]
            else:
                current_group.append(event)

        groups.append(current_group)
        return groups

    def filter_by_time_range(self,
                            events: List[TimelineEvent],
                            start_time: datetime = None,
                            end_time: datetime = None) -> List[TimelineEvent]:
        """
        Filter events to only those within specified time range.

        Args:
            events: List of timeline events
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)

        Returns:
            Filtered list of events
        """
        filtered = []

        for event in events:
            if not event.timestamp:
                continue

            if start_time and event.timestamp < start_time:
                continue

            if end_time and event.timestamp > end_time:
                continue

            filtered.append(event)

        return filtered
