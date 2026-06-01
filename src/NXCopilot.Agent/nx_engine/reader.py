# -*- coding: utf-8 -*-
"""
NXCopilot NX Engine — NXOpen 特征树读取模块。

通过 NXOpen Python API 连接运行中的 NX 实例，
读取当前 Work Part 的特征树，输出结构化的 FeatureTreeSnapshot。

与 CATIA 版本的差异：
  - CATIA: pywin32 COM -> win32com.client.GetActiveObject("CATIA.Application")
  - NX:    NXOpen.Session.GetSession() -> session.Parts.Work.Features
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("nxcopilot.nx_engine.reader")


class FeatureType(str, Enum):
    """NX 特征类型枚举（建模常用特征）。"""

    # === 实体特征 ===
    EXTRUDE = "Extrude"
    REVOLVE = "Revolve"
    SWEEP = "SweepAlongGuide"
    LOFT = "Loft"
    BOOLEAN_UNITE = "Unite"
    BOOLEAN_SUBTRACT = "Subtract"
    BOOLEAN_INTERSECT = "Intersect"

    # === 孔/槽 ===
    HOLE = "Hole"
    POCKET = "Pocket"
    SLOT = "Slot"
    GROOVE = "Groove"

    # === 圆角/倒角 ===
    EDGE_BLEND = "EdgeBlend"
    CHAMFER = "Chamfer"
    FACE_BLEND = "FaceBlend"
    VARIABLE_RADIUS_BLEND = "VariableRadiusBlend"

    # === 壳/筋/抽壳 ===
    SHELL = "Shell"
    RIB = "Rib"
    STIFFENER = "Stiffener"
    BOSS = "Boss"
    PAD_FEATURE = "Pad"

    # === 阵列/镜像 ===
    CIRCULAR_PATTERN = "CircularPattern"
    RECTANGULAR_PATTERN = "RectangularPattern"
    MIRROR = "Mirror"
    PATTERN_FEATURE = "PatternFeature"
    USER_DEFINED_PATTERN = "UserDefinedPattern"

    # === 变换 ===
    DRAFT = "Draft"
    OFFSET = "Offset"
    SCALE = "Scale"
    TRIM_BODY = "TrimBody"
    REPLACE_FACE = "ReplaceFace"
    THICKEN = "Thicken"

    # === 草图 ===
    SKETCH = "Sketch"

    # === 基准 ===
    DATUM_PLANE = "DatumPlane"
    DATUM_AXIS = "DatumAxis"
    DATUM_CSYS = "DatumCsys"
    POINT = "Point"

    # === 其他 ===
    BODY = "Body"
    IMPORT = "Import"
    UNKNOWN = "Unknown"


@dataclass
class FeatureNode:
    """单个特征的结构化表示。"""
    id: str                          # 唯一标识 (NX: Tag 或 Name)
    name: str                        # 显示名称 (如 "EXTRUDE(1)")
    feature_type: FeatureType        # 特征类型
    parameters: dict[str, Any] = field(default_factory=dict)
    expressions: dict[str, float] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    sketch_ref: Optional[str] = None
    body_name: Optional[str] = None
    suppressed: bool = False
    timestamp: Optional[datetime] = None


@dataclass
class FeatureTreeSnapshot:
    """特征树快照 — Agent 的核心上下文。"""
    part_name: str
    file_path: str
    features: list[FeatureNode] = field(default_factory=list)
    feature_count: int = 0
    body_names: list[str] = field(default_factory=list)
    expressions: dict[str, float] = field(default_factory=dict)
    sketch_names: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    nx_version: str = ""


@dataclass
class FeatureTreeDelta:
    """特征树增量差异。"""
    added: list[FeatureNode] = field(default_factory=list)
    modified: list[dict[str, Any]] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)


class PartReader:
    """
    NX 特征树读取器。

    通过 NXOpen API 遍历当前 Work Part 的全部特征、表达式、Body，
    输出 FeatureTreeSnapshot。

    使用方式::

        reader = PartReader()
        if reader.connect():
            snapshot = reader.read_feature_tree()
            print(f"读取到 {snapshot.feature_count} 个特征")
    """

    # NXOpen Feature 类型字符串 -> FeatureType 枚举的映射
    _NX_TYPE_MAP: dict[str, FeatureType] = {
        "EXTRUDE": FeatureType.EXTRUDE,
        "REVOLVE": FeatureType.REVOLVE,
        "SWEEP": FeatureType.SWEEP,
        "SWEEPALONGGUIDE": FeatureType.SWEEP,
        "LOFT": FeatureType.LOFT,
        "UNITE": FeatureType.BOOLEAN_UNITE,
        "SUBTRACT": FeatureType.BOOLEAN_SUBTRACT,
        "INTERSECT": FeatureType.BOOLEAN_INTERSECT,
        "HOLE": FeatureType.HOLE,
        "SIMPLE_HOLE": FeatureType.HOLE,
        "POCKET": FeatureType.POCKET,
        "SLOT": FeatureType.SLOT,
        "GROOVE": FeatureType.GROOVE,
        "EDGE_BLEND": FeatureType.EDGE_BLEND,
        "CHAMFER": FeatureType.CHAMFER,
        "FACE_BLEND": FeatureType.FACE_BLEND,
        "SHELL": FeatureType.SHELL,
        "RIB": FeatureType.RIB,
        "DRAFT": FeatureType.DRAFT,
        "CIRCULAR_PATTERN": FeatureType.CIRCULAR_PATTERN,
        "RECTANGULAR_PATTERN": FeatureType.RECTANGULAR_PATTERN,
        "MIRROR": FeatureType.MIRROR,
        "PATTERN": FeatureType.PATTERN_FEATURE,
        "SKETCH": FeatureType.SKETCH,
        "DATUM_PLANE": FeatureType.DATUM_PLANE,
        "DATUM_AXIS": FeatureType.DATUM_AXIS,
        "DATUM_CSYS": FeatureType.DATUM_CSYS,
        "TRIM": FeatureType.TRIM_BODY,
    }

    def __init__(self):
        self._session = None
        self._connected = False

    def connect(self) -> bool:
        """连接到运行中的 NX 实例（必须在 NX Journal 环境中或 NXOpen 可用时）。"""
        try:
            import NXOpen
            self._session = NXOpen.Session.GetSession()
            self._connected = True
            logger.info("Connected to NX via NXOpen")
            return True
        except ImportError:
            logger.warning("NXOpen module not available (not running inside NX environment)")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to NX: {e}")
            return False

    def is_connected(self) -> bool:
        return self._connected and self._session is not None

    def get_work_part(self):
        """获取当前 Work Part 对象。"""
        if not self.is_connected():
            return None
        try:
            wp = self._session.Parts.Work
            return wp
        except Exception as e:
            logger.error(f"Failed to get work part: {e}")
            return None

    def read_feature_tree(self) -> Optional[FeatureTreeSnapshot]:
        """
        读取当前 Work Part 的完整特征树。

        Returns:
            FeatureTreeSnapshot or None if not connected / no active part.
        """
        if not self.is_connected():
            logger.error("Not connected to NX")
            return None

        try:
            import NXOpen
        except ImportError:
            return None

        work_part = self.get_work_part()
        if work_part is None:
            logger.warning("No active Work Part in NX")
            return None

        features: list[FeatureNode] = []
        body_names: list[str] = []
        sketch_names: list[str] = []
        global_expressions: dict[str, float] = {}

        # --- 1. 读取全局表达式 ---
        try:
            for expr in work_part.Expressions:
                try:
                    name = expr.Name
                    value = expr.Value
                    global_expressions[name] = value
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Failed to read expressions: {e}")

        # --- 2. 遍历特征 ---
        try:
            for feat in work_part.Features:
                node = self._read_single_feature(feat, global_expressions)
                if node is not None:
                    features.append(node)
                    if node.feature_type == FeatureType.SKETCH:
                        sketch_names.append(node.name)
        except Exception as e:
            logger.error(f"Failed to iterate features: {e}")

        # --- 3. 读取 Body 列表 ---
        try:
            for body in work_part.Bodies:
                body_names.append(body.Name)
        except Exception:
            pass

        snapshot = FeatureTreeSnapshot(
            part_name=work_part.Name,
            file_path=str(getattr(work_part, "FullPath", "")),
            features=features,
            feature_count=len(features),
            body_names=body_names,
            expressions=global_expressions,
            sketch_names=sketch_names,
        )

        logger.info(
            f"Read feature tree: {snapshot.feature_count} features, "
            f"{len(body_names)} bodies, {len(global_expressions)} expressions"
        )
        return snapshot

    def _read_single_feature(self, feat, global_expressions: dict) -> Optional[FeatureNode]:
        """读取单个特征的详细信息。"""
        try:
            import NXOpen
        except ImportError:
            return None

        # 确定特征类型
        feat_type_str = self._get_feature_type_string(feat)
        feat_type = self._NX_TYPE_MAP.get(feat_type_str.upper(), FeatureType.UNKNOWN)

        name = feat.Name if hasattr(feat, "Name") else str(feat.Tag)

        # 读取关联参数
        parameters: dict[str, Any] = {}
        sketch_ref: Optional[str] = None

        try:
            # 通用：尝试读取 Expressions
            if hasattr(feat, "GetExpressions"):
                for expr in feat.GetExpressions():
                    try:
                        parameters[expr.Name] = expr.Value
                    except Exception:
                        continue

            # Extrude: 起止值
            if feat_type == FeatureType.EXTRUDE:
                try:
                    limits = feat.Limits
                    if limits and len(limits) > 0:
                        parameters["StartValue"] = limits[0].StartValue.Value                             if hasattr(limits[0].StartValue, "Value") else 0.0
                        parameters["EndValue"] = limits[0].EndValue.Value                             if hasattr(limits[0].EndValue, "Value") else 0.0
                except Exception:
                    pass

            # Hole: 直径、深度
            if feat_type == FeatureType.HOLE:
                for p in ["Diameter", "Depth", "TipAngle"]:
                    try:
                        val = getattr(feat, p, None)
                        if val is not None:
                            parameters[p] = float(str(val))
                    except Exception:
                        continue

            # EdgeBlend: 半径
            if feat_type == FeatureType.EDGE_BLEND:
                try:
                    if hasattr(feat, "Tolerances") and feat.Tolerances:
                        parameters["Radius"] = feat.Tolerances[0]
                except Exception:
                    pass

            # Chamfer: 距离
            if feat_type == FeatureType.CHAMFER:
                for p in ["FirstDist", "SecondDist"]:
                    try:
                        val = getattr(feat, p, None)
                        if val is not None:
                            parameters[p] = float(str(val))
                    except Exception:
                        continue

        except Exception as e:
            logger.debug(f"Could not read parameters for {name}: {e}")

        # 草图引用
        try:
            if hasattr(feat, "Sketch"):
                sketch_ref = str(feat.Sketch)
        except Exception:
            pass

        # 依赖关系（父特征）
        depends_on: list[str] = []
        try:
            if hasattr(feat, "GetParents"):
                for parent in feat.GetParents():
                    try:
                        depends_on.append(
                            parent.Name if hasattr(parent, "Name") else str(parent.Tag)
                        )
                    except Exception:
                        continue
        except Exception:
            pass

        # 抑制状态
        suppressed = False
        try:
            suppressed = bool(feat.Suppressed) if hasattr(feat, "Suppressed") else False
        except Exception:
            pass

        return FeatureNode(
            id=str(feat.Tag) if hasattr(feat, "Tag") else name,
            name=name,
            feature_type=feat_type,
            parameters=parameters,
            depends_on=depends_on,
            sketch_ref=sketch_ref,
            suppressed=suppressed,
        )

    @staticmethod
    def _get_feature_type_string(feat) -> str:
        """从 NX Feature 对象提取类型字符串。"""
        try:
            # NXOpen 方式
            if hasattr(feat, "FeatureType"):
                ft = feat.FeatureType
                if hasattr(ft, "FamilyName"):
                    return str(ft.FamilyName)
                if hasattr(ft, "ToString"):
                    return str(ft.ToString())
            # 回退: 类名
            return type(feat).__name__.upper()
        except Exception:
            return "UNKNOWN"


class DeltaDetector:
    """对比两次快照，计算增量差异。"""

    def detect(
        self, old: Optional[FeatureTreeSnapshot], new: FeatureTreeSnapshot
    ) -> FeatureTreeDelta:
        """对比新旧快照，返回增/删/改/不变。"""
        if old is None:
            return FeatureTreeDelta(
                added=list(new.features),
                unchanged=[],
            )

        old_map = {f.name: f for f in old.features}
        new_map = {f.name: f for f in new.features}

        added: list[FeatureNode] = []
        removed: list[str] = []
        modified: list[dict[str, Any]] = []
        unchanged: list[str] = []

        for name, new_feat in new_map.items():
            if name not in old_map:
                added.append(new_feat)
            elif new_feat.parameters != old_map[name].parameters:
                modified.append({
                    "name": name,
                    "old_params": old_map[name].parameters,
                    "new_params": new_feat.parameters,
                })
            else:
                unchanged.append(name)

        for name in old_map:
            if name not in new_map:
                removed.append(name)

        return FeatureTreeDelta(
            added=added, modified=modified, removed=removed, unchanged=unchanged,
        )
