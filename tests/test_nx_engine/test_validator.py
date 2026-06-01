# -*- coding: utf-8 -*-
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "NXCopilot.Agent"))
from nx_engine.validator import NXCodeValidator

class TestNXCodeValidator:
    def setup_method(self): self.v = NXCodeValidator()
    def test_valid_syntax(self):
        assert self.v.validate_python_syntax("import NXOpen\n").valid
    def test_syntax_error(self):
        assert not self.v.validate_python_syntax("def foo(\n").valid
    def test_dangerous(self):
        assert not self.v.validate_nxopen_safety("import os\nos.remove('/x')\n").valid
    def test_safe(self):
        assert self.v.validate_nxopen_safety("import NXOpen\nsession = NXOpen.Session.GetSession()\n").valid
    def test_ref_check(self):
        assert self.v.validate_references('feat = work_part.Features.FindObject("E")\n', ["E","H"]).valid
        assert not self.v.validate_references('feat = work_part.Features.FindObject("E")\n', ["H"]).valid
    def test_comprehensive(self):
        assert self.v.validate("import NXOpen\n").valid
