# -*- coding: utf-8 -*-
"""
NXCopilot NX Engine — 正向设计构建器。

从 LLM 结构化输出 (FeatureSpec) 或自然语言描述，
生成完整的 NXOpen Python 创建代码。
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional
from nx_engine.reader import FeatureType

logger = logging.getLogger("nxcopilot.nx_engine.forward_builder")


@dataclass
class FeatureSpec:
    """特征规格 — LLM 的结构化输出。"""
    feature_type: FeatureType
    name: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class ForwardResult:
    """正向构建结果。"""
    success: bool
    nxopen_code: str = ""
    feature_specs: list[FeatureSpec] = field(default_factory=list)
    message: str = ""

# NXOpen creation templates
_TEMPLATES = {
    "extrude": "# Create Extrude: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\nsketch_feat = work_part.Features.FindObject(\"{sketch}\")\nsketch = sketch_feat.Sketch\nextrude_builder = work_part.Features.CreateExtrudeBuilder(NXOpen.Features.Feature.Null)\nsection = work_part.Sections.CreateSection(0.0095, 0.01, 0.5)\nextrude_builder.Section = section\ndirection = work_part.Directions.CreateDirection(\n    sketch.StartPoint, sketch.EndPoint,\n    NXOpen.SmartObject.UpdateOption.WithinModeling)\nextrude_builder.Direction = direction\nextrude_builder.Limits.StartExtend.Value.RightHandSide = \"{start}\"\nextrude_builder.Limits.EndExtend.Value.RightHandSide = \"{end}\"\nextrude_builder.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create\n{target} = extrude_builder.CommitFeature()\n{target}.Name = \"{name}\"\nextrude_builder.Destroy()",
    "revolve": "# Create Revolve: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\nsketch_feat = work_part.Features.FindObject(\"{sketch}\")\nsketch = sketch_feat.Sketch\nrevolve_builder = work_part.Features.CreateRevolveBuilder(NXOpen.Features.Feature.Null)\nrevolve_builder.Limits.StartExtend.Value.RightHandSide = \"{start_angle}\"\nrevolve_builder.Limits.EndExtend.Value.RightHandSide = \"{end_angle}\"\n{target} = revolve_builder.CommitFeature()\n{target}.Name = \"{name}\"\nrevolve_builder.Destroy()",
    "hole": "# Create Hole: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\nhole_builder = work_part.Features.CreateHolePackageBuilder(NXOpen.Features.Feature.Null)\nhole_builder.GeneralHoleDiameter.RightHandSide = \"{diameter}\"\nhole_builder.HoleDepth.RightHandSide = \"{depth}\"\nhole_builder.HoleTipAngle.RightHandSide = \"{tip_angle}\"\n{target} = hole_builder.CommitFeature()\n{target}.Name = \"{name}\"\nhole_builder.Destroy()",
    "edge_blend": "# Create EdgeBlend: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\nblend_builder = work_part.Features.CreateEdgeBlendBuilder(NXOpen.Features.Feature.Null)\nblend_builder.Tolerance = 0.01\nblend_builder.AllInstancesOption = False\n{target} = blend_builder.CommitFeature()\n{target}.Name = \"{name}\"\nblend_builder.Destroy()",
    "chamfer": "# Create Chamfer: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\nchamfer_builder = work_part.Features.CreateChamferBuilder(NXOpen.Features.Feature.Null)\nchamfer_builder.Option = NXOpen.Features.ChamferBuilder.ChamferOption.SymmetricOffsets\nchamfer_builder.FirstOffset = \"{distance}\"\n{target} = chamfer_builder.CommitFeature()\n{target}.Name = \"{name}\"\nchamfer_builder.Destroy()",
    "shell": "# Create Shell: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\nshell_builder = work_part.Features.CreateShellBuilder(NXOpen.Features.Feature.Null)\nshell_builder.Type = NXOpen.Features.ShellBuilder.ShellType.Offset\nshell_builder.Thickness.RightHandSide = \"{thickness}\"\n{target} = shell_builder.CommitFeature()\n{target}.Name = \"{name}\"\nshell_builder.Destroy()",
    "circular_pattern": "# Create CircularPattern: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\nsource_feat = work_part.Features.FindObject(\"{source}\")\naxis_feat = work_part.Features.FindObject(\"{axis}\")\npattern_builder = work_part.Features.CreateCircularPatternBuilder(NXOpen.Features.Feature.Null)\npattern_builder.PatternService.FeatureList = [source_feat]\npattern_builder.PatternService.AxisDefinition.Axis = axis_feat\npattern_builder.PatternService.CircularLayoutDefinition.NPatternCount.RightHandSide = \"{count}\"\npattern_builder.PatternService.CircularLayoutDefinition.AngularPitch.RightHandSide = \"{angle}\"\n{target} = pattern_builder.CommitFeature()\n{target}.Name = \"{name}\"\npattern_builder.Destroy()",
    "rectangular_pattern": "# Create RectangularPattern: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\nsource_feat = work_part.Features.FindObject(\"{source}\")\npattern_builder = work_part.Features.CreateRectangularPatternBuilder(NXOpen.Features.Feature.Null)\npattern_builder.PatternService.FeatureList = [source_feat]\npattern_builder.PatternService.RectangularLayoutDefinition.NPatternCountX.RightHandSide = \"{count_x}\"\npattern_builder.PatternService.RectangularLayoutDefinition.PitchDistanceX.RightHandSide = \"{spacing_x}\"\npattern_builder.PatternService.RectangularLayoutDefinition.NPatternCountY.RightHandSide = \"{count_y}\"\npattern_builder.PatternService.RectangularLayoutDefinition.PitchDistanceY.RightHandSide = \"{spacing_y}\"\n{target} = pattern_builder.CommitFeature()\n{target}.Name = \"{name}\"\npattern_builder.Destroy()",
    "mirror": "# Create Mirror: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\nsource_feat = work_part.Features.FindObject(\"{source}\")\nplane_feat = work_part.Features.FindObject(\"{plane}\")\nmirror_builder = work_part.Features.CreateMirrorFeatureBuilder(NXOpen.Features.Feature.Null)\nmirror_builder.SourceFeature = source_feat\nmirror_builder.MirrorPlane = plane_feat\n{target} = mirror_builder.CommitFeature()\n{target}.Name = \"{name}\"\nmirror_builder.Destroy()",
    "boolean_subtract": "# Boolean Subtract: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\ntarget_body = work_part.Bodies.FindObject(\"{target_body}\")\ntool_body = work_part.Bodies.FindObject(\"{tool_body}\")\nbool_builder = work_part.Features.CreateBooleanBuilder(NXOpen.Features.Feature.Null)\nbool_builder.Operation = NXOpen.Features.Feature.BooleanType.Subtract\nbool_builder.Target = target_body\nbool_builder.Tool = tool_body\n{target} = bool_builder.CommitFeature()\n{target}.Name = \"{name}\"\nbool_builder.Destroy()",
    "boolean_unite": "# Boolean Unite: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\ntarget_body = work_part.Bodies.FindObject(\"{target_body}\")\ntool_body = work_part.Bodies.FindObject(\"{tool_body}\")\nbool_builder = work_part.Features.CreateBooleanBuilder(NXOpen.Features.Feature.Null)\nbool_builder.Operation = NXOpen.Features.Feature.BooleanType.Unite\nbool_builder.Target = target_body\nbool_builder.Tool = tool_body\n{target} = bool_builder.CommitFeature()\n{target}.Name = \"{name}\"\nbool_builder.Destroy()",
    "datum_plane": "# Create DatumPlane: {name}\nimport NXOpen\nsession = NXOpen.Session.GetSession()\nwork_part = session.Parts.Work\nplane_builder = work_part.Features.CreateDatumPlaneBuilder(NXOpen.Features.Feature.Null)\nplane_builder.Type = NXOpen.Features.DatumPlaneBuilder.PlaneType.Fixed\nplane_builder.PlaneReference = work_part.XYPlane\nplane_builder.Offset.RightHandSide = \"{offset}\"\n{target} = plane_builder.CommitFeature()\n{target}.Name = \"{name}\"\nplane_builder.Destroy()",
}


class ForwardBuilder:
    """正向设计代码构建器。"""

    _DEFAULTS = {
        "start": "0", "end": "20",
        "start_angle": "0", "end_angle": "360",
        "diameter": "10", "depth": "20", "tip_angle": "118",
        "radius": "3", "distance": "2", "thickness": "2",
        "offset": "0",
        "count": "6", "angle": "360",
        "count_x": "3", "spacing_x": "20", "count_y": "1", "spacing_y": "0",
        "sketch": "SKETCH(1)", "axis": "DATUM_CSYS(1)", "plane": "DATUM_CSYS(1)",
        "source": "EXTRUDE(1)",
        "target_body": "Body 1", "tool_body": "Body 2",
    }

    def build_from_specs(self, specs: list[FeatureSpec]) -> ForwardResult:
        if not specs:
            return ForwardResult(success=True, nxopen_code="# No features to create")
        blocks = [
            "# === NXCopilot Forward Design ===",
            "import NXOpen", "",
            "session = NXOpen.Session.GetSession()",
            "work_part = session.Parts.Work", "",
        ]
        for i, spec in enumerate(specs):
            code = self._generate_feature_code(spec, i)
            blocks.append(code)
            blocks.append("")
        blocks.append("work_part.Update()")
        return ForwardResult(success=True, nxopen_code="\n".join(blocks), feature_specs=specs)

    def build_from_description(self, description: str) -> ForwardResult:
        specs = self._parse_description(description)
        if not specs:
            return ForwardResult(success=False, message="Could not parse description")
        return self.build_from_specs(specs)

    def _generate_feature_code(self, spec: FeatureSpec, index: int = 0) -> str:
        ft = spec.feature_type.value.lower().replace(" ", "_")
        template = _TEMPLATES.get(ft)
        if template is None:
            return f"# WARNING: No template for {spec.feature_type.value}\n# Parameters: {spec.parameters}"

        name = spec.name or f"{spec.feature_type.value}_{index + 1}"
        target = f"feat_{name.replace('(', '_').replace(')', '')}"

        variables = dict(self._DEFAULTS)
        variables["name"] = name
        variables["target"] = target
        variables.update(spec.parameters)

        try:
            return template.format(**variables)
        except KeyError as e:
            return f"# WARNING: Missing parameter {e} for {spec.feature_type.value}"

    @staticmethod
    def _parse_description(description: str) -> list[FeatureSpec]:
        specs = []
        d = description.lower()

        m = re.search(r'(?:拉伸|extrude)\s*(\d+(?:\.\d+)?)', d)
        if m:
            sketch_m = re.search(r'(?:草图|sketch)\s*[=:]\s*(\w+)', d)
            sketch = sketch_m.group(1) if sketch_m else "SKETCH(1)"
            specs.append(FeatureSpec(FeatureType.EXTRUDE, "EXTRUDE_NEW", {"end": m.group(1), "sketch": sketch}))

        m = re.search(r'(?:旋转|revolve)\s*(\d+(?:\.\d+)?)', d)
        if m:
            specs.append(FeatureSpec(FeatureType.REVOLVE, "REVOLVE_NEW", {"end_angle": m.group(1)}))

        m = re.search(r'(?:孔|hole).*?(?:直径|d)\s*[=: ]?\s*(\d+(?:\.\d+)?)', d)
        if m:
            depth_m = re.search(r'(?:深度|depth)\s*[=: ]?\s*(\d+(?:\.\d+)?)', d)
            specs.append(FeatureSpec(FeatureType.HOLE, "HOLE_NEW", {
                "diameter": m.group(1), "depth": depth_m.group(1) if depth_m else "20"
            }))

        m = re.search(r'(?:倒圆角|blend|fillet)\s*[rR]?\s*(\d+(?:\.\d+)?)', d)
        if m:
            specs.append(FeatureSpec(FeatureType.EDGE_BLEND, "BLEND_NEW", {"radius": m.group(1)}))

        m = re.search(r'(?:倒角|chamfer)\s*(\d+(?:\.\d+)?)', d)
        if m:
            specs.append(FeatureSpec(FeatureType.CHAMFER, "CHAMFER_NEW", {"distance": m.group(1)}))

        m = re.search(r'(?:抽壳|shell)\s*(\d+(?:\.\d+)?)', d)
        if m:
            specs.append(FeatureSpec(FeatureType.SHELL, "SHELL_NEW", {"thickness": m.group(1)}))

        m = re.search(r'(?:圆形阵列|circular\s*pattern)\s*(\d+)', d)
        if m:
            specs.append(FeatureSpec(FeatureType.CIRCULAR_PATTERN, "CPATTERN_NEW", {"count": m.group(1)}))

        m = re.search(r'(?:矩形阵列|rectangular\s*pattern)\s*(\d+)\s*[xX×]\s*(\d+)', d)
        if m:
            specs.append(FeatureSpec(FeatureType.RECTANGULAR_PATTERN, "RPATTERN_NEW", {
                "count_x": m.group(1), "count_y": m.group(2)
            }))

        return specs
