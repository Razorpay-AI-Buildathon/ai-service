from app.state import RecoveryState
from typing import Tuple, List


def validate_output_guardrail(state: RecoveryState) -> Tuple[bool, List[str]]:
    violations = []
    allowed_actions = {
        "RETRY_PAYMENT",
        "SEND_PAYMENT_REMINDER",
        "SEND_CHECKOUT_RECOVERY_MESSAGE",
        "RETRY_SUBSCRIPTION",
        "SEND_INVOICE_REMINDER",
        "ESCALATE_TO_HUMAN",
        "DO_NOTHING",
    }

    proposed = state.get("proposed_action")
    if proposed and proposed not in allowed_actions:
        violations.append(
            f"Output Guardrail: Planner action '{proposed}' does not match allowed Pydantic Literal options."
        )

    return len(violations) == 0, violations
