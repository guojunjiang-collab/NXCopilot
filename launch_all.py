# -*- coding: utf-8 -*-
"""NXCopilot — 一键启动 Agent + UI。"""
import os, sys, subprocess, time, signal, httpx

PROJ = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(PROJ, "src", "NXCopilot.Agent")
UI_DIR = os.path.join(PROJ, "src", "NXCopilot.UI.PySide6")
PORT = int(os.getenv("AGENT_PORT", "8757"))
URL = f"http://127.0.0.1:{PORT}"

def main():
    procs = []
    def cleanup(*a):
        for p in procs:
            try: p.terminate()
            except: pass
        sys.exit(0)
    signal.signal(signal.SIGINT, cleanup); signal.signal(signal.SIGTERM, cleanup)

    print(f"[NXCopilot] Starting Agent on port {PORT}...")
    procs.append(subprocess.Popen([sys.executable, "main.py", "--port", str(PORT)], cwd=AGENT_DIR))

    for _ in range(30):
        try:
            if httpx.get(f"{URL}/health", timeout=2).status_code == 200: print("[NXCopilot] Agent ready!"); break
        except: pass
        time.sleep(1)

    print("[NXCopilot] Starting UI...")
    procs.append(subprocess.Popen([sys.executable, "launch.py", "--agent-url", URL], cwd=UI_DIR))
    print("[NXCopilot] All started. Ctrl+C to stop.")
    procs[-1].wait(); cleanup()

if __name__ == "__main__": main()
