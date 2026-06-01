# -*- coding: utf-8 -*-
"""NXCopilot Agent — 任务编排核心（意图路由 + 读取/分析/执行）。"""

from __future__ import annotations
import asyncio
import json
import logging
import re
from typing import Any, Optional

from nx_engine.reader import PartReader, FeatureTreeSnapshot, DeltaDetector
from nx_engine.converter import feature_tree_to_nxopen, feature_tree_to_nl, get_editable_parameters
from nx_engine.editor import NXEditor, EditAction, EditActionType
from nx_engine.dependency import DependencyGraph, EditValidator
from nx_engine.validator import NXCodeValidator
from nx_engine.forward_builder import ForwardBuilder
from nx_engine.expression import ExpressionManager
from llm.client import LLMClient, LLMConfig, LLMMessage
from llm.prompts import SYSTEM_UNDERSTAND_MODEL, SYSTEM_NL_TO_EDIT, SYSTEM_DESIGN_PLANNING
from nx_bridge.session import NXSession
from nx_bridge.executor import NXExecutor

logger = logging.getLogger("nxcopilot.orchestrator")

SYSTEM_GENERAL = (
    "你是 NXCopilot，Siemens NX AI 设计助手。\n"
    "帮助用户讨论 CAD 设计、解释 NX 功能、规划零件设计、生成 NXOpen 代码。\n"
    "当前 NX 未连接，用中文回答。"
)


class NXCopilotOrchestrator:
    def __init__(self):
        self._nx_session = NXSession()
        self._executor = NXExecutor()
        self._part_reader = PartReader()
        self._nx_editor = NXEditor()
        self._validator = NXCodeValidator()
        self._forward_builder = ForwardBuilder()
        self._expr_manager = ExpressionManager()
        self._llm_client: Optional[LLMClient] = None
        self._current_snapshot: Optional[FeatureTreeSnapshot] = None
        self._connected = False
        self._llm_ready = False

    def connect_nx(self) -> bool:
        self._connected = self._nx_session.connect()
        if self._connected:
            self._executor.set_session(self._nx_session.session)
            self._part_reader._connected = True
            self._part_reader._session = self._nx_session.session
            self._expr_manager.set_part(self._nx_session.work_part)
        return self._connected

    def is_connected(self) -> bool:
        return self._connected and self._nx_session.is_connected()

    def set_llm_config(self, config: LLMConfig) -> None:
        self._llm_client = LLMClient(config)
        self._llm_ready = True

    async def handle_message(self, user_input: str) -> dict[str, Any]:
        intent = self._classify_intent(user_input)
        logger.info(f"Intent: {intent}")

        if intent == "general":
            return await self._handle_general(user_input)
        elif intent == "forward":
            return await self._handle_forward(user_input)
        elif intent == "nx_op":
            return await self._handle_nx_op(user_input)
        return {"intent": "general", "reply": "无法识别意图。"}

    _FORWARD_KW = ["创建","新建","画","拉伸","打孔","倒角","倒圆角","create","extrude","hole","chamfer","blend","fillet"]
    _NX_OP_KW = ["修改","改","删除","抑制","阵列","镜像","参数","尺寸","modify","delete","suppress","pattern","mirror","特征树","读取","分析"]

    def _classify_intent(self, text: str) -> str:
        t = text.lower()
        for kw in self._FORWARD_KW:
            if kw in t: return "forward"
        for kw in self._NX_OP_KW:
            if kw in t: return "nx_op"
        return "general"

    async def _handle_general(self, user_input: str) -> dict:
        if not self._llm_ready:
            return {"intent": "general", "reply": "LLM 未配置，请先设置 API Key。"}
        msgs = [LLMMessage("system", SYSTEM_GENERAL), LLMMessage("user", user_input)]
        resp = await self._llm_client.call(msgs)
        return {"intent": "general", "reply": resp.content}

    async def _handle_forward(self, user_input: str) -> dict:
        if not self._llm_ready:
            return {"intent": "forward", "reply": "LLM 未配置。"}
        model_ctx = ""
        if self.is_connected():
            snap = self._read_model()
            if snap: model_ctx = feature_tree_to_nxopen(snap)
        prompt = f"用户需求: {user_input}\n\n当前模型:\n{model_ctx or '(无)'}\n\n生成 NXOpen Python 创建代码。"
        msgs = [LLMMessage("system", SYSTEM_DESIGN_PLANNING), LLMMessage("user", prompt)]
        resp = await self._llm_client.call(msgs)
        code = self._extract_code(resp.content)
        result = {"intent": "forward", "reply": resp.content, "nxopen_code": code}
        if code and self.is_connected():
            er = self._executor.execute(code)
            result["execution_result"] = {"success": er.success, "error": er.error, "ms": er.duration_ms}
            if er.success: result["feature_tree"] = self._get_tree_summary()
        return result

    async def _handle_nx_op(self, user_input: str) -> dict:
        if not self.is_connected():
            return {"intent": "nx_op", "reply": "NX 未连接。"}
        if not self._llm_ready:
            return {"intent": "nx_op", "reply": "LLM 未配置。"}
        snap = self._read_model()
        if not snap:
            return {"intent": "nx_op", "reply": "无法读取模型。"}
        nxopen_repr = feature_tree_to_nxopen(snap)
        params = get_editable_parameters(snap)
        prompt = (
            f"=== 特征树 ===\n{nxopen_repr}\n\n"
            f"=== 可编辑参数 ===\n{json.dumps(params, ensure_ascii=False, indent=2)}\n\n"
            f"=== 用户需求 ===\n{user_input}\n\n"
            "生成 NXOpen Python 局部修改代码。"
        )
        msgs = [LLMMessage("system", SYSTEM_NL_TO_EDIT), LLMMessage("user", prompt)]
        resp = await self._llm_client.call(msgs)
        code = self._extract_code(resp.content)
        val = self._validator.validate(code, [f.name for f in snap.features])
        result = {"intent": "nx_op", "reply": resp.content, "nxopen_code": code,
                  "validation": {"valid": val.valid, "errors": val.errors}}
        if code and val.valid:
            er = self._executor.execute(code)
            result["execution_result"] = {"success": er.success, "error": er.error, "ms": er.duration_ms}
            if er.success:
                new_snap = self._read_model()
                if new_snap:
                    delta = DeltaDetector().detect(snap, new_snap)
                    result["delta"] = {"added": [f.name for f in delta.added], "modified": [m["name"] for m in delta.modified], "removed": delta.removed}
                    result["feature_tree"] = self._get_tree_summary()
        return result

    def _read_model(self) -> Optional[FeatureTreeSnapshot]:
        snap = self._part_reader.read_feature_tree()
        if snap: self._current_snapshot = snap
        return snap

    def _get_tree_summary(self) -> dict:
        s = self._current_snapshot
        if not s: return {}
        return {
            "part_name": s.part_name, "feature_count": s.feature_count,
            "features": [{"name": f.name, "type": f.feature_type.value, "params": f.parameters} for f in s.features],
            "expressions": s.expressions,
        }

    @staticmethod
    def _extract_code(text: str) -> str:
        for pattern in [r"```python\s*\n(.*?)```", r"```nxopen\s*\n(.*?)```", r"```\s*\n(.*?)```"]:
            m = re.search(pattern, text, re.DOTALL)
            if m: return m.group(1).strip()
        return ""
