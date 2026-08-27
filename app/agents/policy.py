from app.state import RecoveryState
from app.llm.qwen import ask_qwen
import json


def policy_agent(state: RecoveryState) -> dict:
    system_prompt = """
    You are the Policy Agent for a merchant payment platform.
    Analyze if the recovery complies with contact guidelines and maximum retry rules.
    Grounded Policy Rule: You must restrict the action to values allowed in the retrieved recovery playbook.
    
    Return JSON only:
    {
        "policy_status": "STANDARD" or "ELEVATED" or "BLOCKED",
        "policy_reason": "Justification reasoning text",
        "policy_confidence": 0.0 to 1.0
    }
    """

    # Inject retrieved playbook constraints as grounding evidence
    playbooks_txt = ""
    if state.get("playbook_matches"):
        playbooks_txt = json.dumps(state["playbook_matches"])

    user_prompt = f"""
    Evaluate compliance:
    Attempt Number: {state.get("recovery_attempt_count")}
    Max Retries Allowed: {state.get("max_retries")}
    Retrieved Playbook Parameters: {playbooks_txt}
    """

    response = ask_qwen(system_prompt, user_prompt)
    data = json.loads(response)

    return {
        "policy_status": data.get("policy_status", "STANDARD"),
        "policy_reason": data.get("policy_reason", "Complies with standard policies"),
        "policy_confidence": data.get("policy_confidence", 0.70),
    }
