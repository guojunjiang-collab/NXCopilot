# -*- coding: utf-8 -*-
"""NXCopilot Agent — 主入口（FastAPI + CLI）。"""
from __future__ import annotations
import argparse, asyncio, json, logging, os, sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SRC not in sys.path: sys.path.insert(0, os.path.join(SRC, "NXCopilot.Agent"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("nxcopilot")

def create_app():
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from agent.orchestrator import NXCopilotOrchestrator
    from llm.client import LLMConfig

    app = FastAPI(title="NXCopilot Agent", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    orch = NXCopilotOrchestrator()

    @app.on_event("startup")
    async def startup():
        nx_ok = orch.connect_nx()
        logger.info(f"NX: {'OK' if nx_ok else 'OFFLINE'}")
        try:
            cfg = LLMConfig.from_env()
            if cfg.api_key: orch.set_llm_config(cfg); logger.info(f"LLM: {cfg.model}")
        except Exception as e: logger.warning(f"LLM: {e}")

    @app.get("/health")
    async def health():
        return {"status":"ok","nx_connected":orch.is_connected(),"llm_ready":orch._llm_ready}

    @app.get("/model")
    async def model():
        return orch._get_tree_summary() if orch.is_connected() else {"error":"NX not connected"}

    class ChatReq(BaseModel):
        message: str

    @app.post("/chat")
    async def chat(req: ChatReq):
        return await orch.handle_message(req.message)

    class LLMReq(BaseModel):
        api_key: str; model: str = "deepseek/deepseek-v4-pro"; base_url: str = "https://api.deepseek.com/v1"

    @app.post("/settings/llm")
    async def llm_settings(req: LLMReq):
        from llm.client import LLMConfig
        cfg = LLMConfig(api_key=req.api_key, model=req.model, base_url=req.base_url)
        orch.set_llm_config(cfg)
        ok, msg = orch._llm_client.test_connection()
        return {"success": ok, "message": msg}

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await ws.accept()
        try:
            while True:
                data = json.loads(await ws.receive_text())
                result = await orch.handle_message(data.get("message",""))
                await ws.send_text(json.dumps(result, ensure_ascii=False))
        except WebSocketDisconnect: pass

    return app

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", action="store_true")
    parser.add_argument("--host", default=os.getenv("AGENT_HOST","127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("AGENT_PORT","8757")))
    args = parser.parse_args()

    if args.cli:
        from agent.orchestrator import NXCopilotOrchestrator
        from llm.client import LLMConfig
        orch = NXCopilotOrchestrator()
        nx_ok = orch.connect_nx(); print(f"NX: {'Connected' if nx_ok else 'Offline'}")
        try:
            cfg = LLMConfig.from_env()
            if cfg.api_key: orch.set_llm_config(cfg); print(f"LLM: {cfg.model}")
        except: pass
        print("NXCopilot CLI ready. Type 'quit' to exit.\n")
        while True:
            try: inp = input("You: ").strip()
            except (EOFError, KeyboardInterrupt): break
            if inp.lower() in ("quit","exit","q"): break
            if not inp: continue
            r = asyncio.run(orch.handle_message(inp))
            print(f"\n[{r.get('intent')}]: {r.get('reply','')}\n")
            if r.get("nxopen_code"): print(f"--- Code ---\n{r['nxopen_code']}\n---")
        print("Bye!")
    else:
        import uvicorn
        print(f"Starting NXCopilot Agent on {args.host}:{args.port}")
        uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")

if __name__ == "__main__": main()
