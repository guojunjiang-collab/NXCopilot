# -*- coding: utf-8 -*-
"""NXCopilot LLM — 统一 API 客户端（DeepSeek / OpenRouter / OpenAI）。"""
from __future__ import annotations
import json, logging, os
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger("nxcopilot.llm")

@dataclass
class LLMConfig:
    api_key: str = ""
    model: str = "deepseek/deepseek-v4-pro"
    base_url: str = "https://api.deepseek.com/v1"
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "LLMConfig":
        from dotenv import load_dotenv
        load_dotenv()
        return cls(
            api_key=os.getenv("LLM_API_KEY", ""),
            model=os.getenv("LLM_MODEL", "deepseek/deepseek-v4-pro"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
        )

@dataclass
class LLMMessage:
    role: str
    content: str

@dataclass
class LLMResponse:
    content: str
    raw: Optional[dict] = None

class LLMClient:
    def __init__(self, config: LLMConfig):
        self._config = config
        self._url = config.base_url.rstrip("/") + "/chat/completions"

    async def call(self, messages: list[LLMMessage]) -> LLMResponse:
        import httpx
        headers = {"Authorization": f"Bearer {self._config.api_key}", "Content-Type": "application/json"}
        payload = {"model": self._config.model, "messages": [{"role":m.role,"content":m.content} for m in messages],
                   "max_tokens": self._config.max_tokens, "temperature": self._config.temperature}
        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as c:
                r = await c.post(self._url, json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
            return LLMResponse(content=data["choices"][0]["message"]["content"], raw=data)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return LLMResponse(content=f"[ERROR] {e}")

    async def call_structured(self, messages: list[LLMMessage], schema: dict) -> LLMResponse:
        enhanced = list(messages)
        schema_instr = f"\n\nJSON Schema:\n{json.dumps(schema, ensure_ascii=False, indent=2)}"
        if enhanced and enhanced[0].role == "system":
            enhanced[0] = LLMMessage("system", enhanced[0].content + schema_instr)
        resp = await self.call(enhanced)
        try:
            json.loads(resp.content)
            return resp
        except json.JSONDecodeError:
            import re
            m = re.search(r"\{.*\}", resp.content, re.DOTALL)
            if m: return LLMResponse(content=m.group(0), raw=resp.raw)
            return resp

    def test_connection(self) -> tuple[bool, str]:
        import httpx
        headers = {"Authorization": f"Bearer {self._config.api_key}", "Content-Type": "application/json"}
        payload = {"model": self._config.model, "messages": [{"role":"user","content":"ping"}], "max_tokens":10}
        try:
            with httpx.Client(timeout=15) as c:
                r = c.post(self._url, json=payload, headers=headers)
                r.raise_for_status()
                return True, f"OK ({r.status_code})"
        except Exception as e:
            return False, str(e)
