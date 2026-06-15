"""
=============================================================
  ANALISADOR LÉXICO (Scanner)
  Teoria aplicada: Expressões Regulares + AFD
  Converte fluxo de caracteres em sequência de tokens.
=============================================================
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


# ── Token Types ──────────────────────────────────────────────
class TokenType(Enum):
    # Literals
    INTEGER    = auto()
    BOOLEAN    = auto()
    STRING     = auto()
    IDENTIFIER = auto()

    # Keywords
    INT    = auto()
    BOOL   = auto()
    IF     = auto()
    ELSE   = auto()
    WHILE  = auto()
    PRINT  = auto()
    READ   = auto()
    TRUE   = auto()
    FALSE  = auto()

    # Arithmetic operators
    PLUS   = auto()
    MINUS  = auto()
    STAR   = auto()
    SLASH  = auto()

    # Relational / logical operators
    EQ     = auto()   # ==
    NEQ    = auto()   # !=
    LT     = auto()   # <
    GT     = auto()   # >
    LE     = auto()   # <=
    GE     = auto()   # >=
    AND    = auto()   # &&
    OR     = auto()   # ||
    NOT    = auto()   # !

    # Assignment
    ASSIGN = auto()   # =

    # Delimiters
    LPAREN    = auto()
    RPAREN    = auto()
    LBRACE    = auto()
    RBRACE    = auto()
    SEMICOLON = auto()
    COMMA     = auto()

    # Special
    EOF     = auto()
    NEWLINE = auto()


# ── Keyword mapping ───────────────────────────────────────────
KEYWORDS: dict[str, TokenType] = {
    "int":   TokenType.INT,
    "bool":  TokenType.BOOL,
    "if":    TokenType.IF,
    "else":  TokenType.ELSE,
    "while": TokenType.WHILE,
    "print": TokenType.PRINT,
    "read":  TokenType.READ,
    "true":  TokenType.TRUE,
    "false": TokenType.FALSE,
}


# ── Token dataclass ───────────────────────────────────────────
@dataclass
class Token:
    type:    TokenType
    lexeme:  str
    value:   object          # processed Python value
    line:    int
    column:  int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.lexeme!r}, line={self.line}, col={self.column})"


# ── Lexer ─────────────────────────────────────────────────────
class LexerError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"[Léxico] Erro na linha {line}, coluna {col}: {msg}")
        self.line = line
        self.col  = col


class Lexer:
    """
    AFD implementado como máquina de estados explícita.
    Reconhece a linguagem-alvo através de transições de estado.
    """

    # Padrões ordenados por prioridade (mais específicos primeiro)
    TOKEN_PATTERNS = [
        (r'\d+',                         TokenType.INTEGER),
        (r'"[^"]*"',                      TokenType.STRING),
        (r'==',                           TokenType.EQ),
        (r'!=',                           TokenType.NEQ),
        (r'<=',                           TokenType.LE),
        (r'>=',                           TokenType.GE),
        (r'&&',                           TokenType.AND),
        (r'\|\|',                         TokenType.OR),
        (r'<',                            TokenType.LT),
        (r'>',                            TokenType.GT),
        (r'!',                            TokenType.NOT),
        (r'\+',                           TokenType.PLUS),
        (r'-',                            TokenType.MINUS),
        (r'\*',                           TokenType.STAR),
        (r'/',                            TokenType.SLASH),
        (r'=',                            TokenType.ASSIGN),
        (r'\(',                           TokenType.LPAREN),
        (r'\)',                           TokenType.RPAREN),
        (r'\{',                           TokenType.LBRACE),
        (r'\}',                           TokenType.RBRACE),
        (r';',                            TokenType.SEMICOLON),
        (r',',                            TokenType.COMMA),
        (r'[a-zA-Z_][a-zA-Z0-9_]*',      TokenType.IDENTIFIER),
    ]

    def __init__(self, source: str):
        self.source  = source
        self.pos     = 0
        self.line    = 1
        self.column  = 1
        # Compila todos os padrões em um único regex (master pattern)
        self._master = re.compile(
            '|'.join(f'(?P<PAT{i}>{p})' for i, (p, _) in enumerate(self.TOKEN_PATTERNS))
        )

    # ── public API ───────────────────────────────────────────
    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while self.pos < len(self.source):
            self._skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break
            tok = self._next_token()
            tokens.append(tok)
        tokens.append(Token(TokenType.EOF, '', None, self.line, self.column))
        return tokens

    # ── internals ────────────────────────────────────────────
    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            # Blank characters
            if ch in ' \t\r':
                self._advance()
            elif ch == '\n':
                self.line   += 1
                self.column  = 1
                self.pos    += 1
            # Single-line comments  //
            elif self.source[self.pos:self.pos+2] == '//':
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self._advance()
            # Multi-line comments  /* ... */
            elif self.source[self.pos:self.pos+2] == '/*':
                self._advance(); self._advance()   # skip /*
                while self.pos < len(self.source):
                    if self.source[self.pos:self.pos+2] == '*/':
                        self._advance(); self._advance()
                        break
                    if self.source[self.pos] == '\n':
                        self.line += 1; self.column = 1; self.pos += 1
                    else:
                        self._advance()
            else:
                break

    def _next_token(self) -> Token:
        line, col = self.line, self.column
        m = self._master.match(self.source, self.pos)
        if not m:
            bad = self.source[self.pos]
            raise LexerError(f"Caractere inesperado: {bad!r}", line, col)

        lexeme = m.group()
        # Identify which pattern matched
        for i, (_, ttype) in enumerate(self.TOKEN_PATTERNS):
            if m.group(f'PAT{i}') is not None:
                tok_type = ttype
                break

        # Advance position/column
        for ch in lexeme:
            if ch == '\n':
                self.line += 1; self.column = 1
            else:
                self.column += 1
        self.pos += len(lexeme)

        # Resolve keywords vs identifiers
        if tok_type == TokenType.IDENTIFIER and lexeme in KEYWORDS:
            tok_type = KEYWORDS[lexeme]

        # Compute Python value
        value = self._compute_value(tok_type, lexeme)
        return Token(tok_type, lexeme, value, line, col)

    def _compute_value(self, ttype: TokenType, lexeme: str) -> object:
        if ttype == TokenType.INTEGER:
            return int(lexeme)
        if ttype == TokenType.BOOLEAN or ttype in (TokenType.TRUE, TokenType.FALSE):
            return lexeme == 'true'
        if ttype == TokenType.STRING:
            return lexeme[1:-1]   # strip quotes
        return lexeme

    def _advance(self):
        self.pos    += 1
        self.column += 1
