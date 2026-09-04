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

## AI Reasoning Council Workflow

The following Mermaid diagram illustrates the LangGraph state machine and the interaction between the specialized LLM agents when evaluating a failed payment case.

```mermaid
graph TD
    %% Input Node
    Start(["Input: Payment Failure Event<br/>(Amount, Error Code, History)"])
    
    %% Agents
    TransactionAnalyst["Transaction Analyst Agent<br/>Analyzes failure context & amount limits"]
    CustomerRiskGuard["Customer Risk Agent<br/>Evaluates customer history & risk score"]
    StrategySelector["Strategy Selector Agent<br/>Synthesizes findings into final playbook"]
    
    %% Output
    FinalDecision(["Output: Proposed Action<br/>& Confidence Score"])
    
    %% Flow
    Start --> TransactionAnalyst
    TransactionAnalyst --> CustomerRiskGuard
    CustomerRiskGuard --> StrategySelector
    
    %% Decisions (Sub-routing logic)
    StrategySelector --> |"Low Risk + High Success Rate"| ActionRetry[/"Action: RETRY_PAYMENT"/]
    StrategySelector --> |"High Risk or Repeated Failures"| ActionEscalate[/"Action: ESCALATE_TO_HUMAN"/]
    StrategySelector --> |"Fraud Suspected"| ActionDoNothing[/"Action: DO_NOTHING"/]
    
    ActionRetry --> FinalDecision
    ActionEscalate --> FinalDecision
    ActionDoNothing --> FinalDecision

    %% Styling
    classDef agent fill:#f9f2f4,stroke:#d35400,stroke-width:2px;
    class TransactionAnalyst,CustomerRiskGuard,StrategySelector agent;
    classDef endpoint fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    class Start,FinalDecision endpoint;
```
