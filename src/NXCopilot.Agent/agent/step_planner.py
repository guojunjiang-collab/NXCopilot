# -*- coding: utf-8 -*-
"""NXCopilot Agent — 多步骤任务规划器。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class Step:
    step_id: int
    description: str
    action_type: str
    status: str = "pending"
    result: Any = None

@dataclass
class ExecutionPlan:
    steps: list[Step] = field(default_factory=list)
    current: int = 0
    def next(self) -> Optional[Step]:
        if self.current < len(self.steps):
            s = self.steps[self.current]; self.current += 1; return s
        return None

class StepPlanner:
    def plan_modification(self, user_input: str, has_model: bool) -> ExecutionPlan:
        steps, sid = [], 1
        if has_model:
            steps.append(Step(sid, "读取特征树", "read_model")); sid += 1
        steps.append(Step(sid, "LLM 生成修改代码", "generate_code")); sid += 1
        steps.append(Step(sid, "验证代码", "validate")); sid += 1
        steps.append(Step(sid, "执行修改", "execute")); sid += 1
        steps.append(Step(sid, "生成回复", "respond"))
        return ExecutionPlan(steps=steps)

    def plan_creation(self, user_input: str) -> ExecutionPlan:
        steps, sid = [], 1
        steps.append(Step(sid, "LLM 解析需求", "parse")); sid += 1
        steps.append(Step(sid, "生成创建代码", "generate")); sid += 1
        steps.append(Step(sid, "执行创建", "execute")); sid += 1
        steps.append(Step(sid, "生成回复", "respond"))
        return ExecutionPlan(steps=steps)
