# -*- coding: utf-8 -*-
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "NXCopilot.Agent"))
from nx_engine.editor import NXEditor, EditAction, EditActionType

class TestNXEditor:
    def setup_method(self): self.e = NXEditor()
    def test_modify(self):
        r = self.e.generate(EditAction(EditActionType.MODIFY_PARAM,"E","EndValue",30))
        assert r.success and "30" in r.nxopen_code
    def test_remove(self):
        r = self.e.generate(EditAction(EditActionType.REMOVE_FEATURE,"HOLE(1)"))
        assert r.success and "DeleteFeature" in r.nxopen_code
    def test_suppress(self):
        r = self.e.generate(EditAction(EditActionType.SUPPRESS,"BLEND(1)"))
        assert r.success and "Suppressed = True" in r.nxopen_code
    def test_rename(self):
        r = self.e.generate(EditAction(EditActionType.RENAME,"E",new_name="Base"))
        assert r.success and "Base" in r.nxopen_code
    def test_batch(self):
        r = self.e.generate_batch([
            EditAction(EditActionType.MODIFY_PARAM,"E","EndValue",25),
            EditAction(EditActionType.SUPPRESS,"HOLE(1)"),
        ])
        assert r.success and "25" in r.nxopen_code
