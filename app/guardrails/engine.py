from app.state import RecoveryState
from app.guardrails.input import validate_input_guardrail
from app.guardrails.output import validate_output_guardrail
from app.guardrails.confidence import validate_confidence_guardrail
from app.guardrails.hallucination import validate_hallucination_guardrail
from app.guardrails.retry import validate_retry_guardrail
from typing import Dict, Any


class GuardrailsEngine:
    @staticmethod
    def evaluate(state: RecoveryState) -> Dict[str, Any]:
        violations = []
        warnings = []

        # Evaluate Input Guardrail
        in_ok, in_viols = validate_input_guardrail(state)
        if not in_ok:
            violations.extend(in_viols)

        # Evaluate Output Guardrail
        out_ok, out_viols = validate_output_guardrail(state)
        if not out_ok:
            violations.extend(out_viols)

        # Evaluate Confidence Guardrail
        conf_ok, conf_viols = validate_confidence_guardrail(state)
        if not conf_ok:
            violations.extend(conf_viols)

        # Evaluate Hallucination Guardrail
        hal_ok, hal_viols = validate_hallucination_guardrail(state)
        if not hal_ok:
            warnings.extend(hal_viols)  # Treated as warning to avoid total blockages

        # Evaluate Retry Guardrail
        retry_ok, retry_viols = validate_retry_guardrail(state)
        if not retry_ok:
            violations.extend(retry_viols)

        status = "PASSED" if len(violations) == 0 else "FAILED"
        return {
            "guardrail_status": status,
            "guardrail_violations": violations,
            "guardrail_warnings": warnings,
        }
