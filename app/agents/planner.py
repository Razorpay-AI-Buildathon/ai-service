from app.state import RecoveryState
from app.llm.qwen import ask_qwen
import json


def planner_agent(state: RecoveryState) -> dict:
    system_prompt = """
    You are the Planner Agent. Select exactly one bounded action to resolve the failure.
    Allowed proposed_action values:
    "RETRY_PAYMENT", "SEND_PAYMENT_REMINDER", "SEND_CHECKOUT_RECOVERY_MESSAGE", "RETRY_SUBSCRIPTION", "SEND_INVOICE_REMINDER", "ESCALATE_TO_HUMAN", "DO_NOTHING"
    
    Grounding Playbook Instruction: You MUST prioritize the strategy and allowed actions specified in the retrieved playbook.
    
    Return JSON only:
    {
        "proposed_action": "RETRY_PAYMENT" or other enum value,
        "planner_reason": "Justification reasoning text",
        "planner_confidence": 0.0 to 1.0
    }
    """

    playbooks_txt = ""
    if state.get("playbook_matches"):
        playbooks_txt = json.dumps(state["playbook_matches"])

    user_prompt = f"""
    Event Details:
    Event Type: {state.get("event_type")}
    Failure Code: {state.get("failure_code")}
    Amount: {state.get("amount")} {state.get("currency")}
    Risk Level: {state.get("risk_level")}
    Policy Status: {state.get("policy_status")}
    Retrieved Playbook Guidance: {playbooks_txt}
    """

    response = ask_qwen(system_prompt, user_prompt)
    data = json.loads(response)

    return {
        "proposed_action": data.get("proposed_action", "DO_NOTHING"),
        "planner_reason": data.get("planner_reason", "Fallback default no-action plan"),
        "planner_confidence": data.get("planner_confidence", 0.70),
    }
