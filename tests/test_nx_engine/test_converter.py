# -*- coding: utf-8 -*-
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "NXCopilot.Agent"))
from nx_engine.reader import FeatureType, FeatureNode, FeatureTreeSnapshot
from nx_engine.converter import feature_tree_to_nxopen, feature_tree_to_nl, get_editable_parameters

class TestConverter:
    def test_empty(self):
        assert "empty" in feature_tree_to_nxopen(FeatureTreeSnapshot("empty",""))
    def test_basic(self):
        fs = [FeatureNode("1","EXTRUDE(1)",FeatureType.EXTRUDE,parameters={"EndValue":20}),
              FeatureNode("2","HOLE(1)",FeatureType.HOLE,parameters={"Diameter":10})]
        s = FeatureTreeSnapshot("Flange","",fs,2,expressions={"p1":20.0})
        r = feature_tree_to_nxopen(s)
        assert "EXTRUDE(1)" in r and "HOLE(1)" in r and "p1 = 20.0" in r
    def test_nl(self):
        s = FeatureTreeSnapshot("T","",[FeatureNode("1","E",FeatureType.EXTRUDE)])
        assert "E" in feature_tree_to_nl(s)
    def test_editable(self):
        fs = [FeatureNode("1","E",FeatureType.EXTRUDE,parameters={"v":20})]
        assert len(get_editable_parameters(FeatureTreeSnapshot("T","",fs))) == 1
