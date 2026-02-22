"""OpenAI structured output schema for decision log"""

# OpenAI structured output schema for decision log
DECISION_LOG_SCHEMA = {
    "type": "object",
    "properties": {
        "problem_statement": {
            "type": "string",
            "description": "What problem or feature was being addressed"
        },
        "initial_context": {
            "type": "string",
            "description": "Initial requirements, constraints, or background"
        },
        "attempts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "outcome": {
                        "type": "string",
                        "enum": ["failed", "rejected", "partial", "successful"]
                    },
                    "evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Citations to timeline events"
                    },
                    "learnings": {"type": "string"}
                },
                "required": ["description", "outcome", "evidence"],
                "additionalProperties": False
            }
        },
        "final_solution": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "how_it_works": {"type": "string"},
                "evidence": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["description", "evidence"],
            "additionalProperties": False
        },
        "rationale_and_tradeoffs": {
            "type": "object",
            "properties": {
                "why_chosen": {"type": "string"},
                "alternatives_considered": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "tradeoffs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "aspect": {"type": "string"},
                            "decision": {"type": "string"}
                        },
                        "required": ["aspect", "decision"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["why_chosen"],
            "additionalProperties": False
        },
        "risks_and_followups": {
            "type": "object",
            "properties": {
                "risks": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "followups": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "technical_debt": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": [],
            "additionalProperties": False
        }
    },
    "required": [
        "problem_statement",
        "attempts",
        "final_solution",
        "rationale_and_tradeoffs"
    ],
    "additionalProperties": False
}
