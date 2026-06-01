# -*- coding: utf-8 -*-
"""NXCopilot 测试 — nx_engine/expression.py (离线模式, 无 NX)。"""

import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "NXCopilot.Agent"))

from nx_engine.expression import ExpressionManager, NXExpression


class TestNXExpression:
    def test_create(self):
        e = NXExpression("p1", 20.0)
        assert e.name == "p1" and e.value == 20.0
        assert e.unit == "MilliMeter"

    def test_with_unit(self):
        e = NXExpression("angle1", 45.0, unit="Degree")
        assert e.unit == "Degree"


class TestExpressionManager:
    def test_no_part(self):
        mgr = ExpressionManager()
        assert mgr.read_all() == []
        assert mgr.find("p1") is None
        assert mgr.edit("p1", 10) is False
        assert mgr.create("p1", 10) is False
        assert mgr.to_dict() == {}

    def test_set_part_none(self):
        mgr = ExpressionManager()
        mgr.set_part(None)
        assert mgr.read_all() == []
