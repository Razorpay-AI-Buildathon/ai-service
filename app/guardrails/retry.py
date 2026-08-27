from app.state import RecoveryState
from app.config import settings
from typing import Tuple, List


def validate_retry_guardrail(state: RecoveryState) -> Tuple[bool, List[str]]:
    violations = []
    retry_count = state.get("retry_count", 0)

    if retry_count > settings.MAX_REPLANS:
        violations.append(
            f"Retry Guardrail: Council exceeded limit of {settings.MAX_REPLANS} replan cycles. Forcing fallback."
        )

    return len(violations) == 0, violations
