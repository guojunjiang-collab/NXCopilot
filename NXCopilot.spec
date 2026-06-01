# -*- mode: python ; coding: utf-8 -*-
"""NXCopilot PyInstaller spec — 文件夹模式。构建: pyinstaller NXCopilot.spec"""
import os

PROJ = r"D:\OpenCode\NXCopilot"
SRC = os.path.join(PROJ, "src")
AGENT = os.path.join(SRC, "NXCopilot.Agent")
UI = os.path.join(SRC, "NXCopilot.UI.PySide6")

a = Analysis(
    [os.path.join(PROJ, 'launch_all.py')],
    pathex=[PROJ, SRC, AGENT, UI],
    binaries=[],
    datas=[
        (os.path.join(AGENT, 'llm', 'prompts', 'nxopen_api_reference.md'),
         os.path.join('src', 'NXCopilot.Agent', 'llm', 'prompts')),
        (os.path.join(AGENT, 'nx_engine', 'feature_mapping.yaml'),
         os.path.join('src', 'NXCopilot.Agent', 'nx_engine')),
        (os.path.join(AGENT, '.env.example'),
         os.path.join('src', 'NXCopilot.Agent')),
    ],
    hiddenimports=[
        'fastapi', 'uvicorn', 'uvicorn.logging', 'uvicorn.loops',
        'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'PySide6.QtWidgets', 'PySide6.QtCore', 'PySide6.QtGui',
        'agent', 'agent.orchestrator', 'agent.step_planner',
        'agent.forward_planner', 'agent.session_manager',
        'agent.understanding_pipeline',
        'llm', 'llm.client', 'llm.prompts',
        'nx_engine', 'nx_engine.reader', 'nx_engine.editor',
        'nx_engine.converter', 'nx_engine.dependency',
        'nx_engine.validator', 'nx_engine.expression',
        'nx_engine.forward_builder',
        'nx_bridge', 'nx_bridge.session', 'nx_bridge.executor',
        'main_window', 'agent_client',
        'widgets', 'widgets.chat_panel', 'widgets.feature_tree',
        'widgets.settings_dialog',
        'pydantic', 'httpx', 'yaml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='NXCopilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas, [],
    strip=False, upx=True,
    upx_exclude=[],
    name='NXCopilot',
)
