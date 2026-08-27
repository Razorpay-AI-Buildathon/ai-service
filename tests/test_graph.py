import unittest
from app.graph import graph
from app.guardrails.engine import GuardrailsEngine

class TestRecoveryCouncilWorkflow(unittest.TestCase):
    
    def test_full_council_execution_flow(self):
        # Input state context representing a standard failure
        initial_state = {
            "case_id": "test-case-123",
            "event_id": "test-event-456",
            "event_type": "FAILED_PAYMENT",
            "amount": 250.00,
            "failure_code": "insufficient_funds",
            "customer_id": "cust-888",
            "customer_risk_score": 0.1,
            "customer_payment_history_success_rate": 0.95,
            "recovery_attempt_count": 0,
            "max_retries": 3,
            "retry_count": 0
        }
        
        # Invoke the graph workflow
        result = graph.invoke(initial_state)
        
        self.assertEqual(result["current_node"], "handoff")
        self.assertEqual(result["final_action"], "SEND_PAYMENT_REMINDER")
        self.assertEqual(result["critic_decision"], "ACCEPT")
        self.assertFalse(result["replan_required"])

    def test_parallel_nodes_execution_integrity(self):
        # Asserts parallel convergence join logic. When graph executes planner node, 
        # it MUST contain inputs aggregated from diagnosis, policy, and risk nodes.
        initial_state = {
            "case_id": "test-case-123",
            "event_id": "test-event-456",
            "event_type": "FAILED_PAYMENT",
            "amount": 250.00,
            "failure_code": "insufficient_funds",
            "customer_id": "cust-888",
            "customer_risk_score": 0.1,
            "customer_payment_history_success_rate": 0.95,
            "recovery_attempt_count": 0,
            "max_retries": 3,
            "retry_count": 0
        }
        
        result = graph.invoke(initial_state)
        
        # Verify inputs from all parallel agents exist in the state before finalizing
        self.assertIn("diagnosis", result)
        self.assertIn("policy_status", result)
        self.assertIn("risk_level", result)
        self.assertIsNotNone(result["diagnosis"])
        self.assertIsNotNone(result["policy_status"])
        self.assertIsNotNone(result["risk_level"])

    def test_guardrails_engine_passes_valid_state(self):
        state = {
            "case_id": "test-case-123",
            "event_id": "test-event-456",
            "event_type": "FAILED_PAYMENT",
            "amount": 100.0,
            "proposed_action": "RETRY_PAYMENT",
            "planner_confidence": 0.90,
            "risk_level": "LOW",
            "diagnosis": "network_error failure diagnosed",
            "failure_code": "network_error"
        }
        res = GuardrailsEngine.evaluate(state)
        self.assertEqual(res["guardrail_status"], "PASSED")
        self.assertEqual(len(res["guardrail_violations"]), 0)

    def test_guardrails_engine_blocks_missing_inputs(self):
        # Missing required parameter "amount"
        state = {
            "case_id": "test-case-123",
            "event_id": "test-event-456",
            "event_type": "FAILED_PAYMENT"
        }
        res = GuardrailsEngine.evaluate(state)
        self.assertEqual(res["guardrail_status"], "FAILED")
        self.assertTrue(any("Missing required state input parameter" in v for v in res["guardrail_violations"]))

if __name__ == "__main__":
    unittest.main()
