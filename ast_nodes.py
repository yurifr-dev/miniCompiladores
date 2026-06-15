"""
=============================================================
  NÓS DA ÁRVORE DE SINTAXE ABSTRATA (AST)
  Cada nó representa um construto da linguagem.
=============================================================
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


# ── Base ──────────────────────────────────────────────────────
class ASTNode:
    pass


# ── Statements ───────────────────────────────────────────────
@dataclass
class Program(ASTNode):
    """Nó raiz: sequência de declarações."""
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class VarDecl(ASTNode):
    """Declaração de variável: tipo nome [= expr];"""
    var_type: str     # 'int' | 'bool'
    name:     str
    init:     Optional[ASTNode]
    line:     int = 0


@dataclass
class Assign(ASTNode):
    """Atribuição: nome = expr;"""
    name:  str
    value: ASTNode
    line:  int = 0


@dataclass
class If(ASTNode):
    """if (cond) { then } [else { else_ }]"""
    condition:  ASTNode
    then_body:  List[ASTNode]
    else_body:  List[ASTNode] = field(default_factory=list)
    line:       int = 0


@dataclass
class While(ASTNode):
    """while (cond) { body }"""
    condition: ASTNode
    body:      List[ASTNode]
    line:      int = 0


@dataclass
class Print(ASTNode):
    """print(expr);"""
    expr: ASTNode
    line: int = 0


@dataclass
class Read(ASTNode):
    """read(nome);"""
    name: str
    line: int = 0


@dataclass
class Block(ASTNode):
    """Bloco de statements entre { }"""
    statements: List[ASTNode]


# ── Expressions ──────────────────────────────────────────────
@dataclass
class BinOp(ASTNode):
    """Operação binária: left op right"""
    op:    str
    left:  ASTNode
    right: ASTNode
    line:  int = 0


@dataclass
class UnaryOp(ASTNode):
    """Operação unária: op expr"""
    op:   str
    expr: ASTNode
    line: int = 0


@dataclass
class IntLiteral(ASTNode):
    value: int
    line:  int = 0


@dataclass
class BoolLiteral(ASTNode):
    value: bool
    line:  int = 0


@dataclass
class StringLiteral(ASTNode):
    value: str
    line:  int = 0


@dataclass
class VarRef(ASTNode):
    """Referência a variável."""
    name: str
    line: int = 0


# ── Pretty printer ───────────────────────────────────────────
def ast_to_str(node: ASTNode, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(node, Program):
        inner = "\n".join(ast_to_str(s, indent+1) for s in node.statements)
        return f"{pad}Program:\n{inner}"
    if isinstance(node, VarDecl):
        init = f" = {ast_to_str(node.init)}" if node.init else ""
        return f"{pad}VarDecl({node.var_type} {node.name}{init})"
    if isinstance(node, Assign):
        return f"{pad}Assign({node.name} = {ast_to_str(node.value)})"
    if isinstance(node, If):
        then = "\n".join(ast_to_str(s, indent+1) for s in node.then_body)
        else_ = ""
        if node.else_body:
            else_ = "\n" + pad + "  else:\n" + "\n".join(ast_to_str(s, indent+2) for s in node.else_body)
        return f"{pad}If({ast_to_str(node.condition)}):\n{then}{else_}"
    if isinstance(node, While):
        body = "\n".join(ast_to_str(s, indent+1) for s in node.body)
        return f"{pad}While({ast_to_str(node.condition)}):\n{body}"
    if isinstance(node, Print):
        return f"{pad}Print({ast_to_str(node.expr)})"
    if isinstance(node, Read):
        return f"{pad}Read({node.name})"
    if isinstance(node, BinOp):
        return f"({ast_to_str(node.left)} {node.op} {ast_to_str(node.right)})"
    if isinstance(node, UnaryOp):
        return f"({node.op}{ast_to_str(node.expr)})"
    if isinstance(node, IntLiteral):
        return str(node.value)
    if isinstance(node, BoolLiteral):
        return "true" if node.value else "false"
    if isinstance(node, StringLiteral):
        return f'"{node.value}"'
    if isinstance(node, VarRef):
        return node.name
    return repr(node)
