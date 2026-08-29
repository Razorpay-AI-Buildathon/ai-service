import uuid
from typing import Dict, Any, List

class RecoveryStrategyEngine:
    CANDIDATES = [
        "RETRY_PAYMENT",
        "SEND_PAYMENT_REMINDER",
        "SEND_CHECKOUT_RECOVERY_MESSAGE",
        "RETRY_SUBSCRIPTION",
        "SEND_INVOICE_REMINDER",
        "ESCALATE_TO_HUMAN",
        "DO_NOTHING"
    ]

    @classmethod
    def evaluate_candidates(cls, state: dict) -> List[Dict[str, Any]]:
        amount = float(state.get("amount", 0.0))
        attempts = int(state.get("recovery_attempt_count", 0))
        max_retries = int(state.get("max_retries", 3))
        risk_score = float(state.get("customer_risk_score", 0.15))
        success_rate = float(state.get("customer_payment_history_success_rate", 0.90))
        failed_actions = state.get("failed_actions", [])
        failure_code = state.get("failure_code", "")

        results = []
        for candidate in cls.CANDIDATES:
            # 1. Compute baseline probability
            base_prob = 0.50
            if candidate == "RETRY_PAYMENT":
                base_prob = success_rate * 0.8
                # Failure reason affects strategy
                if failure_code == "insufficient_funds":
                    base_prob *= 0.2  # Low chance for direct retry
                elif failure_code in ("bank_timeout", "network_error"):
                    base_prob *= 1.3  # High chance for retrying transient errors
            elif candidate == "SEND_PAYMENT_REMINDER":
                base_prob = success_rate * 0.6
                if failure_code == "insufficient_funds":
                    base_prob *= 1.4  # Remind them to top up balance
            elif candidate == "SEND_CHECKOUT_RECOVERY_MESSAGE":
                base_prob = success_rate * 0.5
            elif candidate == "RETRY_SUBSCRIPTION":
                base_prob = success_rate * 0.7
                if failure_code == "insufficient_funds":
                    base_prob *= 0.2
            elif candidate == "SEND_INVOICE_REMINDER":
                base_prob = success_rate * 0.65
            elif candidate == "ESCALATE_TO_HUMAN":
                base_prob = 0.20
            elif candidate == "DO_NOTHING":
                base_prob = 0.0

            # 2. Strategy Change after repeated failure: Penalize previously failed actions
            if candidate in failed_actions:
                base_prob *= 0.15  # Heavy penalty forces strategy change

            # Apply soft policy penalty rather than hard filtering to let LLM remain advisory
            if candidate in ("RETRY_PAYMENT", "RETRY_SUBSCRIPTION") and attempts >= max_retries:
                base_prob *= 0.1

            # Apply soft risk penalty
            if candidate in ("RETRY_PAYMENT", "RETRY_SUBSCRIPTION") and risk_score > 0.6:
                base_prob *= 0.2

            # 2. ERV Calculation
            erv = amount * base_prob

            results.append({
                "action_type": candidate,
                "confidence": round(base_prob, 2),
                "expected_recovery_value": round(erv, 2),
                "risk_score": risk_score,
                "policy_basis": f"Policy evaluated attempts {attempts}/{max_retries} allowed."
            })

        # Rank candidates by ERV descending
        results.sort(key=lambda x: x["expected_recovery_value"], reverse=True)
        return results
