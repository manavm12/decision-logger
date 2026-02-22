"""Prompt templates for OpenAI inference"""


def get_decision_log_prompt(timeline_context: str, branch_name: str) -> str:
    """
    Generate prompt for decision log inference.

    Key principles:
    - Provide clear instructions
    - Ask for evidence citations
    - Request specific format
    - Minimize hallucination risk

    Args:
        timeline_context: Formatted timeline text
        branch_name: Name of the branch being analyzed

    Returns:
        Prompt string for OpenAI
    """
    return f"""Analyze the following development timeline for branch "{branch_name}" and extract the key technical decisions made.

TIMELINE DATA:
{timeline_context}

Your task is to infer the following, based ONLY on evidence in the timeline above:

1. PROBLEM STATEMENT
   - What problem or feature was being addressed?
   - What were the initial requirements or constraints?

2. ATTEMPTS AND ITERATIONS
   - What different approaches were tried? (cite specific commits, commands, or conversations)
   - What failed or was rejected? Why?
   - What was learned from each attempt?

3. FINAL SOLUTION
   - What approach was ultimately chosen?
   - How does it work (high level)?

4. RATIONALE AND TRADEOFFS
   - Why was this solution chosen over alternatives?
   - What tradeoffs were made?
   - What was prioritized (performance, simplicity, maintainability, etc.)?

5. RISKS AND FOLLOW-UPS
   - What potential issues or edge cases were identified?
   - What follow-up work is needed?
   - What technical debt was introduced?

CRITICAL INSTRUCTIONS:
- Base ALL inferences on explicit evidence from the timeline
- Cite specific events (commits, commands, conversations) as evidence
- Use format like "[commit abc123]", "[shell: npm test]", "[conversation: discussed X]"
- If information is not available in timeline, say "Not evident from timeline"
- DO NOT make up or assume information not present in the data
- Focus on technical decisions, not trivial changes
- Be concise but precise

Return your analysis as structured JSON following the provided schema."""


def get_summary_prompt(decision_log_json: str) -> str:
    """
    Generate prompt for PR summary.

    Args:
        decision_log_json: JSON string of decision log

    Returns:
        Prompt string for OpenAI
    """
    return f"""Based on this decision log, generate a concise PR summary (2-3 paragraphs max):

{decision_log_json}

The summary should:
- Explain what was changed and why
- Highlight key decisions and tradeoffs
- Note any important follow-ups or risks
- Be written for a code reviewer who needs context

Format as markdown with sections:
## Summary
## Key Changes
## Testing Notes"""
