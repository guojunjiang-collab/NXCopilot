# -*- coding: utf-8 -*-
"""
NXCopilot NX Engine — 特征树转 NXOpen Python 代码（仅供 LLM 分析）。
"""

from __future__ import annotations
import logging
from nx_engine.reader import FeatureTreeSnapshot, FeatureNode, FeatureType

logger = logging.getLogger("nxcopilot.nx_engine.converter")


def feature_tree_to_nxopen(snapshot: FeatureTreeSnapshot) -> str:
    """将特征树快照转换为 NXOpen Python 代码（仅供 LLM 阅读）。"""
    if not snapshot or not snapshot.features:
        return f"# Empty part: {snapshot.part_name if snapshot else '(none)'}"

    lines = []
    lines.append(f"# ====== Feature Tree: {snapshot.part_name} ({snapshot.feature_count} features) ======")
    lines.append("# For analysis only, do not execute")
    lines.append("")

    if snapshot.expressions:
        lines.append("# --- Global Expressions ---")
        for name, value in sorted(snapshot.expressions.items()):
            lines.append(f"#   {name} = {value}")
        lines.append("")

    if snapshot.body_names:
        lines.append(f"# --- Bodies: {', '.join(snapshot.body_names)} ---")
        lines.append("")

    for i, feat in enumerate(snapshot.features, 1):
        lines.append(f"# [Feature-{i}: {feat.name}] {feat.feature_type.value}")
        if feat.parameters:
            for pname, pval in feat.parameters.items():
                lines.append(f"#   {pname} = {pval}")
        if feat.expressions:
            expr_str = ", ".join(f"{k}={v}" for k, v in feat.expressions.items())
            lines.append(f"#   Expressions: {expr_str}")
        if feat.depends_on:
            lines.append(f"#   Depends on: {', '.join(feat.depends_on)}")
        if feat.sketch_ref:
            lines.append(f"#   Sketch: {feat.sketch_ref}")
        if feat.suppressed:
            lines.append("#   [SUPPRESSED]")
        lines.append("")

    return "\n".join(lines)


def feature_tree_to_nl(snapshot: FeatureTreeSnapshot) -> str:
    """将特征树快照转换为自然语言摘要。"""
    if not snapshot or not snapshot.features:
        return "Empty part, no features."

    parts = [f"Part '{snapshot.part_name}' has {snapshot.feature_count} features:"]
    for feat in snapshot.features:
        desc = f"  - {feat.name} ({feat.feature_type.value})"
        if feat.parameters:
            params = ", ".join(f"{k}={v}" for k, v in feat.parameters.items())
            desc += f" [{params}]"
        if feat.suppressed:
            desc += " (suppressed)"
        parts.append(desc)

    if snapshot.expressions:
        parts.append(f"\nGlobal parameters ({len(snapshot.expressions)}):")
        for name, value in sorted(snapshot.expressions.items()):
            parts.append(f"  {name} = {value}")

    return "\n".join(parts)


def get_editable_parameters(snapshot: FeatureTreeSnapshot) -> list[dict]:
    """提取所有可编辑参数列表。"""
    result = []
    for feat in snapshot.features:
        if feat.suppressed:
            continue
        for pname, pval in feat.parameters.items():
            if isinstance(pval, (int, float)):
                result.append({
                    "feature_name": feat.name,
                    "feature_type": feat.feature_type.value,
                    "param_name": pname,
                    "current_value": pval,
                })
    return result
