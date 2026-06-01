# -*- coding: utf-8 -*-
"""NXCopilot UI — 特征树可视化。"""
from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QLabel

class FeatureTreeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Feature Tree"))
        self._tree = QTreeWidget(); self._tree.setHeaderLabels(["Name","Type","Parameters"])
        self._tree.setColumnWidth(0, 150); self._tree.setColumnWidth(1, 100)
        layout.addWidget(self._tree)

    def load_from_dict(self, data: dict[str, Any]):
        self._tree.clear()
        root = QTreeWidgetItem(self._tree, [data.get("part_name","Part"), f'{data.get("feature_count",0)} features', ""])
        root.setExpanded(True)
        for f in data.get("features",[]):
            params = ", ".join(f"{k}={v}" for k,v in f.get("params",{}).items())
            QTreeWidgetItem(root, [f.get("name","?"), f.get("type","?"), params])
        exprs = data.get("expressions",{})
        if exprs:
            er = QTreeWidgetItem(root, ["Expressions", f"{len(exprs)}", ""])
            for n,v in sorted(exprs.items()): QTreeWidgetItem(er, [n,"",str(v)])

    def clear(self): self._tree.clear()
