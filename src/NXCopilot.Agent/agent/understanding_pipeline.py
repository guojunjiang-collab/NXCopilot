# -*- coding: utf-8 -*-
"""NXCopilot Agent — 逆向理解管道。"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional
from nx_engine.reader import PartReader, FeatureTreeSnapshot
from nx_engine.converter import feature_tree_to_nxopen, feature_tree_to_nl
from llm.client import LLMClient, LLMMessage

logger = logging.getLogger("nxcopilot.agent.understanding_pipeline")

@dataclass
class UnderstandingResult:
    success: bool
    summary: str = ""
    nxopen_repr: str = ""

class UnderstandingPipeline:
    def __init__(self, reader: PartReader, llm: Optional[LLMClient] = None):
        self._reader = reader
        self._llm = llm

    async def understand(self, question: str = "") -> UnderstandingResult:
        snap = self._reader.read_feature_tree()
        if not snap: return UnderstandingResult(success=False, summary="Cannot read NX model")
        nxopen_repr = feature_tree_to_nxopen(snap)
        nl = feature_tree_to_nl(snap)
        if not self._llm: return UnderstandingResult(success=True, summary=nl, nxopen_repr=nxopen_repr)
        prompt = f"=== 模型 ===\n{nxopen_repr}\n\n问题: {question or '分析设计意图'}"
        msgs = [LLMMessage("system", "你是 NX CAD 分析专家。"), LLMMessage("user", prompt)]
        resp = await self._llm.call(msgs)
        return UnderstandingResult(success=True, summary=resp.content, nxopen_repr=nxopen_repr)
