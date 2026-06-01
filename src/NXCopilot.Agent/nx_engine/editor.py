# -*- coding: utf-8 -*-
"""NXCopilot NX Engine — 局部修改指令生成器。"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional

logger = logging.getLogger("nxcopilot.nx_engine.editor")


class EditActionType(Enum):
    MODIFY_PARAM = auto()
    INSERT_AFTER = auto()
    INSERT_BEFORE = auto()
    REMOVE_FEATURE = auto()
    DUPLICATE_MODIFY = auto()
    SUPPRESS = auto()
    UNSUPPRESS = auto()
    RENAME = auto()


@dataclass
class EditAction:
    action_type: EditActionType
    feature_name: str
    param_name: Optional[str] = None
    new_value: Optional[Any] = None
    anchor: Optional[str] = None
    source: Optional[str] = None
    new_params: dict[str, Any] = field(default_factory=dict)
    new_name: Optional[str] = None


@dataclass
class EditResult:
    success: bool
    nxopen_code: str = ""
    message: str = ""
    affected_features: list[str] = field(default_factory=list)


class NXEditor:
    """NXOpen 局部修改指令生成器 — 优先通过 Expression 修改参数。"""

    def generate(self, action: EditAction) -> EditResult:
        try:
            handlers = {
                EditActionType.MODIFY_PARAM: self._gen_modify_param,
                EditActionType.REMOVE_FEATURE: self._gen_remove_feature,
                EditActionType.INSERT_AFTER: self._gen_insert_after,
                EditActionType.INSERT_BEFORE: self._gen_insert_before,
                EditActionType.SUPPRESS: lambda a: self._gen_suppress(a, True),
                EditActionType.UNSUPPRESS: lambda a: self._gen_suppress(a, False),
                EditActionType.RENAME: self._gen_rename,
                EditActionType.DUPLICATE_MODIFY: self._gen_duplicate,
            }
            handler = handlers.get(action.action_type)
            if handler is None:
                return EditResult(success=False, message=f"Unknown action: {action.action_type}")
            return handler(action)
        except Exception as e:
            return EditResult(success=False, message=str(e))

    def generate_batch(self, actions: list[EditAction]) -> EditResult:
        if not actions:
            return EditResult(success=True, nxopen_code="# No actions")
        blocks = [
            "# === NXCopilot 局部修改代码 ===",
            "import NXOpen", "",
            "session = NXOpen.Session.GetSession()",
            "work_part = session.Parts.Work", "",
        ]
        affected = []
        for i, action in enumerate(actions, 1):
            r = self.generate(action)
            blocks.append(f"# --- Action {i}: {action.action_type.name} ---")
            blocks.append(r.nxopen_code if r.success else f"# FAILED: {r.message}")
            affected.extend(r.affected_features)
        blocks.extend(["", "work_part.Update()"])
        return EditResult(success=True, nxopen_code="\n".join(blocks), affected_features=affected)

    def _gen_modify_param(self, a: EditAction) -> EditResult:
        code = (
            f"target_expr = work_part.Expressions.FindObject(\"{a.param_name}\")\n"
            f"unit_mm = work_part.UnitCollection.FindObject(\"MilliMeter\")\n"
            f"work_part.Expressions.EditWithUnits(target_expr, unit_mm, str({a.new_value}))\n"
        )
        return EditResult(success=True, nxopen_code=code, affected_features=[a.feature_name])

    def _gen_remove_feature(self, a: EditAction) -> EditResult:
        code = (
            f"feat = work_part.Features.FindObject(\"{a.feature_name}\")\n"
            f"if feat: work_part.Features.DeleteFeature(feat)\n"
        )
        return EditResult(success=True, nxopen_code=code, affected_features=[a.feature_name])

    def _gen_insert_after(self, a: EditAction) -> EditResult:
        code = f"# Insert after {a.anchor} (TODO: implement based on feature type)\n"
        return EditResult(success=True, nxopen_code=code, affected_features=[a.anchor or ""])

    def _gen_insert_before(self, a: EditAction) -> EditResult:
        code = f"# Insert before {a.anchor} (TODO: implement based on feature type)\n"
        return EditResult(success=True, nxopen_code=code, affected_features=[a.anchor or ""])

    def _gen_suppress(self, a: EditAction, val: bool) -> EditResult:
        code = (
            f"feat = work_part.Features.FindObject(\"{a.feature_name}\")\n"
            f"if feat: feat.Suppressed = {val}\n"
        )
        return EditResult(success=True, nxopen_code=code, affected_features=[a.feature_name])

    def _gen_rename(self, a: EditAction) -> EditResult:
        code = (
            f"feat = work_part.Features.FindObject(\"{a.feature_name}\")\n"
            f"if feat: feat.Name = \"{a.new_name}\"\n"
        )
        return EditResult(success=True, nxopen_code=code, affected_features=[a.feature_name])

    def _gen_duplicate(self, a: EditAction) -> EditResult:
        code = f"# Duplicate {a.source} (TODO: implement)\n"
        return EditResult(success=True, nxopen_code=code, affected_features=[a.source or ""])


def list_features_in_order(snapshot) -> list[str]:
    return [f.name for f in snapshot.features]
