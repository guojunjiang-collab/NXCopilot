# -*- coding: utf-8 -*-
"""NXCopilot UI 启动脚本。"""
import sys, os, argparse
UI_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(os.path.dirname(UI_DIR), "NXCopilot.Agent")
for d in [UI_DIR, AGENT_DIR]:
    if d not in sys.path: sys.path.insert(0, d)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-url", default="http://127.0.0.1:8757")
    args = parser.parse_args()
    from PySide6.QtWidgets import QApplication
    from main_window import MainWindow
    app = QApplication(sys.argv)
    app.setApplicationName("NXCopilot")
    window = MainWindow(agent_url=args.agent_url)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__": main()
