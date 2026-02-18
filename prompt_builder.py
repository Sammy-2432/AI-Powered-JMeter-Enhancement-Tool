from typing import Dict, Any

PROMPT_TEMPLATE = """
You are an expert JMeter test analyst. You will be provided a JSON payload with the following keys:
- failed_request: {failed_request}
- failed_response: {failed_response}
- candidate_dynamic_values: {candidates}

Return a strict JSON object with the following schema:
{
  "failure_category": "string",
  "correlation_issue": true|false,
  "recommended_extractor": {"type":"jsonpath|regex|xpath","expression":"string","source":"previous_response"},
  "assertion_improvements": ["suggestion strings"],
  "confidence_score": 0-1
}

If the response looks like an HTTP 500 with stacktrace, classify as "server_error" and set correlation_issue=false but provide hints.

Only return JSON. Do not include extra commentary.
"""


def build_prompt(failed_request: str, failed_response: str, candidates: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "failed_request": failed_request,
        "failed_response": failed_response,
        "candidate_dynamic_values": candidates
    }
