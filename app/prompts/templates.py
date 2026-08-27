# app/prompts/templates.py

DIAGNOSIS_PROMPT = """
Analyze the payment event data and diagnosis logs. Explain structural errors.
Output JSON only:
{
  "summary": "Detailed text summary",
  "confidence": 0.0 to 1.0,
  "reason": "Justification reasoning"
}
"""

POLICY_PROMPT = """
Validate transaction policy constraints. 
Output JSON only:
{
  "summary": "Detailed text summary",
  "confidence": 0.0 to 1.0,
  "reason": "Justification reasoning"
}
"""
