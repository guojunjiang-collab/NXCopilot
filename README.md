# NXCopilot — NX AI CAD 副驾驶

基于 LLM 驱动的 Siemens NX 智能设计助手，支持正向设计、逆向理解和自然语言交互。

```
用户 (自然语言)
  |
  v
PySide6 UI --HTTP--> Agent (FastAPI)
  ^                       |
特征树/对话          LLM (DeepSeek)
                     |
               NXOpen Python 代码生成
                     |
               NXOpen API (同进程)
                     |
                 Siemens NX
```

---

## 核心特性

- **正向设计** — 自然语言描述 -> NXOpen 创建代码 -> 自动建模
- **逆向理解** — 读取特征树 -> LLM 分析 -> AI 读懂当前模型
- **混合修改** — 自然语言修改参数，LLM 定位特征 -> Expression 修改，不改的不动
- **离线可用** — NX 未连接时，LLM 对话 + 代码生成仍可使用

---

## 与 CatiaCopilot 对比

| 维度 | CatiaCopilot | NXCopilot |
|------|-------------|-----------|
| CAD 软件 | CATIA V5 | Siemens NX |
| 连接方式 | pywin32 COM | NXOpen Python (原生) |
| 中间表示 | VBS 代码 | NXOpen Python 代码 |
| 参数修改 | FindObjectByName | Expression 系统 |
| MCP Server | catia-mcp-server (87 tools) | 直接调用 NXOpen (无需 MCP) |
| 代码验证 | VBS 语法检查 | Python ast 模块 |
| 特征类型 | 23 种 | 29 种 |
| 测试 | 302 个 | 45 个 |

---

## 开发进度

**当前状态：阶段 1-3 已完成，阶段 4 待开始**

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | NX Engine 核心 (reader/converter/editor/dependency/validator/expression/forward_builder) | 已完成 |
| Phase 2 | Agent + LLM (orchestrator/session/executor/client/prompts/planner) | 已完成 |
| Phase 3 | UI + 启动器 (PySide6 窗口/对话/特征树/设置/launch_all/spec) | 已完成 |
| Phase 4 | NX 环境实测 (端到端验证读取/修改/创建完整链路) | 待开始 |
| Phase 5 | 特征映射完善 (扩展到 40+ 种特征，20+ 创建模板) | 待开始 |
| Phase 6 | 稳定性与发布 (上下文压缩/回滚/安装包/文档) | 待开始 |

### 代码统计

| 模块 | 文件数 | 说明 |
|------|--------|------|
| nx_engine | 8 | 特征树引擎 (reader/converter/editor/expression/dependency/validator/forward_builder/mapping) |
| agent | 5 | Agent 逻辑 (orchestrator/session_manager/step_planner/forward_planner/understanding_pipeline) |
| nx_bridge | 2 | NX 连接 (session/executor) |
| llm | 3 | LLM 适配 (client/prompts/api_reference) |
| ui | 6 | PySide6 界面 (main_window/chat_panel/feature_tree/settings_dialog/agent_client/launch) |
| tests | 7 | 离线测试 (45 个全部通过) |

---

## 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | >= 3.10 | 推荐 3.11+ |
| Siemens NX | NX 12+ | NXOpen Python API |
| Windows | 10/11 | NX 运行环境 |
| PySide6 | >= 6.5 | UI 前端 |
| LLM API | DeepSeek / OpenRouter / OpenAI | 需要 API Key |

---

## 快速开始

### 安装

```bash
# 1. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 2. 安装 Agent 依赖
cd src\NXCopilot.Agent
pip install -r requirements.txt

# 3. 安装 UI 依赖
pip install PySide6

# 4. 配置 LLM
cp .env.example .env
# 编辑 .env 填入 API Key
```

### 启动

```bash
# 方式一：一键启动 (推荐)
python launch_all.py

# 方式二：分别启动
# 终端 1: Agent
cd src\NXCopilot.Agent
python main.py

# 终端 2: UI
cd src\NXCopilot.UI.PySide6
python launch.py

# 方式三：CLI 模式 (不需要 UI)
cd src\NXCopilot.Agent
python main.py --cli
```

### 配置 LLM

编辑 `src\NXCopilot.Agent\.env`:

```ini
# DeepSeek (默认)
LLM_API_KEY=your-a...n

# Agent 服务
AGENT_HOST=127.0.0.1
AGENT_PORT=8757
```

或在 UI 中点击 "File -> LLM Settings" 配置。

---

## 项目结构

```
NXCopilot/
├── 架构设计.md              # 详细架构文档 (25KB)
├── launch_all.py            # 一键启动
├── NXCopilot.spec           # PyInstaller 打包
│
├── src/
│   ├── NXCopilot.Agent/     # 后端 (Python/FastAPI)
│   │   ├── main.py          # 入口 (HTTP + WebSocket + CLI)
│   │   ├── agent/           # Agent 逻辑
│   │   ├── nx_engine/       # NX 特征树引擎
│   │   ├── nx_bridge/       # NX 连接管理
│   │   └── llm/             # LLM 适配层
│   │
│   └── NXCopilot.UI.PySide6/  # 前端 (PySide6)
│       ├── main_window.py
│       └── widgets/
│
└── tests/                   # 离线单元测试 (45 个)
```

---

## 运行测试

```bash
cd tests
pytest test_nx_engine/ -v
```

```
tests/test_nx_engine/test_converter.py      4 passed
tests/test_nx_engine/test_dependency.py     4 passed
tests/test_nx_engine/test_editor.py         5 passed
tests/test_nx_engine/test_expression.py     4 passed
tests/test_nx_engine/test_forward_builder.py 15 passed
tests/test_nx_engine/test_reader.py         5 passed
tests/test_nx_engine/test_validator.py      6 passed
-----------------------------------------------
45 passed in 0.09s
```

---

## 典型使用场景

### 正向设计
```
You: "拉伸20mm，然后打一个直径10的孔"
NXCopilot: 生成 Extrude + Hole 的 NXOpen 创建代码 -> 执行
```

### 逆向理解
```
You: "分析当前零件结构"
NXCopilot: 读取特征树 -> LLM 分析 -> "这是一个法兰盘，有基体、中心孔、螺栓孔阵列..."
```

### 混合修改
```
You: "把孔径改成12mm"
NXCopilot: 读取特征树 -> LLM 定位 HOLE -> Expression 修改 Diameter -> 执行
```

### 离线代码生成 (NX 未连接)
```
You: "帮我写一个创建齿轮的 NXOpen 脚本"
NXCopilot: LLM 生成完整代码 -> 复制到 NX Journal 执行
```

---

## License

MIT
