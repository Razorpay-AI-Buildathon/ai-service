# RecoverAI Agentic Service

LangGraph-powered stateful multi-agent consensus council which analyses payment failure events to formulate recovery strategies.

## Features
- **Multi-Agent Flow**: Coordinates Transaction Analyst, Customer Risk Guard, and Strategy Selection agents using state graph routing.
- **Reasoning Council**: Selects recovery playbooks based on transactional risk metrics and customer success records.

## Getting Started

### Prerequisites
- Python 3.11

### Setup & Run
1. Create virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the development FastAPI server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```
3. Run tests:
   ```bash
   pytest
   ```
