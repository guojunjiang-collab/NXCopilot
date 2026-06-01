# -*- coding: utf-8 -*-
"""NXCopilot UI — Agent 通信客户端。"""
from __future__ import annotations
from typing import Any, Optional
import httpx

class AgentClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8757"):
        self._url = base_url.rstrip("/")

    def check_health(self) -> tuple[bool, dict]:
        try:
            with httpx.Client(timeout=5) as c:
                r = c.get(f"{self._url}/health"); r.raise_for_status()
                return True, r.json()
        except Exception as e: return False, {"error": str(e)}

    def get_model(self) -> Optional[dict]:
        try:
            with httpx.Client(timeout=10) as c:
                r = c.get(f"{self._url}/model"); r.raise_for_status()
                return r.json()
        except: return None

    def send_message(self, msg: str) -> dict:
        try:
            with httpx.Client(timeout=60) as c:
                r = c.post(f"{self._url}/chat", json={"message": msg})
                r.raise_for_status(); return r.json()
        except Exception as e: return {"reply": f"[Error] {e}"}

    def update_llm_settings(self, key: str, model: str, url: str) -> tuple[bool, str]:
        try:
            with httpx.Client(timeout=15) as c:
                r = c.post(f"{self._url}/settings/llm", json={"api_key":key,"model":model,"base_url":url})
                r.raise_for_status(); d = r.json()
                return d.get("success",False), d.get("message","")
        except Exception as e: return False, str(e)
