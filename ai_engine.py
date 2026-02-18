import os
import json
import time
from typing import Dict, Any
from dotenv import load_dotenv
import openai
from utils.logger import setup_logger

load_dotenv()
logger = setup_logger("ai_engine")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

class AIEngine:
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or OPENAI_KEY
        self.model = model
        if not self.api_key:
            raise RuntimeError("OpenAI API key not set. Provide OPENAI_API_KEY in .env")
        openai.api_key = self.api_key

    def analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send structured prompt to OpenAI and expect structured JSON in return.
        Handle transient errors with simple retry.
        """
        prompt = json.dumps(payload)
        tries = 0
        while tries < 3:
            try:
                resp = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role":"user","content":prompt}],
                    max_tokens=800,
                    temperature=0
                )
                text = resp.choices[0].message['content']
                # Try parse JSON
                try:
                    return json.loads(text)
                except Exception:
                    logger.warning("AI returned non-JSON, attempting to extract JSON substring")
                    import re
                    m = re.search(r"\{.*\}", text, re.S)
                    if m:
                        return json.loads(m.group(0))
                    else:
                        return {"error":"non_json_response","raw":text}
            except Exception as e:
                logger.exception("OpenAI call failed, retrying...")
                tries += 1
                time.sleep(2 ** tries)
        raise RuntimeError("OpenAI API failed after retries")
