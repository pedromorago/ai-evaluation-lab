"""Checks on a generated test file before anything runs it.

Generated code is untrusted: a file that touches the file system, the
network or other processes is not executed at all. For the rest, each test
function is checked for an actual assertion."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

from . import faults

ALLOWED_IMPORTS = {
    "pytest", "checkout", "decimal", "datetime", "dataclasses", "itertools", "functools",
    "math", "typing", "collections", "re", "fractions", "__future__",
}
FORBIDDEN_CALLS = {"open", "eval", "exec", "compile", "__import__", "breakpoint", "input"}


@dataclass
class FileCheck:
    name: str
    syntax_error: str | None = None
    unsafe: list[str] = field(default_factory=list)
    no_assertion: list[str] = field(default_factory=list)  # test function names
    tests: list[str] = field(default_factory=list)

    @property
    def runnable(self) -> bool:
        if faults.active("unsafe-code-runs"):
            return self.syntax_error is None
        return self.syntax_error is None and not self.unsafe


def _asserts(node: ast.AST, helpers: dict[str, ast.FunctionDef], seen: set[str]) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Assert):
            return True
        if isinstance(sub, ast.Call):
            f = sub.func
            # pytest.raises(...) / pytest.approx is only a check inside an assert, already covered
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "pytest":
                if f.attr == "raises" and not faults.active("no-assert-ignores-raises"):
                    return True
                if f.attr == "fail":
                    return True
            if isinstance(f, ast.Name) and f.id in helpers and f.id not in seen:
                seen.add(f.id)
                if _asserts(helpers[f.id], helpers, seen):
                    return True
    return False


def check(name: str, source: str) -> FileCheck:
    result = FileCheck(name)
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        result.syntax_error = f"{e.msg} (line {e.lineno})"
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                    result.unsafe.append(f"imports {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                result.unsafe.append(f"imports from {node.module}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            result.unsafe.append(f"calls {node.func.id}()")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__") and node.attr not in ("__name__", "__init__"):
            result.unsafe.append(f"uses {node.attr}")

    helpers = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and not n.name.startswith("test")}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            result.tests.append(node.name)
            if not _asserts(node, helpers, set()):
                result.no_assertion.append(node.name)
    return result
