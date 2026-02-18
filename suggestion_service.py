from core.ai_engine import AIEngine
from core.heuristic_engine import HeuristicEngine
from services.prompt_builder import build_prompt
from models.suggestion_model import Suggestion
from utils.logger import setup_logger

logger = setup_logger("suggestion_service")

class SuggestionService:
    def __init__(self):
        self.ai = AIEngine()
        self.heuristic = HeuristicEngine()

    def analyze_failure(self, failure):
        # Extract candidates
        candidates = self.heuristic.extract_candidates(failure.previous_response, failure.request_data)
        prompt = build_prompt(failure.request_data or "", failure.response_data or "", candidates)
        try:
            ai_result = self.ai.analyze(prompt)
        except Exception as e:
            logger.exception("AI analyze failed")
            return None

        suggestion = Suggestion.from_ai(ai_result)
        return suggestion
