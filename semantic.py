"""
=============================================================
  ANALISADOR SEMÂNTICO
  - Tabela de Símbolos com escopo aninhado
  - Verificação de tipos (Type Checking)
  - Verificação de variáveis declaradas antes do uso
  - Verificação de compatibilidade de operadores
=============================================================
"""

from typing import Dict, List, Optional, Tuple
from ast_nodes import *


# ── Symbol / SymbolTable ──────────────────────────────────────
class SemanticError(Exception):
    def __init__(self, msg: str, line: int = 0):
        super().__init__(f"[Semântico] Erro na linha {line}: {msg}")
        self.line = line


class Symbol:
    def __init__(self, name: str, sym_type: str, line: int):
        self.name     = name
        self.sym_type = sym_type   # 'int' | 'bool' | 'string'
        self.line     = line
        self.used     = False

    def __repr__(self):
        return f"Symbol({self.name}: {self.sym_type})"


class SymbolTable:
    """
    Tabela de símbolos com suporte a escopos aninhados.
    Cada bloco (if/while) cria um novo escopo filho.
    """

    def __init__(self, parent: Optional["SymbolTable"] = None):
        self._table: Dict[str, Symbol] = {}
        self.parent = parent

    def declare(self, name: str, sym_type: str, line: int):
        if name in self._table:
            raise SemanticError(
                f"Variável '{name}' já declarada neste escopo", line
            )
        self._table[name] = Symbol(name, sym_type, line)

    def lookup(self, name: str) -> Optional[Symbol]:
        if name in self._table:
            return self._table[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def require(self, name: str, line: int) -> Symbol:
        sym = self.lookup(name)
        if sym is None:
            raise SemanticError(f"Variável '{name}' não declarada", line)
        sym.used = True
        return sym

    def all_symbols(self) -> List[Symbol]:
        return list(self._table.values())

    def child(self) -> "SymbolTable":
        return SymbolTable(parent=self)


# ── Type system helpers ───────────────────────────────────────
ARITHMETIC_OPS = {'+', '-', '*', '/'}
RELATIONAL_OPS = {'<', '>', '<=', '>='}
EQUALITY_OPS   = {'==', '!='}
LOGICAL_OPS    = {'&&', '||'}


def _check_binop(op: str, lt: str, rt: str, line: int) -> str:
    """Returns result type or raises SemanticError."""
    if op in ARITHMETIC_OPS:
        if lt != 'int' or rt != 'int':
            raise SemanticError(
                f"Operador '{op}' requer int × int, mas recebeu {lt} × {rt}", line
            )
        return 'int'
    if op in RELATIONAL_OPS:
        if lt != 'int' or rt != 'int':
            raise SemanticError(
                f"Operador '{op}' requer int × int, mas recebeu {lt} × {rt}", line
            )
        return 'bool'
    if op in EQUALITY_OPS:
        if lt != rt:
            raise SemanticError(
                f"Operador '{op}' requer operandos do mesmo tipo, mas recebeu {lt} × {rt}", line
            )
        return 'bool'
    if op in LOGICAL_OPS:
        if lt != 'bool' or rt != 'bool':
            raise SemanticError(
                f"Operador '{op}' requer bool × bool, mas recebeu {lt} × {rt}", line
            )
        return 'bool'
    raise SemanticError(f"Operador desconhecido: '{op}'", line)


# ── Semantic Analyzer ─────────────────────────────────────────
class SemanticAnalyzer:
    """
    Visitor pattern sobre a AST.
    Retorna o tipo inferido de cada expressão.
    Popula / valida a tabela de símbolos.
    """

    def __init__(self):
        self.global_scope  = SymbolTable()
        self._scope        = self.global_scope
        self.errors: List[SemanticError] = []

    # ── entry point ─────────────────────────────────────────
    def analyze(self, program: Program) -> List[SemanticError]:
        for stmt in program.statements:
            self._visit_stmt(stmt)
        return self.errors

    # ── statements ──────────────────────────────────────────
    def _visit_stmt(self, node: ASTNode):
        try:
            if isinstance(node, VarDecl):
                self._visit_var_decl(node)
            elif isinstance(node, Assign):
                self._visit_assign(node)
            elif isinstance(node, If):
                self._visit_if(node)
            elif isinstance(node, While):
                self._visit_while(node)
            elif isinstance(node, Print):
                self._visit_print(node)
            elif isinstance(node, Read):
                self._visit_read(node)
            else:
                raise SemanticError(f"Nó desconhecido: {type(node).__name__}", 0)
        except SemanticError as e:
            self.errors.append(e)

    def _visit_var_decl(self, node: VarDecl):
        if node.init is not None:
            init_type = self._visit_expr(node.init)
            if init_type != node.var_type and init_type != 'unknown':
                raise SemanticError(
                    f"Tipo incompatível: variável '{node.name}' é '{node.var_type}', "
                    f"mas inicializada com '{init_type}'",
                    node.line
                )
        self._scope.declare(node.name, node.var_type, node.line)

    def _visit_assign(self, node: Assign):
        sym       = self._scope.require(node.name, node.line)
        val_type  = self._visit_expr(node.value)
        if val_type != sym.sym_type and val_type != 'unknown':
            raise SemanticError(
                f"Tipo incompatível: variável '{node.name}' é '{sym.sym_type}', "
                f"mas recebe valor do tipo '{val_type}'",
                node.line
            )

    def _visit_if(self, node: If):
        cond_type = self._visit_expr(node.condition)
        if cond_type != 'bool' and cond_type != 'unknown':
            raise SemanticError(
                f"Condição do 'if' deve ser bool, mas é '{cond_type}'",
                node.line
            )
        self._push_scope()
        for s in node.then_body:
            self._visit_stmt(s)
        self._pop_scope()
        if node.else_body:
            self._push_scope()
            for s in node.else_body:
                self._visit_stmt(s)
            self._pop_scope()

    def _visit_while(self, node: While):
        cond_type = self._visit_expr(node.condition)
        if cond_type != 'bool' and cond_type != 'unknown':
            raise SemanticError(
                f"Condição do 'while' deve ser bool, mas é '{cond_type}'",
                node.line
            )
        self._push_scope()
        for s in node.body:
            self._visit_stmt(s)
        self._pop_scope()

    def _visit_print(self, node: Print):
        self._visit_expr(node.expr)  # qualquer tipo aceito

    def _visit_read(self, node: Read):
        self._scope.require(node.name, node.line)

    # ── expressions (returns type string) ───────────────────
    def _visit_expr(self, node: ASTNode) -> str:
        try:
            if isinstance(node, IntLiteral):
                return 'int'
            if isinstance(node, BoolLiteral):
                return 'bool'
            if isinstance(node, StringLiteral):
                return 'string'
            if isinstance(node, VarRef):
                sym = self._scope.require(node.name, node.line)
                return sym.sym_type
            if isinstance(node, BinOp):
                lt = self._visit_expr(node.left)
                rt = self._visit_expr(node.right)
                return _check_binop(node.op, lt, rt, node.line)
            if isinstance(node, UnaryOp):
                t = self._visit_expr(node.expr)
                if node.op == '!':
                    if t != 'bool' and t != 'unknown':
                        raise SemanticError(f"'!' requer bool, mas recebeu '{t}'", node.line)
                    return 'bool'
                if node.op == '-':
                    if t != 'int' and t != 'unknown':
                        raise SemanticError(f"'-' unário requer int, mas recebeu '{t}'", node.line)
                    return 'int'
        except SemanticError as e:
            self.errors.append(e)
            return 'unknown'
        return 'unknown'

    # ── scope helpers ────────────────────────────────────────
    def _push_scope(self):
        self._scope = self._scope.child()

    def _pop_scope(self):
        self._scope = self._scope.parent

    # ── report ───────────────────────────────────────────────
    def symbol_table_report(self) -> str:
        lines = ["╔══════════════════════════════════╗",
                 "║      TABELA DE SÍMBOLOS           ║",
                 "╚══════════════════════════════════╝"]
        for sym in self.global_scope.all_symbols():
            used = "✓" if sym.used else "✗"
            lines.append(f"  {sym.name:<15} tipo={sym.sym_type:<8} usado={used}  (linha {sym.line})")
        return "\n".join(lines)
