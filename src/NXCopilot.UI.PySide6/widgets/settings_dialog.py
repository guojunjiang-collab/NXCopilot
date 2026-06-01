# -*- coding: utf-8 -*-
"""NXCopilot UI — LLM 设置对话框。"""
from __future__ import annotations
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton, QLabel, QMessageBox)

PRESETS = {
    "DeepSeek V4 Pro": ("deepseek/deepseek-v4-pro", "https://api.deepseek.com/v1"),
    "DeepSeek Chat": ("deepseek/deepseek-chat", "https://api.deepseek.com/v1"),
    "OpenRouter": ("anthropic/claude-sonnet-4", "https://openrouter.ai/api/v1"),
    "OpenAI": ("gpt-4o", "https://openrouter.ai/api/v1"),
}

class SettingsDialog(QDialog):
    def __init__(self, agent, parent=None):
        super().__init__(parent); self._agent = agent
        self.setWindowTitle("LLM Settings"); self.setMinimumWidth(450)
        layout = QVBoxLayout(self); form = QFormLayout()
        self._preset = QComboBox(); self._preset.addItems(PRESETS.keys())
        self._preset.currentTextChanged.connect(self._on_preset); form.addRow("Preset:", self._preset)
        self._model = QLineEdit("deepseek/deepseek-v4-pro"); form.addRow("Model:", self._model)
        self._url = QLineEdit("https://api.deepseek.com/v1"); form.addRow("Base URL:", self._url)
        self._key = QLineEdit(); self._key.setEchoMode(QLineEdit.Password); self._key.setPlaceholderText("sk-..."); form.addRow("API Key:", self._key)
        layout.addLayout(form)
        self._test_btn = QPushButton("Test Connection"); self._test_btn.clicked.connect(self._test); layout.addWidget(self._test_btn)
        self._save_btn = QPushButton("Save"); self._save_btn.clicked.connect(self._save); layout.addWidget(self._save_btn)
        self._status = QLabel(""); layout.addWidget(self._status)

    def _on_preset(self, name):
        if name in PRESETS:
            m, u = PRESETS[name]; self._model.setText(m); self._url.setText(u)

    def _test(self):
        self._status.setText("Testing...")
        ok, msg = self._agent.update_llm_settings(self._key.text(), self._model.text(), self._url.text())
        self._status.setText(f"{'OK' if ok else 'FAILED'}: {msg}")

    def _save(self):
        ok, msg = self._agent.update_llm_settings(self._key.text(), self._model.text(), self._url.text())
        if ok: QMessageBox.information(self, "Saved", "LLM config updated."); self.accept()
        else: QMessageBox.warning(self, "Failed", f"Error: {msg}")
