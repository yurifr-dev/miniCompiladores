"""
=============================================================
  ANALISADOR SINTÁTICO (Parser)
  Método: Descendente Recursivo (Recursive Descent)
  Produz a Árvore de Sintaxe Abstrata (AST).

  Gramática (simplificada em BNF):
    program       → stmt*
    stmt          → var_decl | assign | if_stmt
                   | while_stmt | print_stmt | read_stmt
    var_decl      → type IDENT ['=' expr] ';'
    assign        → IDENT '=' expr ';'
    if_stmt       → 'if' '(' expr ')' block ['else' block]
    while_stmt    → 'while' '(' expr ')' block
    print_stmt    → 'print' '(' expr ')' ';'
    read_stmt     → 'read'  '(' IDENT ')' ';'
    block         → '{' stmt* '}'
    type          → 'int' | 'bool'

    expr          → or_expr
    or_expr       → and_expr ('||' and_expr)*
    and_expr      → eq_expr  ('&&' eq_expr)*
    eq_expr       → rel_expr (('=='|'!=') rel_expr)*
    rel_expr      → add_expr (('<'|'>'|'<='|'>=') add_expr)*
    add_expr      → mul_expr (('+'|'-') mul_expr)*
    mul_expr      → unary   (('*'|'/') unary)*
    unary         → '!' unary | '-' unary | primary
    primary       → INTEGER | BOOLEAN | STRING | IDENT
                   | '(' expr ')'
=============================================================
"""

from typing import List, Optional
from lexer import Token, TokenType
from ast_nodes import *


class ParserError(Exception):
    def __init__(self, msg: str, line: int, col: int = 0):
        super().__init__(f"[Sintático] Erro na linha {line}: {msg}")
        self.line = line


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos    = 0

    # ── helpers ──────────────────────────────────────────────
    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def check(self, *types: TokenType) -> bool:
        return self.current.type in types

    def match(self, *types: TokenType) -> Optional[Token]:
        if self.check(*types):
            tok = self.current
            self.pos += 1
            return tok
        return None

    def expect(self, ttype: TokenType, msg: str = "") -> Token:
        tok = self.match(ttype)
        if tok is None:
            got = self.current
            label = msg or ttype.name
            raise ParserError(
                f"Esperado '{label}', mas encontrado '{got.lexeme}'",
                got.line, got.column
            )
        return tok

    # ── entry point ──────────────────────────────────────────
    def parse(self) -> Program:
        stmts: List[ASTNode] = []
        while not self.check(TokenType.EOF):
            stmts.append(self._stmt())
        return Program(stmts)

    # ── statements ───────────────────────────────────────────
    def _stmt(self) -> ASTNode:
        tok = self.current
        if self.check(TokenType.INT, TokenType.BOOL):
            return self._var_decl()
        if self.check(TokenType.IF):
            return self._if_stmt()
        if self.check(TokenType.WHILE):
            return self._while_stmt()
        if self.check(TokenType.PRINT):
            return self._print_stmt()
        if self.check(TokenType.READ):
            return self._read_stmt()
        # Assignment: IDENT '=' ...
        if self.check(TokenType.IDENTIFIER) and self.peek().type == TokenType.ASSIGN:
            return self._assign_stmt()
        raise ParserError(
            f"Statement inválido (token: '{tok.lexeme}')",
            tok.line, tok.column
        )

    def _var_decl(self) -> VarDecl:
        tok      = self.current
        var_type = self.current.lexeme
        self.pos += 1
        name     = self.expect(TokenType.IDENTIFIER, "nome de variável").lexeme
        init     = None
        if self.match(TokenType.ASSIGN):
            init = self._expr()
        self.expect(TokenType.SEMICOLON, ";")
        return VarDecl(var_type, name, init, tok.line)

    def _assign_stmt(self) -> Assign:
        tok  = self.current
        name = self.expect(TokenType.IDENTIFIER).lexeme
        self.expect(TokenType.ASSIGN, "=")
        value = self._expr()
        self.expect(TokenType.SEMICOLON, ";")
        return Assign(name, value, tok.line)

    def _if_stmt(self) -> If:
        tok = self.expect(TokenType.IF)
        self.expect(TokenType.LPAREN, "(")
        cond = self._expr()
        self.expect(TokenType.RPAREN, ")")
        then_body = self._block()
        else_body: List[ASTNode] = []
        if self.match(TokenType.ELSE):
            else_body = self._block()
        return If(cond, then_body, else_body, tok.line)

    def _while_stmt(self) -> While:
        tok = self.expect(TokenType.WHILE)
        self.expect(TokenType.LPAREN, "(")
        cond = self._expr()
        self.expect(TokenType.RPAREN, ")")
        body = self._block()
        return While(cond, body, tok.line)

    def _print_stmt(self) -> Print:
        tok = self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN, "(")
        expr = self._expr()
        self.expect(TokenType.RPAREN, ")")
        self.expect(TokenType.SEMICOLON, ";")
        return Print(expr, tok.line)

    def _read_stmt(self) -> Read:
        tok = self.expect(TokenType.READ)
        self.expect(TokenType.LPAREN, "(")
        name = self.expect(TokenType.IDENTIFIER, "nome de variável").lexeme
        self.expect(TokenType.RPAREN, ")")
        self.expect(TokenType.SEMICOLON, ";")
        return Read(name, tok.line)

    def _block(self) -> List[ASTNode]:
        self.expect(TokenType.LBRACE, "{")
        stmts: List[ASTNode] = []
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            stmts.append(self._stmt())
        self.expect(TokenType.RBRACE, "}")
        return stmts

    # ── expressions (operator precedence via recursion) ──────
    def _expr(self) -> ASTNode:
        return self._or_expr()

    def _or_expr(self) -> ASTNode:
        node = self._and_expr()
        while self.check(TokenType.OR):
            op  = self.current.lexeme; ln = self.current.line; self.pos += 1
            rhs = self._and_expr()
            node = BinOp(op, node, rhs, ln)
        return node

    def _and_expr(self) -> ASTNode:
        node = self._eq_expr()
        while self.check(TokenType.AND):
            op  = self.current.lexeme; ln = self.current.line; self.pos += 1
            rhs = self._eq_expr()
            node = BinOp(op, node, rhs, ln)
        return node

    def _eq_expr(self) -> ASTNode:
        node = self._rel_expr()
        while self.check(TokenType.EQ, TokenType.NEQ):
            op  = self.current.lexeme; ln = self.current.line; self.pos += 1
            rhs = self._rel_expr()
            node = BinOp(op, node, rhs, ln)
        return node

    def _rel_expr(self) -> ASTNode:
        node = self._add_expr()
        while self.check(TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE):
            op  = self.current.lexeme; ln = self.current.line; self.pos += 1
            rhs = self._add_expr()
            node = BinOp(op, node, rhs, ln)
        return node

    def _add_expr(self) -> ASTNode:
        node = self._mul_expr()
        while self.check(TokenType.PLUS, TokenType.MINUS):
            op  = self.current.lexeme; ln = self.current.line; self.pos += 1
            rhs = self._mul_expr()
            node = BinOp(op, node, rhs, ln)
        return node

    def _mul_expr(self) -> ASTNode:
        node = self._unary()
        while self.check(TokenType.STAR, TokenType.SLASH):
            op  = self.current.lexeme; ln = self.current.line; self.pos += 1
            rhs = self._unary()
            node = BinOp(op, node, rhs, ln)
        return node

    def _unary(self) -> ASTNode:
        if self.check(TokenType.NOT):
            op = self.current.lexeme; ln = self.current.line; self.pos += 1
            return UnaryOp(op, self._unary(), ln)
        if self.check(TokenType.MINUS):
            op = self.current.lexeme; ln = self.current.line; self.pos += 1
            return UnaryOp(op, self._unary(), ln)
        return self._primary()

    def _primary(self) -> ASTNode:
        tok = self.current
        if self.match(TokenType.INTEGER):
            return IntLiteral(tok.value, tok.line)
        if self.match(TokenType.TRUE, TokenType.FALSE):
            return BoolLiteral(tok.value if tok.type == TokenType.TRUE else False, tok.line)
        if self.match(TokenType.STRING):
            return StringLiteral(tok.value, tok.line)
        if self.match(TokenType.IDENTIFIER):
            return VarRef(tok.lexeme, tok.line)
        if self.match(TokenType.LPAREN):
            expr = self._expr()
            self.expect(TokenType.RPAREN, ")")
            return expr
        raise ParserError(
            f"Expressão inválida: '{tok.lexeme}'",
            tok.line, tok.column
        )
