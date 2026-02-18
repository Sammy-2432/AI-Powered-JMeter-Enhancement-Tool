from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class Failure:
    thread_name: str
    sampler_name: str
    label: str
    request_data: Optional[str]
    response_data: Optional[str]
    previous_response: Optional[str]
    previous_request: Optional[str]
    candidate_dynamic_fields: Optional[Dict[str, Any]] = None
