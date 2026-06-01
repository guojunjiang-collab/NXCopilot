# -*- coding: utf-8 -*-
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "NXCopilot.Agent"))
from nx_engine.reader import FeatureType, FeatureNode, FeatureTreeSnapshot, FeatureTreeDelta, DeltaDetector

class TestFeatureNode:
    def test_create(self):
        n = FeatureNode("1","EXTRUDE(1)",FeatureType.EXTRUDE)
        assert n.name == "EXTRUDE(1)" and n.feature_type == FeatureType.EXTRUDE
    def test_params(self):
        n = FeatureNode("2","HOLE(1)",FeatureType.HOLE, parameters={"Diameter":10.0})
        assert n.parameters["Diameter"] == 10.0

class TestDeltaDetector:
    def test_first_read(self):
        new = FeatureTreeSnapshot("t","",[FeatureNode("1","EXTRUDE(1)",FeatureType.EXTRUDE)])
        d = DeltaDetector().detect(None, new)
        assert len(d.added) == 1
    def test_no_change(self):
        f = FeatureNode("1","EXTRUDE(1)",FeatureType.EXTRUDE)
        d = DeltaDetector().detect(FeatureTreeSnapshot("t","",[f]), FeatureTreeSnapshot("t","",[f]))
        assert len(d.unchanged) == 1
    def test_param_change(self):
        old = FeatureTreeSnapshot("t","",[FeatureNode("1","E",FeatureType.EXTRUDE,parameters={"v":20})])
        new = FeatureTreeSnapshot("t","",[FeatureNode("1","E",FeatureType.EXTRUDE,parameters={"v":30})])
        d = DeltaDetector().detect(old, new)
        assert len(d.modified) == 1
