PLAYBOOK_KB = {
    # Payment failure playbooks
    "insufficient_funds": {
        "playbook_id": "PB-PAY-001",
        "description": "Insufficient balance or card limits exceeded",
        "recovery_strategy": [
            "1. Do not immediately retry transaction.",
            "2. Send soft payment reminder asking client to top up balance or swap cards.",
            "3. Enforce maximum 1 payment retry to prevent card issuer penalty blocks.",
        ],
        "allowed_actions": ["SEND_PAYMENT_REMINDER", "ESCALATE_TO_HUMAN"],
        "cooldown_hours": 24,
    },
    "bank_timeout": {
        "playbook_id": "PB-PAY-002",
        "description": "Issuer bank network timed out or failed to respond",
        "recovery_strategy": [
            "1. Retry payment automatically after a short technical delay.",
            "2. Limit retries to 3 times over 48 hours.",
            "3. Escalate to human support if failure persists after max retries.",
        ],
        "allowed_actions": ["RETRY_PAYMENT", "ESCALATE_TO_HUMAN"],
        "cooldown_hours": 12,
    },
    "network_error": {
        "playbook_id": "PB-PAY-003",
        "description": "Network connection error in merchant router payment stream",
        "recovery_strategy": [
            "1. Immediate auto-retry is permissible due to connection dropped during transport.",
            "2. Escalate if card networks reject retries due to security token expirations.",
        ],
        "allowed_actions": ["RETRY_PAYMENT", "ESCALATE_TO_HUMAN"],
        "cooldown_hours": 4,
    },
    "expired_card": {
        "playbook_id": "PB-PAY-004",
        "description": "Card expiry date check failed on network gateway",
        "recovery_strategy": [
            "1. Never auto-retry the payment method.",
            "2. Deliver checkout update notifications prompting update of card parameters.",
        ],
        "allowed_actions": ["SEND_PAYMENT_REMINDER", "ESCALATE_TO_HUMAN"],
        "cooldown_hours": 48,
    },
    "card_declined": {
        "playbook_id": "PB-PAY-005",
        "description": "General card issuer declined error code",
        "recovery_strategy": [
            "1. Check risk profile metrics of customer.",
            "2. Request client review credit limit configurations.",
            "3. Escalate to human review if consecutive attempts decline.",
        ],
        "allowed_actions": ["SEND_PAYMENT_REMINDER", "ESCALATE_TO_HUMAN"],
        "cooldown_hours": 24,
    },
    # Checkout abandonment playbooks
    "checkout abandonment": {
        "playbook_id": "PB-CHK-001",
        "description": "Customer dropped off checkout screen during selection",
        "recovery_strategy": [
            "1. Deliver checkout recovery message including cart details and coupon link.",
            "2. Restrict to 1 recovery notification to avoid spam warnings.",
        ],
        "allowed_actions": ["SEND_CHECKOUT_RECOVERY_MESSAGE", "DO_NOTHING"],
        "cooldown_hours": 24,
    },
    # Subscription failure playbooks
    "subscription failure": {
        "playbook_id": "PB-SUB-001",
        "description": "Recurring billing schedule payment failed",
        "recovery_strategy": [
            "1. Retry subscription billing cycle at off-peak hours.",
            "2. Escalate to human recovery team after 3 consecutive days failed charging.",
        ],
        "allowed_actions": ["RETRY_SUBSCRIPTION", "SEND_PAYMENT_REMINDER"],
        "cooldown_hours": 24,
    },
    # Overdue invoice playbooks
    "overdue invoice": {
        "playbook_id": "PB-INV-001",
        "description": "B2B client invoice overdue past grace threshold",
        "recovery_strategy": [
            "1. Deliver formal invoice reminder attaching invoice statement.",
            "2. Track promise-to-pay calendar date updates.",
        ],
        "allowed_actions": ["SEND_INVOICE_REMINDER", "ESCALATE_TO_HUMAN"],
        "cooldown_hours": 72,
    },
    # Payment promise broken playbooks
    "payment promise broken": {
        "playbook_id": "PB-INV-002",
        "description": "Client missed scheduled promise-to-pay date",
        "recovery_strategy": [
            "1. Escalate directly to human collection team.",
            "2. Restrict further automatic payment reminders.",
        ],
        "allowed_actions": ["ESCALATE_TO_HUMAN"],
        "cooldown_hours": 24,
    },
    # Disputed invoice playbooks
    "disputed invoice": {
        "playbook_id": "PB-INV-003",
        "description": "Customer disputed invoice charges",
        "recovery_strategy": [
            "1. Mark case status as blocked and suspend collections.",
            "2. Route case immediately to account dispute specialist.",
        ],
        "allowed_actions": ["ESCALATE_TO_HUMAN", "DO_NOTHING"],
        "cooldown_hours": 24,
    },
}


def retrieve_playbook(event_type: str, failure_code: str = None) -> dict:
    """
    Looks up appropriate recovery playbook instructions from the domain KB.
    Failsafe: Defaults to generic recovery guidelines.
    """
    key = None
    # For subscription failures, prioritize the event type classification playbook
    if event_type and event_type.upper() == "SUBSCRIPTION_FAILURE":
        key = "subscription failure"
    elif failure_code and failure_code.lower() in PLAYBOOK_KB:
        key = failure_code.lower()
    elif event_type and event_type.lower().replace("_", " ") in PLAYBOOK_KB:
        key = event_type.lower().replace("_", " ")

    if key and key in PLAYBOOK_KB:
        match = PLAYBOOK_KB[key]
        return {
            "playbook_id": match["playbook_id"],
            "description": match["description"],
            "recovery_strategy": match["recovery_strategy"],
            "allowed_actions": match["allowed_actions"],
            "cooldown_hours": match["cooldown_hours"],
            "source": "Local Playbook KB Store",
            "confidence": 1.0,
        }

    return {
        "playbook_id": "PB-GEN-999",
        "description": "Generic billing recovery playbook directives",
        "recovery_strategy": [
            "1. Escalate to human supervisor if risk level is CRITICAL.",
            "2. Propose DO_NOTHING if risk cannot be calculated.",
        ],
        "allowed_actions": ["ESCALATE_TO_HUMAN", "DO_NOTHING"],
        "cooldown_hours": 24,
        "source": "Failsafe default",
        "confidence": 0.50,
    }
