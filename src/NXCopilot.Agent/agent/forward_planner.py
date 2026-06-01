# -*- coding: utf-8 -*-
"""NXCopilot Agent — 正向设计规划器（LLM 桥接 ForwardBuilder）。"""
from __future__ import annotations
import json, logging
from dataclasses import dataclass, field
from typing import Optional
from nx_engine.forward_builder import ForwardBuilder, FeatureSpec, ForwardResult
from nx_engine.reader import FeatureType
from llm.client import LLMClient, LLMMessage

logger = logging.getLogger("nxcopilot.agent.forward_planner")

@dataclass
class ForwardPlanningResult:
    success: bool
    feature_specs: list[FeatureSpec] = field(default_factory=list)
    nxopen_code: str = ""
    message: str = ""

class ForwardPlanner:
    def __init__(self, llm: Optional[LLMClient] = None):
        self._llm = llm
        self._builder = ForwardBuilder()

    async def plan_from_llm(self, user_input: str, ctx: str = "") -> ForwardPlanningResult:
        if not self._llm:
            return ForwardPlanningResult(success=False, message="LLM not configured")
        prompt = f"用户需求: {user_input}\n\n上下文:\n{ctx or '(无)'}\n\n输出 JSON 格式的特征规格。"
        msgs = [LLMMessage("system", "将需求转为 JSON 特征规格。"), LLMMessage("user", prompt)]
        resp = await self._llm.call(msgs)
        try:
            data = json.loads(resp.content)
            specs = [FeatureSpec(FeatureType(s.get("feature_type","Unknown")), s.get("name",""), s.get("parameters",{})) for s in data.get("features",[])]
            r = self._builder.build_from_specs(specs)
            return ForwardPlanningResult(success=r.success, feature_specs=specs, nxopen_code=r.nxopen_code)
        except Exception as e:
            return ForwardPlanningResult(success=False, message=str(e))

    def plan_from_description(self, desc: str) -> ForwardPlanningResult:
        r = self._builder.build_from_description(desc)
        return ForwardPlanningResult(success=r.success, feature_specs=r.feature_specs, nxopen_code=r.nxopen_code)
