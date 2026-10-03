"""A small mutation engine for the system under test.

Each mutant changes one thing in pricing.py: a comparison, an operator, a
constant, a rounding mode, a deleted statement. A test suite "kills" a mutant
when at least one of its tests fails on it. Every rule in pricing.py carries the
acceptance criterion it implements, so each mutant also knows which criterion
it breaks."""

from __future__ import annotations

import ast
import copy
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from . import SUT, faults

AC_TAG = re.compile(r"#\s*(S\d+-AC\d+)\s*$")

COMPARE_SWAPS = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.In: ast.NotIn, ast.NotIn: ast.In,
    ast.Is: ast.IsNot, ast.IsNot: ast.Is,
}
BINOP_SWAPS = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult}
SYMBOL = {
    ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!=",
    ast.In: "in", ast.NotIn: "not in", ast.Is: "is", ast.IsNot: "is not",
    ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
}
ROUNDING_SWAPS = {"ROUND_HALF_UP": "ROUND_HALF_EVEN"}


@dataclass(frozen=True)
class Mutant:
    id: str
    operator: str
    line: int
    ac: str | None
    change: str
    source: str


def _bump(text: str) -> str:
    """Decimal("50.00") -> "50.01", Decimal("0.15") -> "0.16": one unit in the last place."""
    d = Decimal(text)
    return str(d + Decimal(1).scaleb(d.as_tuple().exponent))


def _sites(tree: ast.Module):
    """Yields (index in ast.walk order, operator, description) for every place a mutant can go.
    Only code inside functions is mutated."""
    inside: set[int] = set()
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef):
            for node in ast.walk(fn):
                inside.add(id(node))
            for arg in ast.walk(fn.args):  # default values and annotations are not behaviour under test
                inside.discard(id(arg))
            for deco in fn.decorator_list:
                for node in ast.walk(deco):
                    inside.discard(id(node))
            if fn.returns is not None:
                for node in ast.walk(fn.returns):
                    inside.discard(id(node))
    for i, node in enumerate(ast.walk(tree)):
        if id(node) not in inside:
            continue
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in COMPARE_SWAPS:
            op = type(node.ops[0])
            yield i, "relational", f"`{SYMBOL[op]}` → `{SYMBOL[COMPARE_SWAPS[op]]}`"
        elif isinstance(node, (ast.BinOp, ast.AugAssign)) and type(node.op) in BINOP_SWAPS:
            op = type(node.op)
            yield i, "arithmetic", f"`{SYMBOL[op]}` → `{SYMBOL[BINOP_SWAPS[op]]}`"
        elif isinstance(node, ast.BoolOp):
            yield i, "logical", "`and` ↔ `or`"
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            yield i, "negation", "drop `not`"
        elif isinstance(node, ast.Constant) and type(node.value) is int:
            yield i, "constant", f"`{node.value}` → `{node.value + 1}`"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name == "Decimal" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                text = node.args[0].value
                yield i, "constant", f'`Decimal("{text}")` → `Decimal("{_bump(text)}")`'
            elif name in ("min", "max"):
                yield i, "call", f"`{name}` → `{'max' if name == 'min' else 'min'}`"
            elif name == "_cents" and node.args:
                yield i, "rounding", "drop the rounding to cents"
        elif isinstance(node, ast.Name) and node.id in ROUNDING_SWAPS:
            yield i, "rounding", f"`{node.id}` → `{ROUNDING_SWAPS[node.id]}`"
        elif isinstance(node, ast.Raise):
            yield i, "statement", "delete the `raise`"
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            yield i, "statement", "delete the call"


def _replace(tree: ast.Module, old: ast.AST, new: ast.AST) -> None:
    for parent in ast.walk(tree):
        for field, value in ast.iter_fields(parent):
            if value is old:
                setattr(parent, field, new)
                return
            if isinstance(value, list):
                for k, item in enumerate(value):
                    if item is old:
                        value[k] = new
                        return
    raise LookupError("node not found")


def _apply(tree: ast.Module, index: int) -> None:
    node = list(ast.walk(tree))[index]
    if isinstance(node, ast.Compare):
        node.ops = [COMPARE_SWAPS[type(node.ops[0])]()]
    elif isinstance(node, (ast.BinOp, ast.AugAssign)):
        node.op = BINOP_SWAPS[type(node.op)]()
    elif isinstance(node, ast.BoolOp):
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
    elif isinstance(node, ast.UnaryOp):
        _replace(tree, node, node.operand)
    elif isinstance(node, ast.Constant):
        node.value = node.value + 1
    elif isinstance(node, ast.Call):
        name = node.func.id
        if name == "Decimal":
            node.args[0].value = _bump(node.args[0].value)
        elif name in ("min", "max"):
            node.func.id = "max" if name == "min" else "min"
        else:  # _cents(x) -> x
            _replace(tree, node, node.args[0])
    elif isinstance(node, ast.Name):
        node.id = ROUNDING_SWAPS[node.id]
    elif isinstance(node, (ast.Raise, ast.Expr)):
        _replace(tree, node, ast.Pass())


def ac_by_line(source: str) -> dict[int, str]:
    tags = {}
    for n, text in enumerate(source.splitlines(), start=1):
        m = AC_TAG.search(text)
        if m:
            tags[n] = m.group(1)
    return tags


def mutants(path: Path | None = None) -> list[Mutant]:
    path = path or SUT / "pricing.py"
    source = path.read_text()
    tree = ast.parse(source)
    tags = ac_by_line(source)
    lines = source.splitlines()
    out = []
    for k, (index, operator, change) in enumerate(_sites(tree), start=1):
        mutated = copy.deepcopy(tree)
        _apply(mutated, index)
        line = list(ast.walk(tree))[index].lineno
        tag_line = line + 1 if faults.active("ac-map-off-by-one") else line
        out.append(Mutant(
            id=f"M{k:03d}",
            operator=operator,
            line=line,
            ac=tags.get(tag_line),
            change=f"line {line}: {change} in `{lines[line - 1].split('#')[0].strip()}`",
            source=ast.unparse(mutated) + "\n",
        ))
    return out
