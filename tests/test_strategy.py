import unittest
from app.services.strategy_engine import RecoveryStrategyEngine

class TestRecoveryStrategyEngine(unittest.TestCase):

    def test_evaluate_candidates_low_risk(self):
        state = {
            "amount": 1000.00,
            "currency": "INR",
            "recovery_attempt_count": 0,
            "max_retries": 3,
            "customer_risk_score": 0.15,
            "customer_payment_history_success_rate": 0.90
        }

        ranked = RecoveryStrategyEngine.evaluate_candidates(state)
        self.assertTrue(len(ranked) > 0)
        
        # Verify first action type is RETRY_PAYMENT since it has highest probability/ERV
        self.assertEqual(ranked[0]["action_type"], "RETRY_PAYMENT")
        self.assertEqual(ranked[0]["confidence"], 0.72)  # 0.90 * 0.8
        self.assertEqual(ranked[0]["expected_recovery_value"], 720.00)

    def test_evaluate_candidates_policy_blocked(self):
        state = {
            "amount": 1000.00,
            "currency": "INR",
            "recovery_attempt_count": 3,  # Max retries reached!
            "max_retries": 3,
            "customer_risk_score": 0.15,
            "customer_payment_history_success_rate": 0.90
        }

        ranked = RecoveryStrategyEngine.evaluate_candidates(state)
        
        # RETRY_PAYMENT and RETRY_SUBSCRIPTION must be heavily penalized!
        retry_pay = next(r for r in ranked if r["action_type"] == "RETRY_PAYMENT")
        retry_sub = next(r for r in ranked if r["action_type"] == "RETRY_SUBSCRIPTION")
        self.assertTrue(retry_pay["confidence"] < 0.1)
        self.assertTrue(retry_sub["confidence"] < 0.1)

    def test_evaluate_candidates_high_risk_blocked(self):
        state = {
            "amount": 1000.00,
            "currency": "INR",
            "recovery_attempt_count": 0,
            "max_retries": 3,
            "customer_risk_score": 0.85,  # High risk score (> 0.6)
            "customer_payment_history_success_rate": 0.90
        }

        ranked = RecoveryStrategyEngine.evaluate_candidates(state)

        # Retry actions must be penalized by Risk Filter!
        retry_pay = next(r for r in ranked if r["action_type"] == "RETRY_PAYMENT")
        retry_sub = next(r for r in ranked if r["action_type"] == "RETRY_SUBSCRIPTION")
        self.assertTrue(retry_pay["confidence"] < 0.2)
        self.assertTrue(retry_sub["confidence"] < 0.2)

    def test_evaluate_candidates_failure_reason_affects_strategy(self):
        state = {
            "amount": 1000.00,
            "currency": "INR",
            "recovery_attempt_count": 0,
            "max_retries": 3,
            "customer_risk_score": 0.15,
            "customer_payment_history_success_rate": 0.90,
            "failure_code": "insufficient_funds"
        }
        ranked = RecoveryStrategyEngine.evaluate_candidates(state)
        # RETRY_PAYMENT is penalized, SEND_PAYMENT_REMINDER is boosted
        retry_pay = next(r for r in ranked if r["action_type"] == "RETRY_PAYMENT")
        reminder = next(r for r in ranked if r["action_type"] == "SEND_PAYMENT_REMINDER")
        self.assertTrue(reminder["expected_recovery_value"] > retry_pay["expected_recovery_value"])

    def test_evaluate_candidates_failed_actions_strategy_change(self):
        state = {
            "amount": 1000.00,
            "currency": "INR",
            "recovery_attempt_count": 1,
            "max_retries": 3,
            "customer_risk_score": 0.15,
            "customer_payment_history_success_rate": 0.90,
            "failed_actions": ["RETRY_PAYMENT"]
        }
        ranked = RecoveryStrategyEngine.evaluate_candidates(state)
        # RETRY_PAYMENT should drop in ranking because of previous failure
        retry_pay = next(r for r in ranked if r["action_type"] == "RETRY_PAYMENT")
        self.assertTrue(retry_pay["confidence"] < 0.15)

if __name__ == "__main__":
    unittest.main()
