# -*- coding: utf-8 -*-
"""NXCopilot Agent — 会话管理器。"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class ConversationTurn:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent: str = ""

@dataclass
class Session:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    turns: list[ConversationTurn] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._active: Optional[Session] = None

    def create_session(self) -> Session:
        s = Session()
        self._sessions[s.session_id] = s
        self._active = s
        return s

    def get_active(self) -> Session:
        if not self._active: return self.create_session()
        return self._active

    def add_turn(self, role: str, content: str, intent: str = "") -> None:
        self.get_active().turns.append(ConversationTurn(role=role, content=content, intent=intent))

    def get_history(self, n: int = 20) -> list[dict]:
        return [{"role": t.role, "content": t.content} for t in self.get_active().turns[-n:]]

    def clear(self) -> None:
        if self._active: self._active.turns.clear()
