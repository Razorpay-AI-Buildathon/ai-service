import os
import json
import re
import httpx
from app.config import settings


def ask_qwen(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 800,
    temperature: float = 0.0,
    structured: bool = True,
) -> str:
    """
    Sends request to LLM, falling back to a deterministic payment recovery response rule engine
    if API keys are missing or requests fail.
    """
    api_key = os.getenv("HF_TOKEN") or os.getenv("QWEN_API_KEY")
    model_name = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-72B-Instruct")

    if api_key:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            resp = httpx.post(
                "https://router.huggingface.co/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=15.0,
            )
            if resp.status_code == 200:
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                return content.strip()
        except Exception as e:
            print(f"⚠️ Qwen API Call failed: {e}. Falling back to rule-based engine.")

    # Resilient local fallback reasoning engine for payment failures
    low_sys = system_prompt.lower()
    low_user = user_prompt.lower()

    if "diagnosis agent" in low_sys:
        diag = "Standard payment processing issues"
        cause = "General transaction declined"
        if "insufficient_funds" in low_user:
            diag = "Insufficient Balance Outage"
            cause = "Customer has insufficient funds in card or bank account"
        elif "bank_timeout" in low_user:
            diag = "Bank Network Timeout Latency"
            cause = "Issuer bank failed to respond within the allowed window"
        elif "overdue" in low_user:
            diag = "Invoice Payment Overdue"
            cause = "Client invoice outstanding past grace period date"
        elif "checkout_abandonment" in low_user:
            diag = "Abandoned checkout session"
            cause = "Customer dropped off cart without completing payment flow"
        elif (
            "subscription_failure" in low_user
            or "recurring" in low_user
            or "card_declined" in low_user
        ):
            diag = "Recurring Subscription Billing Failure"
            cause = "Card declined or expired during automated subscription renewal retry cycle"

        return json.dumps({"diagnosis": diag, "root_cause": cause, "confidence": 0.95})

    elif "policy agent" in low_sys:
        status = "STANDARD"
        reason = "Active policies permit automated intervention"
        if "attempt_number: 3" in low_user or "attempt_number: 2" in low_user:
            status = "ELEVATED"
            reason = "Retry limit threshold boundaries reached"
        return json.dumps(
            {
                "policy_status": status,
                "policy_reason": reason,
                "policy_confidence": 0.98,
            }
        )

    elif "risk agent" in low_sys:
        level = "LOW"
        reason = "Low risk profile transaction"

        # Regex numerical risk parser to handle raw thresholds safely
        match = re.search(r"customer risk score:\s*([0-9.]+)", low_user)
        if match:
            try:
                score = float(match.group(1))
                if score >= 0.85:
                    level = "CRITICAL"
                    reason = f"Customer risk score {score} is in the critical threshold window"
                elif score >= 0.60:
                    level = "HIGH"
                    reason = f"Customer risk score {score} is elevated"
                elif score >= 0.30:
                    level = "MEDIUM"
                    reason = f"Customer risk score {score} is moderate"
            except Exception:
                pass

        return json.dumps(
            {"risk_level": level, "risk_reason": reason, "risk_confidence": 0.92}
        )

    elif "planner agent" in low_sys:
        proposed = "DO_NOTHING"
        reason = "No match"
        if "insufficient_funds" in low_user:
            proposed = "SEND_PAYMENT_REMINDER"
            reason = "Notify client of insufficient balance"
        elif "bank_timeout" in low_user:
            proposed = "RETRY_PAYMENT"
            reason = "Automatically retry charge block"
        elif "overdue" in low_user:
            proposed = "SEND_INVOICE_REMINDER"
            reason = "Deliver overdue balance statement"
        elif "checkout_abandonment" in low_user:
            proposed = "SEND_CHECKOUT_RECOVERY_MESSAGE"
            reason = "Trigger cart abandonment sequence"
        elif (
            "subscription_failure" in low_user
            or "recurring" in low_user
            or "card_declined" in low_user
        ):
            proposed = "RETRY_SUBSCRIPTION"
            reason = "Automatically schedule retry attempt for recurring subscription"

        return json.dumps(
            {
                "proposed_action": proposed,
                "planner_reason": reason,
                "planner_confidence": 0.89,
            }
        )

    elif "critic agent" in low_sys:
        decision = "ACCEPT"
        reason = "Proposed action aligns with historical success variables"
        replan = False

        if (
            "proposed action: retry_payment" in low_user
            and "risk level: high" in low_user
        ):
            decision = "REJECT"
            reason = "Risk level is HIGH. Retry payment represents excessive transaction failure penalty risks."
            replan = True

        return json.dumps(
            {
                "critic_decision": decision,
                "critic_reason": reason,
                "critic_confidence": 0.95,
                "replan_required": replan,
            }
        )

    elif "replan agent" in low_sys:
        return json.dumps(
            {
                "revised_action": "ESCALATE_TO_HUMAN",
                "revised_reason": "Escalated due to repeated rejections or critical conditions",
                "replan_confidence": 0.99,
            }
        )

    return json.dumps({"status": "SUCCESS"})
