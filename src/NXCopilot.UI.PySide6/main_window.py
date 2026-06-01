# -*- coding: utf-8 -*-
"""NXCopilot UI — PySide6 主窗口。"""
from __future__ import annotations
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QStatusBar, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from widgets.chat_panel import ChatPanel
from widgets.feature_tree import FeatureTreeWidget
from widgets.settings_dialog import SettingsDialog
from agent_client import AgentClient

class MainWindow(QMainWindow):
    def __init__(self, agent_url="http://127.0.0.1:8757"):
        super().__init__()
        self.setWindowTitle("NXCopilot — NX AI 设计助手")
        self.setMinimumSize(1000, 700)
        self._agent = AgentClient(agent_url)
        self._setup_ui(); self._setup_menu(); self._setup_status()
        QTimer.singleShot(500, self._try_connect)

    def _setup_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        splitter = QSplitter(Qt.Horizontal)
        self._tree = FeatureTreeWidget(); splitter.addWidget(self._tree)
        self._chat = ChatPanel(self._agent); splitter.addWidget(self._chat)
        splitter.setSizes([350, 650]); layout.addWidget(splitter)

    def _setup_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("File")
        sa = QAction("LLM Settings...", self); sa.triggered.connect(self._show_settings); fm.addAction(sa)
        fm.addSeparator()
        qa = QAction("Quit", self); qa.triggered.connect(self.close); fm.addAction(qa)
        vm = mb.addMenu("View")
        ra = QAction("Refresh Model", self); ra.triggered.connect(self._refresh); vm.addAction(ra)

    def _setup_status(self):
        self._sb = QStatusBar(); self.setStatusBar(self._sb); self._sb.showMessage("Ready")

    def _try_connect(self):
        ok, info = self._agent.check_health()
        if ok:
            nx = "Connected" if info.get("nx_connected") else "Not connected"
            llm = "Ready" if info.get("llm_ready") else "Not configured"
            self._sb.showMessage(f"Agent: OK | NX: {nx} | LLM: {llm}")
        else:
            self._sb.showMessage("Agent not connected — start backend first")

    def _show_settings(self):
        SettingsDialog(self._agent, self).exec()

    def _refresh(self):
        m = self._agent.get_model()
        if m and "features" in m:
            self._tree.load_from_dict(m)
            self._sb.showMessage(f"Model: {m.get('part_name','?')} ({m.get('feature_count',0)} features)")
        else:
            self._sb.showMessage("Cannot read model")
