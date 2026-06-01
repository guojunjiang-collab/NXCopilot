# -*- coding: utf-8 -*-
"""NXCopilot NX Engine — 正向设计构建器。"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional
from nx_engine.reader import FeatureType

logger = logging.getLogger("nxcopilot.nx_engine.forward_builder")


@dataclass
class FeatureSpec:
    feature_type: FeatureType
    name: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class ForwardResult:
    success: bool
    nxopen_code: str = ""
    feature_specs: list[FeatureSpec] = field(default_factory=list)
    message: str = ""


class ForwardBuilder:
    def build_from_specs(self, specs: list[FeatureSpec]) -> ForwardResult:
        if not specs:
            return ForwardResult(success=True, nxopen_code="# No features to create")
        blocks = [
            "# === NXCopilot 正向设计代码 ===",
            "import NXOpen", "",
            "session = NXOpen.Session.GetSession()",
            "work_part = session.Parts.Work", "",
        ]
        for spec in specs:
            blocks.append(f"# Create {spec.feature_type.value}: {spec.name}")
            blocks.append(f"# Parameters: {spec.parameters}")
            blocks.append("")
        blocks.extend(["work_part.Update()", ""])
        return ForwardResult(success=True, nxopen_code="\n".join(blocks), feature_specs=specs)

    def build_from_description(self, description: str) -> ForwardResult:
        specs = self._parse_description(description)
        if not specs:
            return ForwardResult(success=False, message="Could not parse description")
        return self.build_from_specs(specs)

    @staticmethod
    def _parse_description(description: str) -> list[FeatureSpec]:
        specs = []
        desc_lower = description.lower()
        m = re.search(r'(?:拉伸|extrude)\s*(\d+(?:\.\d+)?)', desc_lower)
        if m:
            specs.append(FeatureSpec(FeatureType.EXTRUDE, "EXTRUDE_NEW", {"end": m.group(1)}))
        m = re.search(r'(?:孔|hole).*?(?:直径|d)\s*[=: ]?\s*(\d+(?:\.\d+)?)', desc_lower)
        if m:
            specs.append(FeatureSpec(FeatureType.HOLE, "HOLE_NEW", {"diameter": m.group(1)}))
        m = re.search(r'(?:倒圆角|blend|fillet)\s*[rR]?\s*(\d+(?:\.\d+)?)', desc_lower)
        if m:
            specs.append(FeatureSpec(FeatureType.EDGE_BLEND, "BLEND_NEW", {"radius": m.group(1)}))
        m = re.search(r'(?:倒角|chamfer)\s*(\d+(?:\.\d+)?)', desc_lower)
        if m:
            specs.append(FeatureSpec(FeatureType.CHAMFER, "CHAMFER_NEW", {"distance": m.group(1)}))
        return specs
