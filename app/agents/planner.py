from app.state import RecoveryState
from app.llm.qwen import ask_qwen
from app.services.strategy_engine import RecoveryStrategyEngine
import json


def planner_agent(state: RecoveryState) -> dict:
    # 1. Run the Strategy Selection Engine to rank candidates
    ranked = RecoveryStrategyEngine.evaluate_candidates(state)
    ranked_actions = [r["action_type"] for r in ranked]

    system_prompt = f"""
    You are the Planner Agent. Select exactly one bounded action to resolve the failure.
    Allowed proposed_action values (ranked by historical effectiveness & policy compliance):
    {json.dumps(ranked_actions)}
    
    Grounding Playbook Instruction: You MUST prioritize the strategy and allowed actions specified in the retrieved playbook.
    
    Return JSON only:
    {{
        "proposed_action": "RETRY_PAYMENT" or other enum value,
        "planner_reason": "Justification reasoning text",
        "planner_confidence": 0.0 to 1.0
    }}
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
    Ranked Candidate Strategy Suggestions: {json.dumps(ranked)}
    """

    response = ask_qwen(system_prompt, user_prompt)
    data = json.loads(response)

    proposed = data.get("proposed_action", "DO_NOTHING")
    # Enforce policy bounds: if proposed action is filtered out by strategy engine, fallback to highest ranked candidate
    if proposed not in ranked_actions and len(ranked_actions) > 0:
        proposed = ranked_actions[0]

    return {
        "proposed_action": proposed,
        "planner_reason": data.get("planner_reason", "Fallback default no-action plan"),
        "planner_confidence": data.get("planner_confidence", 0.70),
    }
