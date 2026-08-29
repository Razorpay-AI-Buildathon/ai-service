from fastapi import FastAPI
from app.graph import graph
from app.state import RecoveryState

app = FastAPI(title="RecoverAI Agentic Service")


@app.get("/health")
def get_health():
    return {"status": "ok"}


@app.post("/analyze-event")
def analyze_event(state_input: RecoveryState):
    # Run the compiled LangGraph workflow state machine
    final_state = graph.invoke(state_input)
    return final_state
