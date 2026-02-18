import json
import re
from typing import Dict, Any
from utils.logger import setup_logger

logger = setup_logger("heuristic_engine")

DYNAMIC_KEYS = ['id','token','session','auth','csrf','key','reference','number']

class HeuristicEngine:
    def extract_candidates(self, previous_response: str, failed_request: str) -> Dict[str, Any]:
        """
        Simple heuristic extraction:
        - Try parse JSON
        - Extract keys that contain dynamic hints
        - Keep values with length>8 and alphanumeric
        - Cross-check presence in failed_request
        - Limit to 10
        """
        if not previous_response:
            return {}

        candidates = {}
        try:
            obj = json.loads(previous_response)
        except Exception:
            # Try find JSON snippet inside
            m = re.search(r"\{.*\}", previous_response, re.S)
            if m:
                try:
                    obj = json.loads(m.group(0))
                except Exception:
                    obj = {}
            else:
                obj = {}

        def walk(o, path=''):
            if isinstance(o, dict):
                for k, v in o.items():
                    key_lower = k.lower()
                    full_key = f"{path}.{k}" if path else k
                    if any(token in key_lower for token in DYNAMIC_KEYS):
                        if isinstance(v, str) and len(v) > 8 and re.search(r"[A-Za-z0-9]{8,}", v):
                            if str(v) in (failed_request or ""):
                                candidates[full_key] = v
                            else:
                                # still include; will filter later
                                candidates[full_key] = v
                    # Recurse
                    walk(v, full_key)
            elif isinstance(o, list):
                for idx, item in enumerate(o):
                    walk(item, f"{path}[{idx}]")

        walk(obj)

        # Filter only those that appear in failed_request
        filtered = {k:v for k,v in list(candidates.items())[:50] if str(v) in (failed_request or "")}
        # If none appear, fallback to top candidates
        if not filtered:
            items = list(candidates.items())[:10]
            filtered = dict(items)
        else:
            # limit
            filtered = dict(list(filtered.items())[:10])

        logger.info("Heuristic candidates: %s", list(filtered.keys()))
        return filtered
