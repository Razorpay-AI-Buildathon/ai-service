# app/tools/notify_backend.py

from app.schemas.proposal import RecoveryProposal
from app.config import settings
import httpx


def send_proposal_to_action_guard(state: dict) -> dict:
    proposal = RecoveryProposal(
        case_id=state["case_id"],
        proposed_action=state["final_action"],
        confidence_score=state.get("final_confidence", 0.0),
        diagnosis_reason=state.get("diagnosis", ""),
        critic_decision=state.get("critic_decision", "UNKNOWN"),
        critic_reason=state.get("critic_reason", ""),
        replan_required=state.get("replan_required", False),
        action_id=state.get("action_id"),
    )

    # In-memory direct call wrapper for testing/standalone script execution
    # to avoid needing a live running API server for the vertical slice tests.
    try:
        # Check environment flag to determine local-direct or HTTP execution
        import os

        if os.getenv("STANDALONE_CLI_TEST", "false").lower() == "true":
            # Lazy import to prevent backend dependencies in the dockerized ai-service container
            import sys
            from pathlib import Path

            backend_dir = str(Path(__file__).parent.parent.parent.parent / "backend")

            # Remove ai-service 'app' modules from sys.modules temporarily
            cached_ai_modules = {
                k: v
                for k, v in list(sys.modules.items())
                if k == "app" or k.startswith("app.")
            }
            for k in cached_ai_modules:
                sys.modules.pop(k, None)

            original_path = list(sys.path)
            if backend_dir in sys.path:
                sys.path.remove(backend_dir)
            sys.path.insert(0, backend_dir)

            try:
                try:
                    from app.services.action_guard import ActionGuard
                    from decimal import Decimal

                    approved, token, violations = ActionGuard.validate_action(
                        action_type=proposal.proposed_action,
                        amount=Decimal(str(state.get("amount", 0.0))),
                        currency=state.get("currency", "INR"),
                        current_attempts=state.get("recovery_attempt_count", 0),
                        max_retries=state.get("max_retries", 3),
                        amount_threshold_inr=Decimal("5000.00"),
                        has_active_action=state.get("has_active_action", False),
                        last_contact_at_str=state.get("last_contact_at_str"),
                        now_str=state.get("now_str"),
                        contact_cooldown_hours=state.get("contact_cooldown_hours", 24),
                        planner_confidence=proposal.confidence_score,
                        min_confidence_threshold=0.55,
                        case_id=state["case_id"],
                        event_id=state["event_id"],
                        action_id=state.get("action_id", "act-fallback"),
                    )
                except (ImportError, ModuleNotFoundError):
                    approved = True
                    violations = []
                    token = "MOCK-GUARD-TOKEN"
                    amount = float(state.get("amount", 0.0))
                    current_attempts = state.get("recovery_attempt_count", 0)
                    max_retries = state.get("max_retries", 3)
                    payment_actions = ("RETRY_PAYMENT", "RETRY_SUBSCRIPTION")
                    if amount > 5000.0 and proposal.proposed_action in payment_actions:
                        approved = False
                        violations.append("Amount exceeds guard threshold")
                    if current_attempts >= max_retries and proposal.proposed_action in payment_actions:
                        approved = False
                        violations.append("Retry attempts limit exceeded")

                res_status = "APPROVED" if approved else "REJECTED"
                if proposal.proposed_action == "ESCALATE_TO_HUMAN":
                    res_status = "HUMAN_REVIEW"

                return {
                    "approved": approved,
                    "authorization_token": token,
                    "resulting_status": res_status,
                    "violations": violations,
                    "warnings": [],
                }
            except Exception as e:
                raise e
            finally:
                # Restore original path and modules
                sys.path = original_path
                for k, v in cached_ai_modules.items():
                    sys.modules[k] = v

        with httpx.Client(timeout=5.0) as client:
            api_key = os.getenv("RECOVERAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "RECOVERAI_API_KEY environment variable is not configured on the AI Service."
                )
            headers = {"X-API-Key": api_key}
            resp = client.post(
                f"{settings.BACKEND_URL}/api/action-guard/evaluate",
                headers=headers,
                json={
                    "action_type": proposal.proposed_action,
                    "amount": state.get("amount", 0.0),
                    "currency": state.get("currency", "INR"),
                    "current_attempts": state.get("recovery_attempt_count", 0),
                    "max_retries": state.get("max_retries", 3),
                    "has_active_action": state.get("has_active_action", False),
                    "last_contact_at": state.get("last_contact_at_str"),
                    "now": state.get("now_str"),
                    "planner_confidence": proposal.confidence_score,
                    "case_id": state["case_id"],
                    "event_id": state["event_id"],
                    "action_id": state.get("action_id", "act-fallback"),
                },
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                return {
                    "approved": False,
                    "resulting_status": "HUMAN_REVIEW",
                    "violations": [
                        f"Backend Action Guard returned status {resp.status_code}"
                    ],
                }
    except Exception as e:
        return {
            "approved": False,
            "resulting_status": "HUMAN_REVIEW",
            "violations": [f"Connection error reaching Action Guard backend: {str(e)}"],
        }
