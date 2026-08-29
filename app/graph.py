# app/graph.py

from langgraph.graph import END, START, StateGraph
from app.agents.diagnosis import diagnosis_agent
from app.agents.policy import policy_agent
from app.agents.risk import risk_agent
from app.agents.planner import planner_agent
from app.agents.critic import critic_agent
from app.agents.replan import replan_agent
from app.state import RecoveryState
from app.tools.notify_backend import send_proposal_to_action_guard


def diagnosis_node(state: RecoveryState):
    return diagnosis_agent(state)


def policy_node(state: RecoveryState):
    return policy_agent(state)


def risk_node(state: RecoveryState):
    return risk_agent(state)


def planner_node(state: RecoveryState):
    return planner_agent(state)


def critic_node(state: RecoveryState):
    return critic_agent(state)


def replan_node(state: RecoveryState):
    result = replan_agent(state)
    result["retry_count"] = state.get("retry_count", 0) + 1
    result["replan_required"] = False
    result["current_node"] = "replan"
    return result


def finalize_node(state: RecoveryState):
    if state.get("revised_action"):
        final_action = state.get("revised_action")
        final_reason = state.get("revised_reason")
        final_confidence = state.get("replan_confidence")
    else:
        final_action = state.get("proposed_action")
        final_reason = state.get("planner_reason")
        final_confidence = state.get("planner_confidence")

    import uuid

    action_id = state.get("action_id") or f"act-{uuid.uuid4().hex}"

    amount = float(state.get("amount", 0.0))
    history_success_rate = float(state.get("customer_payment_history_success_rate", 0.90))
    erv = amount * history_success_rate * float(final_confidence or 0.7)

    risk_score = float(state.get("customer_risk_score", 0.15))

    playbook_ref = "DEFAULT_PLAYBOOK"
    if state.get("playbook_matches"):
        playbook_ref = state["playbook_matches"][0].get("id", "DEFAULT_PLAYBOOK")

    recommended_delay = 300
    if final_action == "SEND_PAYMENT_REMINDER":
        recommended_delay = 3600 * 2
    elif final_action == "SEND_CHECKOUT_RECOVERY_MESSAGE":
        recommended_delay = 1800

    proposal = {
        "action_id": action_id,
        "action_type": final_action,
        "confidence": float(final_confidence or 0.70),
        "reasoning_summary": final_reason,
        "expected_recovery_value": round(erv, 2),
        "risk_score": risk_score,
        "policy_basis": state.get("policy_reason", "Standard compliance policy checks passed."),
        "playbook_reference": playbook_ref,
        "recommended_delay_seconds": recommended_delay
    }

    return {
        "final_action": final_action,
        "final_reason": final_reason,
        "final_confidence": final_confidence,
        "action_id": action_id,
        "proposal": proposal,
        "current_node": "finalize",
    }


def handoff_node(state: RecoveryState):
    result = send_proposal_to_action_guard(state)
    return {"action_guard_result": result, "current_node": "handoff"}


def route_after_critic(state: RecoveryState) -> str:
    raw_decision = state.get("critic_decision")
    decision_str = str(raw_decision).strip().upper() if raw_decision else ""

    replan_needed = state.get("replan_required", False)
    retry_count = int(state.get("retry_count", 0))
    max_retries = int(state.get("max_retries", 1))

    if decision_str == "ACCEPT" and not replan_needed:
        return "finalize"
    if decision_str == "REJECT" or replan_needed:
        if retry_count < max_retries:
            return "replan"
        return "finalize"
    return "finalize"


def build_graph():
    workflow = StateGraph(RecoveryState)

    workflow.add_node("diagnosis", diagnosis_node)
    workflow.add_node("policy", policy_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("replan", replan_node)
    workflow.add_node("finalize", finalize_node)
    workflow.add_node("handoff", handoff_node)

    workflow.add_edge(START, "diagnosis")
    workflow.add_edge(START, "policy")
    workflow.add_edge(START, "risk")

    workflow.add_edge("diagnosis", "planner")
    workflow.add_edge("policy", "planner")
    workflow.add_edge("risk", "planner")

    workflow.add_edge("planner", "critic")

    workflow.add_conditional_edges(
        "critic", route_after_critic, {"finalize": "finalize", "replan": "replan"}
    )

    workflow.add_edge("replan", "finalize")
    workflow.add_edge("finalize", "handoff")
    workflow.add_edge("handoff", END)

    return workflow.compile()


graph = build_graph()
