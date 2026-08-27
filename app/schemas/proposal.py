# app/schemas/proposal.py

from pydantic import BaseModel, Field
from typing import Literal

RecoveryActionLiteral = Literal[
    "RETRY_PAYMENT",
    "SEND_PAYMENT_REMINDER",
    "SEND_CHECKOUT_RECOVERY_MESSAGE",
    "RETRY_SUBSCRIPTION",
    "SEND_INVOICE_REMINDER",
    "ESCALATE_TO_HUMAN",
    "DO_NOTHING",
]


class RecoveryProposal(BaseModel):
    case_id: str
    proposed_action: RecoveryActionLiteral
    confidence_score: float = Field(ge=0.0, le=1.0)
    diagnosis_reason: str
    critic_decision: Literal["ACCEPT", "REJECT", "UNKNOWN"] = "UNKNOWN"
    critic_reason: str = None
    replan_required: bool = False
    action_id: str | None = None
