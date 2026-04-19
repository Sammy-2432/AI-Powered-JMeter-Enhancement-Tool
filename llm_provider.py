"""
Unified LLM provider interface supporting multiple APIs.
"""
import anthropic
import openai
import google.generativeai as genai
from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    def chat(self, system_prompt: str, messages: list, max_tokens: int) -> str:
        """Send a chat request and return the response text."""
        pass


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def chat(self, system_prompt: str, messages: list, max_tokens: int) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        return resp.content[0].text


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4-turbo"  # or "gpt-4", "gpt-3.5-turbo"
    
    def chat(self, system_prompt: str, messages: list, max_tokens: int) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        return resp.choices[0].message.content


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")
    
    def chat(self, system_prompt: str, messages: list, max_tokens: int) -> str:
        # Convert OpenAI format to Gemini format
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_messages.append({"role": role, "parts": [msg["content"]]})
        
        resp = self.model.generate_content(
            gemini_messages,
            generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens)
        )
        return resp.text


def get_llm_provider(provider_name: str, api_key: str) -> LLMProvider:
    """Factory function to get the appropriate LLM provider."""
    providers = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(providers.keys())}")
    
    return providers[provider_name](api_key)
