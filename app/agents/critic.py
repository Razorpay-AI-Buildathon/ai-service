from app.state import RecoveryState
from app.llm.qwen import ask_qwen
import json


def critic_agent(state: RecoveryState) -> dict:
    system_prompt = """
    You are the Critic Agent. Assess whether the Planner's proposed action is consistent and justified.
    Return JSON only:
    {
        "critic_decision": "ACCEPT" or "REJECT",
        "critic_reason": "Justification reasoning text",
        "critic_confidence": 0.0 to 1.0,
        "replan_required": true or false
    }
    """

    user_prompt = f"""
    Evaluate proposal consistency:
    Proposed Action: {state.get("proposed_action")}
    Planner Reason: {state.get("planner_reason")}
    Risk Level: {state.get("risk_level")}
    """

    response = ask_qwen(system_prompt, user_prompt)
    data = json.loads(response)

    return {
        "critic_decision": data.get("critic_decision", "ACCEPT"),
        "critic_reason": data.get("critic_reason", "Action verified as safe"),
        "critic_confidence": data.get("critic_confidence", 0.70),
        "replan_required": data.get("replan_required", False),
    }
