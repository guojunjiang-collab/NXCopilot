# NXCopilot — NX AI CAD 副驾驶

基于 LLM 驱动的 Siemens NX 智能设计助手，支持正向设计、逆向理解和自然语言交互。

```
用户 (自然语言)
  ↓
PySide6 UI ──HTTP──→ Agent (FastAPI)
  ↑                       ↓
特征树/对话          LLM (DeepSeek)
                     ↓
               NXOpen Python 代码生成
                     ↓
               NXOpen API (同进程)
                     ↓
                 Siemens NX
```

## 与 CatiaCopilot 对比

| 维度 | CatiaCopilot | NXCopilot |
|------|-------------|-----------|
| CAD 软件 | CATIA V5 | Siemens NX |
| 连接方式 | pywin32 COM | NXOpen Python (原生) |
| 中间表示 | VBS 代码 | NXOpen Python 代码 |
| 参数修改 | FindObjectByName | Expression 系统 |
| MCP Server | catia-mcp-server (87 tools) | 直接调用 NXOpen |

## 环境要求

- Python >= 3.10, PySide6 >= 6.5, Windows 10/11
- Siemens NX 12+ (NXOpen Python API)
- LLM API Key (DeepSeek / OpenRouter / OpenAI)

## 快速开始

```bash
# 安装
python -m venv .venv && .venv\Scripts\activate
cd src\NXCopilot.Agent && pip install -r requirements.txt && pip install PySide6
cp .env.example .env  # 编辑填入 API Key

# 启动
python launch_all.py              # 一键启动
python src\NXCopilot.Agent\main.py --cli  # CLI 模式
```

## 项目结构

```
NXCopilot/
├── launch_all.py              # 一键启动
├── src/
│   ├── NXCopilot.Agent/       # 后端 (FastAPI)
│   │   ├── main.py            # 入口
│   │   ├── agent/             # Agent 逻辑 (orchestrator/planner)
│   │   ├── nx_engine/         # NX 特征树引擎 (reader/converter/editor)
│   │   ├── nx_bridge/         # NX 连接管理 (session/executor)
│   │   └── llm/               # LLM 适配层
│   └── NXCopilot.UI.PySide6/  # 前端 (PySide6)
└── tests/                     # 离线单元测试
```

## 测试

```bash
cd tests && pytest test_nx_engine/ -v
```
