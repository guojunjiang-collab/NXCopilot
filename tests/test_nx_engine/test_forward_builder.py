# -*- coding: utf-8 -*-
"""NXCopilot 测试 — nx_engine/forward_builder.py (离线模式)。"""

import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "NXCopilot.Agent"))

from nx_engine.reader import FeatureType
from nx_engine.forward_builder import ForwardBuilder, FeatureSpec, ForwardResult


class TestForwardBuilder:
    def setup_method(self):
        self.builder = ForwardBuilder()

    def test_empty_specs(self):
        r = self.builder.build_from_specs([])
        assert r.success
        assert "No features" in r.nxopen_code

    def test_extrude_spec(self):
        spec = FeatureSpec(
            feature_type=FeatureType.EXTRUDE,
            name="BASE",
            parameters={"end": "25", "sketch": "SKETCH(1)"},
        )
        r = self.builder.build_from_specs([spec])
        assert r.success
        assert "EXTRUDE" in r.nxopen_code or "Extrude" in r.nxopen_code
        assert "25" in r.nxopen_code
        assert "feat_BASE" in r.nxopen_code

    def test_hole_spec(self):
        spec = FeatureSpec(
            feature_type=FeatureType.HOLE,
            name="H1",
            parameters={"diameter": "12", "depth": "30"},
        )
        r = self.builder.build_from_specs([spec])
        assert r.success
        assert "12" in r.nxopen_code
        assert "30" in r.nxopen_code

    def test_edge_blend_spec(self):
        spec = FeatureSpec(
            feature_type=FeatureType.EDGE_BLEND,
            name="R3",
            parameters={"radius": "3"},
        )
        r = self.builder.build_from_specs([spec])
        assert r.success
        assert "3" in r.nxopen_code

    def test_multiple_specs(self):
        specs = [
            FeatureSpec(FeatureType.EXTRUDE, "BASE", {"end": "20"}),
            FeatureSpec(FeatureType.HOLE, "H1", {"diameter": "10"}),
            FeatureSpec(FeatureType.EDGE_BLEND, "R2", {"radius": "2"}),
        ]
        r = self.builder.build_from_specs(specs)
        assert r.success
        assert r.nxopen_code.count("work_part.Update()") == 1  # final update

    def test_parse_extrude(self):
        specs = self.builder._parse_description("拉伸20mm")
        assert len(specs) == 1
        assert specs[0].feature_type == FeatureType.EXTRUDE
        assert specs[0].parameters["end"] == "20"

    def test_parse_hole(self):
        specs = self.builder._parse_description("打孔 直径10 深度25")
        assert len(specs) == 1
        assert specs[0].feature_type == FeatureType.HOLE
        assert specs[0].parameters["diameter"] == "10"
        assert specs[0].parameters["depth"] == "25"

    def test_parse_blend(self):
        specs = self.builder._parse_description("倒圆角R5")
        assert len(specs) == 1
        assert specs[0].feature_type == FeatureType.EDGE_BLEND
        assert specs[0].parameters["radius"] == "5"

    def test_parse_chamfer(self):
        specs = self.builder._parse_description("倒角3mm")
        assert len(specs) == 1
        assert specs[0].feature_type == FeatureType.CHAMFER

    def test_parse_shell(self):
        specs = self.builder._parse_description("抽壳2mm")
        assert len(specs) == 1
        assert specs[0].feature_type == FeatureType.SHELL
        assert specs[0].parameters["thickness"] == "2"

    def test_parse_circular_pattern(self):
        specs = self.builder._parse_description("圆形阵列6个")
        assert len(specs) == 1
        assert specs[0].feature_type == FeatureType.CIRCULAR_PATTERN
        assert specs[0].parameters["count"] == "6"

    def test_parse_rectangular_pattern(self):
        specs = self.builder._parse_description("矩形阵列3x4")
        assert len(specs) == 1
        assert specs[0].feature_type == FeatureType.RECTANGULAR_PATTERN
        assert specs[0].parameters["count_x"] == "3"
        assert specs[0].parameters["count_y"] == "4"

    def test_parse_multi_feature(self):
        specs = self.builder._parse_description("拉伸20mm 然后打孔 直径10")
        assert len(specs) == 2
        types = {s.feature_type for s in specs}
        assert FeatureType.EXTRUDE in types
        assert FeatureType.HOLE in types

    def test_parse_empty(self):
        specs = self.builder._parse_description("hello world")
        assert len(specs) == 0

    def test_unknown_template(self):
        spec = FeatureSpec(FeatureType.UNKNOWN, "X")
        r = self.builder.build_from_specs([spec])
        assert r.success
        assert "WARNING" in r.nxopen_code

    def test_build_from_description(self):
        r = self.builder.build_from_description("拉伸30mm")
        assert r.success
        assert "30" in r.nxopen_code

    def test_build_from_description_empty(self):
        r = self.builder.build_from_description("just chatting")
        assert not r.success
