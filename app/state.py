# app/state.py

from typing import List, Dict, Any
from typing_extensions import TypedDict


class RecoveryState(TypedDict, total=False):
    case_id: str
    event_id: str
    event_type: str
    amount: float
    currency: str
    failure_code: str
    customer_id: str
    customer_risk_score: float
    customer_payment_history_success_rate: float
    recovery_attempt_count: int
    max_retries: int
    retry_count: int
    failed_actions: List[str]

    # RAG playbook parameters
    playbook_matches: List[Dict[str, Any]]
    playbook_source: str
    playbook_confidence: float

    # Diagnosis Agent outputs
    diagnosis: str
    diagnosis_root_cause: str
    diagnosis_confidence: float

    # Policy Agent outputs
    policy_status: str
    policy_reason: str
    policy_confidence: float

    # Risk Agent outputs
    risk_level: str
    risk_reason: str
    risk_confidence: float

    # Planner Agent outputs
    proposed_action: str
    planner_reason: str
    planner_confidence: float

    # Critic Agent outputs
    critic_decision: str
    critic_reason: str
    critic_confidence: float
    replan_required: bool

    # Replan Agent outputs
    revised_action: str
    revised_reason: str
    replan_confidence: float

    # Final collapsed fields
    final_action: str
    final_reason: str
    final_confidence: float
    current_node: str
    action_id: str
    proposal: Dict[str, Any]

    # Guardrails
    guardrail_status: str
    guardrail_violations: List[str]
    guardrail_warnings: List[str]
    action_guard_result: Dict[str, Any]
