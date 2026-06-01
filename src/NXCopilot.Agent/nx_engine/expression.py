# -*- coding: utf-8 -*-
"""NXCopilot NX Engine — NX Expression 管理器。"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("nxcopilot.nx_engine.expression")


@dataclass
class NXExpression:
    name: str
    value: float
    unit: str = "MilliMeter"


class ExpressionManager:
    def __init__(self, work_part=None):
        self._part = work_part

    def set_part(self, work_part) -> None:
        self._part = work_part

    def read_all(self) -> list[NXExpression]:
        if self._part is None:
            return []
        result = []
        try:
            for expr in self._part.Expressions:
                try:
                    result.append(NXExpression(name=expr.Name, value=expr.Value))
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Failed to read expressions: {e}")
        return result

    def find(self, name: str) -> Optional[NXExpression]:
        if self._part is None:
            return None
        try:
            expr = self._part.Expressions.FindObject(name)
            if expr:
                return NXExpression(name=expr.Name, value=expr.Value)
        except Exception:
            pass
        return None

    def edit(self, name: str, new_value: float, unit_name: str = "MilliMeter") -> bool:
        if self._part is None:
            return False
        try:
            expr = self._part.Expressions.FindObject(name)
            unit = self._part.UnitCollection.FindObject(unit_name)
            self._part.Expressions.EditWithUnits(expr, unit, str(new_value))
            return True
        except Exception as e:
            logger.error(f"Failed to edit expression {name}: {e}")
            return False

    def create(self, name: str, value: float, unit_name: str = "MilliMeter") -> bool:
        if self._part is None:
            return False
        try:
            unit = self._part.UnitCollection.FindObject(unit_name)
            self._part.Expressions.CreateWithUnits(name, unit, str(value))
            return True
        except Exception as e:
            logger.error(f"Failed to create expression {name}: {e}")
            return False

    def to_dict(self) -> dict[str, float]:
        return {e.name: e.value for e in self.read_all()}
