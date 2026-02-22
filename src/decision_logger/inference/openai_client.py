"""OpenAI client for decision log inference"""

import json
from typing import Dict, Any
from openai import OpenAI
from .prompts import get_decision_log_prompt, get_summary_prompt
from .schema import DECISION_LOG_SCHEMA


class InferenceError(Exception):
    """Exception raised when inference fails"""
    pass


class DecisionLogInference:
    """OpenAI client for decision log inference"""

    def __init__(self, config):
        self.config = config
        api_key = config.get_openai_api_key()

        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or add to config file."
            )

        self.client = OpenAI(api_key=api_key)

    def infer_decision_log(self,
                          timeline_context: str,
                          branch_name: str) -> Dict[str, Any]:
        """
        Use OpenAI to infer decision log from timeline.

        Args:
            timeline_context: Formatted timeline text
            branch_name: Name of branch being analyzed

        Returns:
            Structured JSON with:
            - problem_statement
            - attempts (list of {description, outcome, evidence})
            - final_solution
            - tradeoffs
            - risks_and_followups

        Raises:
            InferenceError: If OpenAI API call fails
        """
        prompt = get_decision_log_prompt(timeline_context, branch_name)

        try:
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical decision analyst. Analyze development "
                                 "timelines to extract decision rationale. Always cite evidence "
                                 "from the timeline."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "decision_log",
                        "strict": True,
                        "schema": DECISION_LOG_SCHEMA
                    }
                }
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except json.JSONDecodeError as e:
            raise InferenceError(f"Invalid JSON from OpenAI: {e}")
        except Exception as e:
            raise InferenceError(f"OpenAI API error: {e}")

    def generate_summary(self, decision_log: Dict[str, Any]) -> str:
        """
        Generate a short PR summary from decision log.

        Args:
            decision_log: Decision log dictionary

        Returns:
            Markdown formatted summary

        Raises:
            InferenceError: If OpenAI API call fails
        """
        decision_log_json = json.dumps(decision_log, indent=2)
        prompt = get_summary_prompt(decision_log_json)

        try:
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.temperature
            )

            return response.choices[0].message.content

        except Exception as e:
            raise InferenceError(f"OpenAI API error: {e}")
