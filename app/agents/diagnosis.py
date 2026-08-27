from app.state import RecoveryState
from app.llm.qwen import ask_qwen
from app.retrieval.playbook_kb import retrieve_playbook
import json


def diagnosis_agent(state: RecoveryState) -> dict:
    system_prompt = """
    You are the Diagnosis Agent for a payment revenue recovery platform.
    Your responsibility is to identify the technical reason for the failure.
    Return JSON only:
    {
        "diagnosis": "Short technical diagnosis description",
        "root_cause": "Identified root cause details",
        "confidence": 0.0 to 1.0
    }
    """

    user_prompt = f"""
    Analyze this failure event:
    Event Type: {state.get("event_type")}
    Failure Code: {state.get("failure_code")}
    Amount: {state.get("amount")} {state.get("currency")}
    """

    response = ask_qwen(system_prompt, user_prompt)
    data = json.loads(response)

    # Trigger RAG playbook retrieval step inside diagnosis agent node
    playbook = retrieve_playbook(state.get("event_type"), state.get("failure_code"))

    return {
        "diagnosis": data.get("diagnosis", "Unknown technical error"),
        "diagnosis_root_cause": data.get("root_cause", "UNKNOWN"),
        "diagnosis_confidence": data.get("confidence", 0.70),
        "playbook_matches": [playbook],
        "playbook_source": playbook["source"],
        "playbook_confidence": playbook["confidence"],
    }
