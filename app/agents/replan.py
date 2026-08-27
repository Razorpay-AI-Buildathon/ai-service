from app.state import RecoveryState
from app.llm.qwen import ask_qwen
import json


def replan_agent(state: RecoveryState) -> dict:
    system_prompt = """
    You are the Replan Agent. The Critic rejected the Planner's original action. Propose a revised action.
    Return JSON only:
    {
        "revised_action": "ESCALATE_TO_HUMAN" or other enum value,
        "revised_reason": "Justification reasoning text",
        "replan_confidence": 0.0 to 1.0
    }
    """

    user_prompt = f"""
    Planner Proposed: {state.get("proposed_action")}
    Critic Reason: {state.get("critic_reason")}
    """

    response = ask_qwen(system_prompt, user_prompt)
    data = json.loads(response)

    return {
        "revised_action": data.get("revised_action", "ESCALATE_TO_HUMAN"),
        "revised_reason": data.get(
            "revised_reason", "Default fallback to human review"
        ),
        "replan_confidence": data.get("replan_confidence", 0.70),
    }
