from app.state import RecoveryState
from typing import Dict, Any, Tuple, List


def validate_input_guardrail(state: RecoveryState) -> Tuple[bool, List[str]]:
    violations = []
    required = ["case_id", "event_id", "event_type", "amount"]
    for field in required:
        if field not in state or state[field] is None:
            violations.append(
                f"Input Guardrail: Missing required state input parameter '{field}'."
            )
    return len(violations) == 0, violations
