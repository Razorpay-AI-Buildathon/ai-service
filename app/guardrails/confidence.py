from app.state import RecoveryState
from app.config import settings
from typing import Tuple, List


def validate_confidence_guardrail(state: RecoveryState) -> Tuple[bool, List[str]]:
    violations = []
    confidence = state.get("planner_confidence", 0.0)
    risk_level = state.get("risk_level", "LOW")

    threshold = settings.CONFIDENCE_THRESHOLD
    if risk_level == "HIGH" or risk_level == "CRITICAL":
        threshold = settings.CRITICAL_CONFIDENCE_THRESHOLD

    if confidence < threshold:
        violations.append(
            f"Confidence Guardrail: Planner confidence {confidence:.2f} is below safety threshold {threshold:.2f} for risk level '{risk_level}'."
        )

    return len(violations) == 0, violations
