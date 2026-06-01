# -*- coding: utf-8 -*-
"""NXCopilot NX Engine — 依赖关系管理（有向图 + 拓扑排序）。"""

from __future__ import annotations
import logging
from collections import defaultdict, deque
from typing import Optional
from nx_engine.reader import FeatureNode, FeatureTreeSnapshot

logger = logging.getLogger("nxcopilot.nx_engine.dependency")


class DependencyGraph:
    def __init__(self):
        self._edges: dict[str, list[str]] = defaultdict(list)
        self._reverse: dict[str, list[str]] = defaultdict(list)
        self._nodes: set[str] = set()

    def build_from_features(self, features: list[FeatureNode]) -> None:
        self._edges.clear(); self._reverse.clear(); self._nodes.clear()
        for feat in features:
            self._nodes.add(feat.name)
            for dep in feat.depends_on:
                self._edges[feat.name].append(dep)
                self._reverse[dep].append(feat.name)

    def build_from_snapshot(self, snapshot: FeatureTreeSnapshot) -> None:
        self.build_from_features(snapshot.features)

    def topological_sort(self) -> list[str]:
        in_degree = {n: 0 for n in self._nodes}
        for node in self._nodes:
            for dep in self._edges.get(node, []):
                if dep in self._nodes:
                    in_degree[node] += 1
        queue = deque(n for n, d in in_degree.items() if d == 0)
        result = []
        while queue:
            node = queue.popleft()
            result.append(node)
            for dep in self._reverse.get(node, []):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
        return result

    def get_dependents(self, name: str) -> list[str]:
        return list(self._reverse.get(name, []))

    def get_all_dependents(self, name: str) -> set[str]:
        visited = set()
        queue = deque([name])
        while queue:
            cur = queue.popleft()
            for dep in self._reverse.get(cur, []):
                if dep not in visited:
                    visited.add(dep)
                    queue.append(dep)
        return visited

    def can_safely_remove(self, name: str) -> tuple[bool, list[str]]:
        affected = list(self.get_all_dependents(name))
        return len(affected) == 0, affected

    def get_insertion_points(self, new_name: str, deps: list[str]) -> Optional[str]:
        topo = self.topological_sort()
        if not topo:
            return None
        last_idx = -1
        for dep in deps:
            if dep in topo:
                last_idx = max(last_idx, topo.index(dep))
        return topo[min(last_idx + 1, len(topo) - 1)] if last_idx >= 0 else topo[-1]


class EditValidator:
    def validate_edit(self, old_snapshot, new_features: list[FeatureNode]) -> tuple[bool, list[str]]:
        errors = []
        graph = DependencyGraph()
        graph.build_from_features(new_features)
        name_set = {f.name for f in new_features}
        for feat in new_features:
            for dep in feat.depends_on:
                if dep not in name_set:
                    errors.append(f"{feat.name} depends on missing feature {dep}")
        topo = graph.topological_sort()
        if len(topo) < len(new_features):
            errors.append("Cycle detected")
        return len(errors) == 0, errors
