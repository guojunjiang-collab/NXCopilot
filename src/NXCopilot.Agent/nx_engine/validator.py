# -*- coding: utf-8 -*-
"""NXCopilot NX Engine — NXOpen 代码结构验证器。"""

from __future__ import annotations
import ast
import re
from dataclasses import dataclass, field

_DANGEROUS = [
    (r'os\.remove|os\.unlink|shutil\.rmtree', "Dangerous file deletion"),
    (r'subprocess\.', "Subprocess not allowed"),
    (r'__import__', "Dynamic import not allowed"),
    (r'eval\(', "eval() not allowed"),
    (r'exec\(', "exec() not allowed"),
]


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class NXCodeValidator:
    def validate_python_syntax(self, code: str) -> ValidationResult:
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"SyntaxError at line {e.lineno}: {e.msg}")
        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_nxopen_safety(self, code: str) -> ValidationResult:
        errors, warnings = [], []
        for pat, desc in _DANGEROUS:
            if re.search(pat, code):
                errors.append(f"Dangerous: {desc}")
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_references(self, code: str, known: list[str]) -> ValidationResult:
        errors = []
        known_set = set(known)
        refs = re.findall(r'FindObject\(["\']([^"\']+)["\']\)', code)
        for ref in refs:
            if ref not in known_set:
                errors.append(f"Unknown feature reference: {ref}")
        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate(self, code: str, known_features: list[str] | None = None) -> ValidationResult:
        all_errors, all_warnings = [], []
        r1 = self.validate_python_syntax(code)
        all_errors.extend(r1.errors)
        r2 = self.validate_nxopen_safety(code)
        all_errors.extend(r2.errors)
        all_warnings.extend(r2.warnings)
        if known_features:
            r3 = self.validate_references(code, known_features)
            all_errors.extend(r3.errors)
        return ValidationResult(valid=len(all_errors) == 0, errors=all_errors, warnings=all_warnings)
