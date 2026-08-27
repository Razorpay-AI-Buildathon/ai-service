from app.state import RecoveryState
from typing import Tuple, List


def validate_hallucination_guardrail(state: RecoveryState) -> Tuple[bool, List[str]]:
    violations = []
    diagnosis = state.get("diagnosis", "")
    failure_code = state.get("failure_code", "")

    # Flags hallucinated claims not matching the core failure event
    if failure_code and failure_code not in diagnosis:
        violations.append(
            f"Hallucination Guardrail: Diagnosis does not ground the original failure code '{failure_code}'."
        )

    return len(violations) == 0, violations
