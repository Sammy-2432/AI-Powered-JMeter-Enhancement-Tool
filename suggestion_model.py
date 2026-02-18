from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class Suggestion:
    failure_category: Optional[str]
    correlation_issue: Optional[bool]
    recommended_extractor: Optional[Dict[str, Any]]
    assertion_improvements: Optional[List[str]]
    confidence_score: Optional[float]

    @staticmethod
    def from_ai(obj: Dict[str, Any]):
        if not obj:
            return None
        return Suggestion(
            failure_category=obj.get('failure_category'),
            correlation_issue=obj.get('correlation_issue'),
            recommended_extractor=obj.get('recommended_extractor'),
            assertion_improvements=obj.get('assertion_improvements'),
            confidence_score=obj.get('confidence_score')
        )
