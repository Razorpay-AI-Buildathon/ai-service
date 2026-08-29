import unittest
import os
import json
from pathlib import Path
from app.graph import graph

class TestVerticalSliceCases(unittest.TestCase):
    
    def setUp(self):
        import sys
        os.environ["STANDALONE_CLI_TEST"] = "true"
        # Resolve portable relative path from ai-service/tests/ to RazorPay/backend/tests/
        root_dir = str(Path(__file__).parent.parent.parent)
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        local_path = Path(__file__).parent / "synthetic_events.json"
        events_path = local_path if local_path.exists() else Path(__file__).parent.parent.parent / "backend" / "tests" / "synthetic_events.json"
        with open(events_path, "r") as f:
            self.events = json.load(f)

    def tearDown(self):
        os.environ["STANDALONE_CLI_TEST"] = "false"

    def test_case_1_low_value_insufficient_funds(self):
        matching_event = next(
            e for e in self.events 
            if e["event_type"] == "FAILED_PAYMENT" 
            and e["failure_code"] == "insufficient_funds"
            and e["amount"] < 3000.0
            and e["currency"] == "INR"
        )
        
        state_input = {
            "case_id": matching_event["id"],
            "event_id": matching_event["id"],
            "event_type": matching_event["event_type"],
            "amount": matching_event["amount"],
            "currency": matching_event["currency"],
            "failure_code": matching_event["failure_code"],
            "customer_id": matching_event["customer_id"],
            "customer_risk_score": matching_event["customer_history"]["risk_score"],
            "customer_payment_history_success_rate": matching_event["customer_history"]["success_rate"],
            "recovery_attempt_count": matching_event["recovery_context"]["attempt_number"],
            "max_retries": matching_event["recovery_context"]["max_retries"],
            "has_active_action": matching_event["recovery_context"]["has_active_action"]
        }
        
        result = graph.invoke(state_input)
        
        self.assertIn("playbook_matches", result)
        self.assertEqual(result["playbook_matches"][0]["playbook_id"], "PB-PAY-001")
        self.assertEqual(result["playbook_source"], "Local Playbook KB Store")
        
        self.assertEqual(result["final_action"], "SEND_PAYMENT_REMINDER")
        self.assertTrue(result["action_guard_result"]["approved"])

    def test_case_2_high_value_overdue_invoice(self):
        matching_event = next(
            e for e in self.events 
            if e["event_type"] == "OVERDUE_INVOICE"
            and e["amount"] > 1000.0
        )
        
        state_input = {
            "case_id": matching_event["id"],
            "event_id": matching_event["id"],
            "event_type": matching_event["event_type"],
            "amount": matching_event["amount"],
            "currency": matching_event["currency"],
            "failure_code": matching_event["failure_code"],
            "customer_id": matching_event["customer_id"],
            "customer_risk_score": matching_event["customer_history"]["risk_score"],
            "customer_payment_history_success_rate": matching_event["customer_history"]["success_rate"],
            "recovery_attempt_count": matching_event["recovery_context"]["attempt_number"],
            "max_retries": matching_event["recovery_context"]["max_retries"],
            "has_active_action": matching_event["recovery_context"]["has_active_action"]
        }
        
        result = graph.invoke(state_input)
        
        self.assertEqual(result["playbook_matches"][0]["playbook_id"], "PB-INV-001")
        self.assertEqual(result["final_action"], "SEND_INVOICE_REMINDER")
        if not result["action_guard_result"]["approved"]:
            print(f"DEBUG: test_case_2 failed. Guard result: {result['action_guard_result']}")
        self.assertTrue(result["action_guard_result"]["approved"])

    def test_case_3_repeated_failed_payment_blocked(self):
        state_input = {
            "case_id": "case-test-repeated",
            "event_id": "event-test-repeated",
            "event_type": "FAILED_PAYMENT",
            "amount": 1000.0,
            "currency": "INR",
            "failure_code": "bank_timeout",
            "customer_id": "cust-repeated",
            "customer_risk_score": 0.1,
            "customer_payment_history_success_rate": 0.9,
            "recovery_attempt_count": 3,
            "max_retries": 3,
            "has_active_action": False
        }
        
        result = graph.invoke(state_input)
        self.assertEqual(result["playbook_matches"][0]["playbook_id"], "PB-PAY-002")
        self.assertEqual(result["final_action"], "RETRY_PAYMENT")
        self.assertFalse(result["action_guard_result"]["approved"])

    def test_case_4_amount_above_merchant_threshold(self):
        state_input = {
            "case_id": "case-test-above-thresh",
            "event_id": "event-test-above-thresh",
            "event_type": "FAILED_PAYMENT",
            "amount": 6000.0,
            "currency": "INR",
            "failure_code": "bank_timeout",
            "customer_id": "cust-thresh",
            "customer_risk_score": 0.1,
            "customer_payment_history_success_rate": 0.9,
            "recovery_attempt_count": 0,
            "max_retries": 3,
            "has_active_action": False
        }
        
        result = graph.invoke(state_input)
        self.assertEqual(result["playbook_matches"][0]["playbook_id"], "PB-PAY-002")
        self.assertEqual(result["final_action"], "RETRY_PAYMENT")
        self.assertFalse(result["action_guard_result"]["approved"])

    def test_case_5_checkout_abandonment(self):
        matching_event = next(
            e for e in self.events 
            if e["event_type"] == "CHECKOUT_ABANDONMENT"
        )
        
        state_input = {
            "case_id": matching_event["id"],
            "event_id": matching_event["id"],
            "event_type": matching_event["event_type"],
            "amount": matching_event["amount"],
            "currency": matching_event["currency"],
            "failure_code": matching_event["failure_code"],
            "customer_id": matching_event["customer_id"],
            "customer_risk_score": matching_event["customer_history"]["risk_score"],
            "customer_payment_history_success_rate": matching_event["customer_history"]["success_rate"],
            "recovery_attempt_count": matching_event["recovery_context"]["attempt_number"],
            "max_retries": matching_event["recovery_context"]["max_retries"],
            "has_active_action": matching_event["recovery_context"]["has_active_action"]
        }
        
        result = graph.invoke(state_input)
        self.assertEqual(result["playbook_matches"][0]["playbook_id"], "PB-CHK-001")
        self.assertEqual(result["final_action"], "SEND_CHECKOUT_RECOVERY_MESSAGE")
        self.assertTrue(result["action_guard_result"]["approved"])

    def test_case_6_critic_rejects_and_replans(self):
        state_input = {
            "case_id": "case-critic-reject",
            "event_id": "event-critic-reject",
            "event_type": "FAILED_PAYMENT",
            "amount": 1000.0,
            "currency": "INR",
            "failure_code": "bank_timeout",
            "customer_id": "cust-critic-reject",
            "customer_risk_score": 0.75,
            "customer_payment_history_success_rate": 0.9,
            "recovery_attempt_count": 0,
            "max_retries": 3,
            "has_active_action": False
        }
        
        result = graph.invoke(state_input)
        self.assertEqual(result["final_action"], "ESCALATE_TO_HUMAN")
        self.assertEqual(result["action_guard_result"]["resulting_status"], "HUMAN_REVIEW")

    def test_case_7_subscription_failure_recovers(self):
        # 7. Subscription failure under retry limit (attempt 0 < max 3) gets approved for RETRY_SUBSCRIPTION
        state_input = {
            "case_id": "sub-case-success",
            "event_id": "sub-event-success",
            "event_type": "SUBSCRIPTION_FAILURE",
            "amount": 1200.0,
            "currency": "INR",
            "failure_code": "card_declined",
            "customer_id": "cust-sub",
            "customer_risk_score": 0.20,
            "customer_payment_history_success_rate": 0.95,
            "recovery_attempt_count": 0,
            "max_retries": 3,
            "has_active_action": False
        }
        result = graph.invoke(state_input)
        self.assertEqual(result["playbook_matches"][0]["playbook_id"], "PB-SUB-001")
        self.assertEqual(result["final_action"], "RETRY_SUBSCRIPTION")
        self.assertTrue(result["action_guard_result"]["approved"])

    def test_case_8_subscription_failure_blocked_over_limits(self):
        # 8. Subscription failure over retry limit (attempt 3 >= max 3) gets blocked by Action Guard
        state_input = {
            "case_id": "sub-case-blocked",
            "event_id": "sub-event-blocked",
            "event_type": "SUBSCRIPTION_FAILURE",
            "amount": 1200.0,
            "currency": "INR",
            "failure_code": "card_declined",
            "customer_id": "cust-sub",
            "customer_risk_score": 0.20,
            "customer_payment_history_success_rate": 0.95,
            "recovery_attempt_count": 3,
            "max_retries": 3,
            "has_active_action": False
        }
        result = graph.invoke(state_input)
        self.assertEqual(result["final_action"], "RETRY_SUBSCRIPTION")
        self.assertFalse(result["action_guard_result"]["approved"])

if __name__ == "__main__":
    unittest.main()
