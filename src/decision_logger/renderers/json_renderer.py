"""JSON renderer for decision logs"""

import json
from typing import List, Dict, Any
from datetime import datetime
from ..models.events import TimelineEvent


class JSONRenderer:
    """Renders decision log as JSON"""

    def render(self,
               decision_log: Dict[str, Any],
               timeline: List[TimelineEvent],
               branch_name: str,
               generated_at: datetime) -> str:
        """
        Render complete decision log as JSON.

        Args:
            decision_log: Inferred decision log dictionary
            timeline: List of timeline events
            branch_name: Name of the branch
            generated_at: Timestamp when log was generated

        Returns:
            JSON formatted string
        """
        output = {
            "metadata": {
                "branch": branch_name,
                "generated_at": generated_at.isoformat(),
                "event_count": len(timeline)
            },
            "decision_log": decision_log,
            "timeline": [event.to_dict() for event in timeline]
        }

        return json.dumps(output, indent=2)
