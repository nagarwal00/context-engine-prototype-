"""
LLM Client Interface (Section 3.2)
Provides standard-library-only HTTP client to communicate with LLM providers
(OpenAI-compatible, Anthropic, or Gemini) when configured via environment variables.
"""
import os
import json
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("CIF_LLM_PROVIDER", "openai").lower()
        self.api_key = os.getenv("CIF_LLM_API_KEY", "").strip()
        self.model = os.getenv("CIF_LLM_MODEL", "").strip()
        self.timeout = 30 # 30s timeout per Section 3.2

    @staticmethod
    def is_local_only() -> bool:
        return os.getenv("CIF_LOCAL_ONLY", "0").lower() in ("1", "true", "yes")

    def available(self) -> bool:
        """Returns True only if API key and model name are configured and local-only mode is not active."""
        if self.is_local_only():
            return False
        return bool(self.api_key and self.model)

    def complete_json(self, prompt: str, system_prompt: str = "You extract architectural decisions in strict JSON format.") -> Optional[str]:
        """Sends prompt and returns response string with exponential retry backoff."""
        if self.is_local_only() or not self.available():
            return None

        # Build request payload based on provider
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

        data = json.dumps(payload).encode("utf-8")
        retries = 2
        backoff = 1.0

        for attempt in range(retries + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                    choices = resp_json.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
            except urllib.error.HTTPError as e:
                # Do not log API key
                if attempt == retries or e.code in (400, 401, 403):
                    return None
                time.sleep(backoff)
                backoff *= 2.0
            except Exception:
                if attempt == retries:
                    return None
                time.sleep(backoff)
                backoff *= 2.0

        return None
