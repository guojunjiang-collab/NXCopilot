# -*- coding: utf-8 -*-
"""NXCopilot NX Bridge — 代码执行器（重试/超时/错误分类）。"""

from __future__ import annotations
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

logger = logging.getLogger("nxcopilot.nx_bridge.executor")


class ErrorType(Enum):
    TIMEOUT = auto()
    NXOPEN_ERROR = auto()
    SYNTAX_ERROR = auto()
    FEATURE_NOT_FOUND = auto()
    PERMANENT = auto()


@dataclass
class ExecutionResult:
    success: bool
    output: str = ""
    error: str = ""
    retry_attempts: int = 0
    duration_ms: float = 0.0
    error_type: Optional[ErrorType] = None


class NXExecutor:
    MAX_RETRIES = 3

    def __init__(self, nx_session=None):
        self._session = nx_session

    def set_session(self, nx_session) -> None:
        self._session = nx_session

    def execute(self, code: str) -> ExecutionResult:
        if self._session is None:
            return ExecutionResult(success=False, error="No NX session", error_type=ErrorType.PERMANENT)

        start = time.monotonic()
        for attempt in range(self.MAX_RETRIES):
            try:
                import NXOpen
                exec_globals = {
                    "session": self._session,
                    "work_part": self._session.Parts.Work,
                    "NXOpen": NXOpen,
                }
                exec(code, exec_globals, {})
                elapsed = (time.monotonic() - start) * 1000
                return ExecutionResult(success=True, duration_ms=elapsed, retry_attempts=attempt)
            except SyntaxError as e:
                return ExecutionResult(success=False, error=f"SyntaxError: {e}",
                    error_type=ErrorType.SYNTAX_ERROR, duration_ms=(time.monotonic()-start)*1000)
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(0.5 * (attempt + 1))

        return ExecutionResult(success=False, error="Max retries exceeded",
            error_type=ErrorType.NXOPEN_ERROR, duration_ms=(time.monotonic()-start)*1000,
            retry_attempts=self.MAX_RETRIES)

    async def execute_async(self, code: str) -> ExecutionResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, code)
