# -*- coding: utf-8 -*-
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "NXCopilot.Agent"))
from nx_engine.reader import FeatureType, FeatureNode, FeatureTreeSnapshot
from nx_engine.dependency import DependencyGraph, EditValidator

class TestDependencyGraph:
    def test_topo_sort(self):
        fs = [FeatureNode("1","SKETCH(1)",FeatureType.SKETCH),
              FeatureNode("2","EXTRUDE(1)",FeatureType.EXTRUDE,depends_on=["SKETCH(1)"]),
              FeatureNode("3","HOLE(1)",FeatureType.HOLE,depends_on=["EXTRUDE(1)"])]
        g = DependencyGraph(); g.build_from_features(fs)
        topo = g.topological_sort()
        assert topo.index("SKETCH(1)") < topo.index("EXTRUDE(1)") < topo.index("HOLE(1)")
    def test_safe_remove(self):
        fs = [FeatureNode("1","E",FeatureType.EXTRUDE),
              FeatureNode("2","H",FeatureType.HOLE,depends_on=["E"])]
        g = DependencyGraph(); g.build_from_features(fs)
        assert g.can_safely_remove("H")[0] is True
        assert g.can_safely_remove("E")[0] is False

class TestEditValidator:
    def test_valid(self):
        fs = [FeatureNode("1","E",FeatureType.EXTRUDE),
              FeatureNode("2","H",FeatureType.HOLE,depends_on=["E"])]
        v, e = EditValidator().validate_edit(FeatureTreeSnapshot("t",""), fs)
        assert v is True
    def test_missing_dep(self):
        fs = [FeatureNode("1","H",FeatureType.HOLE,depends_on=["E"])]
        v, e = EditValidator().validate_edit(FeatureTreeSnapshot("t",""), fs)
        assert v is False
