from app.state import RecoveryState
from app.llm.qwen import ask_qwen
import json


def risk_agent(state: RecoveryState) -> dict:
    system_prompt = """
    You are the Risk Agent. Analyze transaction amount, user history, and charge failure frequency to determine risk.
    Return JSON only:
    {
        "risk_level": "LOW" or "MEDIUM" or "HIGH" or "CRITICAL",
        "risk_reason": "Risk analysis justification details",
        "risk_confidence": 0.0 to 1.0
    }
    """

    user_prompt = f"""
    Evaluate risk metrics:
    Amount: {state.get("amount")} {state.get("currency")}
    Customer Risk Score: {state.get("customer_risk_score")}
    Payment success history: {state.get("customer_payment_history_success_rate")}
    """

    response = ask_qwen(system_prompt, user_prompt)
    data = json.loads(response)

    return {
        "risk_level": data.get("risk_level", "LOW"),
        "risk_reason": data.get("risk_reason", "Low baseline transaction risk profile"),
        "risk_confidence": data.get("risk_confidence", 0.70),
    }
