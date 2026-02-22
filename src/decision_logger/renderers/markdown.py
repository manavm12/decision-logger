"""Markdown renderer for decision logs"""

from typing import List, Dict, Any
from datetime import datetime
from ..models.events import TimelineEvent, EventType


class MarkdownRenderer:
    """Renders decision log as markdown"""

    def render_decision_log(self,
                           decision_log: Dict[str, Any],
                           timeline: List[TimelineEvent],
                           branch_name: str,
                           generated_at: datetime) -> str:
        """
        Render complete decision log as markdown.

        Structure:
        1. Header with metadata
        2. Problem statement
        3. Attempts and iterations
        4. Final solution
        5. Rationale
        6. Risks and follow-ups
        7. Appendix: Timeline events

        Args:
            decision_log: Inferred decision log dictionary
            timeline: List of timeline events
            branch_name: Name of the branch
            generated_at: Timestamp when log was generated

        Returns:
            Markdown formatted string
        """
        md = []

        # Header
        md.append(f"# Decision Log: {branch_name}\n")
        md.append(f"\n**Generated:** {generated_at.isoformat()}\n")
        md.append(f"**Branch:** `{branch_name}`\n")
        md.append("\n---\n")

        # Problem Statement
        md.append("## Problem Statement\n\n")
        md.append(decision_log['problem_statement'])
        md.append("\n\n")

        if decision_log.get('initial_context'):
            md.append("### Initial Context\n\n")
            md.append(decision_log['initial_context'])
            md.append("\n\n")

        # Attempts
        if decision_log.get('attempts'):
            md.append("## Attempts and Iterations\n\n")
            for i, attempt in enumerate(decision_log['attempts'], 1):
                md.append(f"### Attempt {i}: {attempt['description']}\n\n")
                md.append(f"**Outcome:** {attempt['outcome']}\n\n")

                if attempt.get('learnings'):
                    md.append(f"**Learnings:** {attempt['learnings']}\n\n")

                md.append("**Evidence:**\n")
                for evidence in attempt['evidence']:
                    md.append(f"- {evidence}\n")
                md.append("\n")

        # Final Solution
        md.append("## Final Solution\n\n")
        md.append(decision_log['final_solution']['description'])
        md.append("\n\n")

        if decision_log['final_solution'].get('how_it_works'):
            md.append("### How It Works\n\n")
            md.append(decision_log['final_solution']['how_it_works'])
            md.append("\n\n")

        md.append("**Evidence:**\n")
        for evidence in decision_log['final_solution']['evidence']:
            md.append(f"- {evidence}\n")
        md.append("\n")

        # Rationale
        md.append("## Rationale and Tradeoffs\n\n")
        md.append(decision_log['rationale_and_tradeoffs']['why_chosen'])
        md.append("\n\n")

        if decision_log['rationale_and_tradeoffs'].get('alternatives_considered'):
            md.append("### Alternatives Considered\n\n")
            for alt in decision_log['rationale_and_tradeoffs']['alternatives_considered']:
                md.append(f"- {alt}\n")
            md.append("\n")

        if decision_log['rationale_and_tradeoffs'].get('tradeoffs'):
            md.append("### Tradeoffs\n\n")
            for tradeoff in decision_log['rationale_and_tradeoffs']['tradeoffs']:
                md.append(f"- **{tradeoff['aspect']}:** {tradeoff['decision']}\n")
            md.append("\n")

        # Risks and Follow-ups
        risks_section = decision_log.get('risks_and_followups', {})
        if risks_section:
            md.append("## Risks and Follow-ups\n\n")

            if risks_section.get('risks'):
                md.append("### Risks\n\n")
                for risk in risks_section['risks']:
                    md.append(f"- {risk}\n")
                md.append("\n")

            if risks_section.get('followups'):
                md.append("### Follow-up Work\n\n")
                for followup in risks_section['followups']:
                    md.append(f"- {followup}\n")
                md.append("\n")

            if risks_section.get('technical_debt'):
                md.append("### Technical Debt\n\n")
                for debt in risks_section['technical_debt']:
                    md.append(f"- {debt}\n")
                md.append("\n")

        # Appendix: Timeline
        md.append("---\n\n")
        md.append("## Appendix: Full Timeline\n\n")
        md.append(self._render_timeline(timeline))

        return "".join(md)

    def _render_timeline(self, events: List[TimelineEvent]) -> str:
        """Render timeline events as markdown list"""
        lines = []

        for event in events:
            if not event.timestamp:
                continue

            timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")

            if event.event_type == EventType.GIT_COMMIT:
                commit_hash = event.commit_hash[:7] if hasattr(event, 'commit_hash') else 'unknown'
                commit_msg = event.commit_message if hasattr(event, 'commit_message') else ''
                lines.append(f"- **{timestamp}** [commit `{commit_hash}`] {commit_msg}\n")

            elif event.event_type == EventType.SHELL_COMMAND:
                cmd = event.command if hasattr(event, 'command') else ''
                # Truncate long commands
                if len(cmd) > 100:
                    cmd = cmd[:100] + "..."
                lines.append(f"- **{timestamp}** [shell] `{cmd}`\n")

            elif event.event_type == EventType.AI_CONVERSATION:
                role = event.role if hasattr(event, 'role') else 'unknown'
                content = event.content if hasattr(event, 'content') else ''
                # Truncate and clean content
                content = content[:150].replace('\n', ' ')
                if len(content) >= 150:
                    content += "..."
                lines.append(f"- **{timestamp}** [AI {role}] {content}\n")

        return "".join(lines)
