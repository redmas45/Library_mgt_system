from typing import List, Dict, Optional
from app.utils.logger import logger


class OpenAILLM:
    """Wrapper around OpenAI's chat completion API. Supports custom base URLs for providers like Groq."""

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b", base_url: str = ""):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or None
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                client_kwargs = {"api_key": self.api_key}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                self._client = OpenAI(**client_kwargs)
                provider = self.base_url or "api.openai.com"
                logger.info(f"LLM client initialized (model: {self.model}, provider: {provider})")
            except ImportError:
                raise ImportError("openai package is required. Install with: pip install openai")
        return self._client

    def chat(
        self, messages: List[Dict[str, str]],
        temperature: float = 0.7, max_tokens: int = 1024,
    ) -> Dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages,
                temperature=temperature, max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            logger.info(f"LLM response: {len(content)} chars, {tokens_used} tokens")
            return {"content": content, "tokens_used": tokens_used}
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def generate(
        self, system_prompt: str, user_prompt: str,
        temperature: float = 0.7, max_tokens: int = 1024,
    ) -> Dict:
        """Convenience method: system + user prompt in one call."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens)
