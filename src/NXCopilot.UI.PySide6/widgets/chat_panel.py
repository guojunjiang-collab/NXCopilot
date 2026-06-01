# -*- coding: utf-8 -*-
"""NXCopilot UI — 对话面板。"""
from __future__ import annotations
import threading
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, Qt, QMetaObject, Q_ARG
from PySide6.QtGui import QFont

class ChatPanel(QWidget):
    def __init__(self, agent, parent=None):
        super().__init__(parent)
        self._agent = agent
        layout = QVBoxLayout(self)
        self._display = QTextEdit(); self._display.setReadOnly(True); self._display.setFont(QFont("Consolas", 10))
        layout.addWidget(self._display)
        row = QHBoxLayout()
        self._input = QLineEdit(); self._input.setPlaceholderText("Type message..."); self._input.returnPressed.connect(self._send)
        row.addWidget(self._input)
        self._btn = QPushButton("Send"); self._btn.clicked.connect(self._send); row.addWidget(self._btn)
        layout.addLayout(row)

    def _send(self):
        text = self._input.text().strip()
        if not text: return
        self._append("You", text); self._input.clear(); self._btn.setEnabled(False)
        threading.Thread(target=self._async_send, args=(text,), daemon=True).start()

    def _async_send(self, text):
        r = self._agent.send_message(text)
        self._append("NXCopilot", r.get("reply",""), r.get("intent",""))
        self._btn.setEnabled(True)

    def _append(self, sender, text, intent=""):
        tag = f" [{intent}]" if intent else ""
        html = f'<div style="margin:8px 0"><b>{sender}{tag}:</b><br>{text}</div>'
        QMetaObject.invokeMethod(self._display, "append", Qt.QueuedConnection, Q_ARG(str, html))
