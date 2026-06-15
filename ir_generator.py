"""
=============================================================
  GERADOR DE CÓDIGO INTERMEDIÁRIO
  Representação: Código de Três Endereços (TAC)
  Formato: result = arg1 op arg2   |   goto L   |   ifFalse x goto L
=============================================================
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union
from ast_nodes import *


# ── TAC Instructions ─────────────────────────────────────────
@dataclass
class TACInstr:
    pass

@dataclass
class TACAssign(TACInstr):
    """dest = src"""
    dest: str
    src:  str
    def __str__(self): return f"    {self.dest} = {self.src}"

@dataclass
class TACBinOp(TACInstr):
    """dest = left op right"""
    dest:  str
    left:  str
    op:    str
    right: str
    def __str__(self): return f"    {self.dest} = {self.left} {self.op} {self.right}"

@dataclass
class TACUnary(TACInstr):
    """dest = op src"""
    dest: str
    op:   str
    src:  str
    def __str__(self): return f"    {self.dest} = {self.op}{self.src}"

@dataclass
class TACLabel(TACInstr):
    """L0:"""
    name: str
    def __str__(self): return f"{self.name}:"

@dataclass
class TACGoto(TACInstr):
    """goto L"""
    label: str
    def __str__(self): return f"    goto {self.label}"

@dataclass
class TACIfFalse(TACInstr):
    """if_false cond goto L"""
    cond:  str
    label: str
    def __str__(self): return f"    if_false {self.cond} goto {self.label}"

@dataclass
class TACPrint(TACInstr):
    """print src"""
    src: str
    def __str__(self): return f"    print {self.src}"

@dataclass
class TACRead(TACInstr):
    """read dest"""
    dest: str
    def __str__(self): return f"    read {self.dest}"

@dataclass
class TACCopy(TACInstr):
    """dest = src  (alias for clarity)"""
    dest: str
    src:  str
    def __str__(self): return f"    {self.dest} = {self.src}"


# ── IR Generator ─────────────────────────────────────────────
class IRGenerator:
    def __init__(self):
        self.code:    List[TACInstr] = []
        self._tmp_cnt = 0
        self._lbl_cnt = 0

    # ── helpers ──────────────────────────────────────────────
    def _new_tmp(self) -> str:
        t = f"t{self._tmp_cnt}"
        self._tmp_cnt += 1
        return t

    def _new_label(self) -> str:
        l = f"L{self._lbl_cnt}"
        self._lbl_cnt += 1
        return l

    def emit(self, instr: TACInstr):
        self.code.append(instr)

    # ── entry ────────────────────────────────────────────────
    def generate(self, program: Program) -> List[TACInstr]:
        for stmt in program.statements:
            self._gen_stmt(stmt)
        return self.code

    # ── statements ───────────────────────────────────────────
    def _gen_stmt(self, node: ASTNode):
        if isinstance(node, VarDecl):
            if node.init:
                val = self._gen_expr(node.init)
                self.emit(TACAssign(node.name, val))
            else:
                # Inicialização padrão
                default = "0" if node.var_type == 'int' else "false"
                self.emit(TACAssign(node.name, default))

        elif isinstance(node, Assign):
            val = self._gen_expr(node.value)
            self.emit(TACAssign(node.name, val))

        elif isinstance(node, If):
            cond      = self._gen_expr(node.condition)
            else_lbl  = self._new_label()
            end_lbl   = self._new_label()
            self.emit(TACIfFalse(cond, else_lbl if node.else_body else end_lbl))
            for s in node.then_body:
                self._gen_stmt(s)
            if node.else_body:
                self.emit(TACGoto(end_lbl))
                self.emit(TACLabel(else_lbl))
                for s in node.else_body:
                    self._gen_stmt(s)
            self.emit(TACLabel(end_lbl if node.else_body else (else_lbl if not node.else_body else end_lbl)))

        elif isinstance(node, While):
            start_lbl = self._new_label()
            end_lbl   = self._new_label()
            self.emit(TACLabel(start_lbl))
            cond = self._gen_expr(node.condition)
            self.emit(TACIfFalse(cond, end_lbl))
            for s in node.body:
                self._gen_stmt(s)
            self.emit(TACGoto(start_lbl))
            self.emit(TACLabel(end_lbl))

        elif isinstance(node, Print):
            val = self._gen_expr(node.expr)
            self.emit(TACPrint(val))

        elif isinstance(node, Read):
            self.emit(TACRead(node.name))

    # ── expressions → returns operand name ───────────────────
    def _gen_expr(self, node: ASTNode) -> str:
        if isinstance(node, IntLiteral):
            return str(node.value)
        if isinstance(node, BoolLiteral):
            return "true" if node.value else "false"
        if isinstance(node, StringLiteral):
            return f'"{node.value}"'
        if isinstance(node, VarRef):
            return node.name

        if isinstance(node, BinOp):
            l = self._gen_expr(node.left)
            r = self._gen_expr(node.right)
            t = self._new_tmp()
            self.emit(TACBinOp(t, l, node.op, r))
            return t

        if isinstance(node, UnaryOp):
            s = self._gen_expr(node.expr)
            t = self._new_tmp()
            self.emit(TACUnary(t, node.op, s))
            return t

        raise ValueError(f"IR: nó não suportado: {type(node).__name__}")

    # ── pretty print ─────────────────────────────────────────
    def dump(self) -> str:
        lines = ["╔══════════════════════════════════════════╗",
                 "║   CÓDIGO INTERMEDIÁRIO (TAC)              ║",
                 "╚══════════════════════════════════════════╝"]
        for instr in self.code:
            lines.append(str(instr))
        return "\n".join(lines)
