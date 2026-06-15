"""
=============================================================
  GERAÇÃO DE CÓDIGO FINAL
  Alvo: Assembly x86-64 (sintaxe AT&T / GNU as)
  + Otimizações:
      1. Eliminação de código morto (dead code elimination)
      2. Propagação de constantes (constant folding)
=============================================================
"""

from typing import List, Dict, Set, Optional
from ir_generator import (
    TACInstr, TACAssign, TACBinOp, TACUnary,
    TACLabel, TACGoto, TACIfFalse, TACPrint, TACRead, TACCopy
)


# ── Optimizer ─────────────────────────────────────────────────
class Optimizer:
    """
    Passe de otimização sobre o TAC.
    1. Constant Folding   – avalia operações com literais em compile-time.
    2. Dead Code Elim     – remove atribuições a temporários nunca usados.
    """

    def optimize(self, code: List[TACInstr]) -> List[TACInstr]:
        code = self._constant_fold(code)
        code = self._dead_code_elim(code)
        return code

    # ── Pass 1: constant folding ──────────────────────────────
    def _constant_fold(self, code: List[TACInstr]) -> List[TACInstr]:
        result = []
        for instr in code:
            if isinstance(instr, TACBinOp):
                folded = self._try_fold(instr)
                result.append(folded)
            else:
                result.append(instr)
        return result

    def _try_fold(self, instr: TACBinOp) -> TACInstr:
        l, r = instr.left, instr.right
        op    = instr.op

        def is_int(x):
            try: int(x); return True
            except: return False

        def is_bool(x):
            return x in ('true', 'false')

        if is_int(l) and is_int(r):
            lv, rv = int(l), int(r)
            try:
                if   op == '+':  v = lv + rv;  return TACAssign(instr.dest, str(v))
                elif op == '-':  v = lv - rv;  return TACAssign(instr.dest, str(v))
                elif op == '*':  v = lv * rv;  return TACAssign(instr.dest, str(v))
                elif op == '/' and rv != 0:
                                 v = lv // rv; return TACAssign(instr.dest, str(v))
                elif op == '<':  return TACAssign(instr.dest, 'true' if lv <  rv else 'false')
                elif op == '>':  return TACAssign(instr.dest, 'true' if lv >  rv else 'false')
                elif op == '<=': return TACAssign(instr.dest, 'true' if lv <= rv else 'false')
                elif op == '>=': return TACAssign(instr.dest, 'true' if lv >= rv else 'false')
                elif op == '==': return TACAssign(instr.dest, 'true' if lv == rv else 'false')
                elif op == '!=': return TACAssign(instr.dest, 'true' if lv != rv else 'false')
            except: pass

        if is_bool(l) and is_bool(r):
            lv = l == 'true'; rv = r == 'true'
            if   op == '&&': return TACAssign(instr.dest, 'true' if lv and rv else 'false')
            elif op == '||': return TACAssign(instr.dest, 'true' if lv or  rv else 'false')
            elif op == '==': return TACAssign(instr.dest, 'true' if lv == rv else 'false')
            elif op == '!=': return TACAssign(instr.dest, 'true' if lv != rv else 'false')

        return instr

    # ── Pass 2: dead code elimination ────────────────────────
    def _dead_code_elim(self, code: List[TACInstr]) -> List[TACInstr]:
        # Collect all operands that are read
        used: Set[str] = set()
        for instr in code:
            if isinstance(instr, TACBinOp):
                used |= {instr.left, instr.right}
            elif isinstance(instr, TACUnary):
                used.add(instr.src)
            elif isinstance(instr, TACAssign):
                used.add(instr.src)
            elif isinstance(instr, TACIfFalse):
                used.add(instr.cond)
            elif isinstance(instr, TACPrint):
                used.add(instr.src)

        result = []
        for instr in code:
            # Remove assignments to temporaries that are never read
            if isinstance(instr, (TACAssign, TACBinOp, TACUnary)):
                dest = instr.dest
                if dest.startswith('t') and dest not in used:
                    continue  # dead code – skip
            result.append(instr)
        return result


# ── x86-64 Code Generator ─────────────────────────────────────
class X86Generator:
    """
    Gera Assembly x86-64 (AT&T syntax) a partir do TAC.
    Variáveis são mantidas em memória (stack ou .bss).
    Temporários são mapeados para registradores virtuais
    (simplificado: %rax, %rbx, %rcx via stack slots).
    """

    def __init__(self):
        self._vars:    Dict[str, int] = {}   # var → stack offset
        self._stack    = 0
        self._strings: List[str]      = []   # string literals
        self._str_cnt  = 0

    def generate(self, code: List[TACInstr]) -> str:
        # --- First pass: collect variables and temporaries ---
        self._collect_vars(code)

        asm: List[str] = []

        # ── Header ──────────────────────────────────────────
        asm += [
            "# ==========================================",
            "# Código gerado pelo MiniCompiler",
            "# Alvo: x86-64 Linux (AT&T syntax)",
            "# ==========================================",
            "",
            "    .section .data",
            '    fmt_int:    .string "%d\\n"',
            '    fmt_bool_t: .string "true\\n"',
            '    fmt_bool_f: .string "false\\n"',
            '    fmt_str:    .string "%s\\n"',
            '    fmt_read:   .string "%d"',
        ]

        # ── .text ────────────────────────────────────────────
        asm += [
            "",
            "    .section .text",
            "    .globl main",
            "main:",
            "    pushq   %rbp",
            "    movq    %rsp, %rbp",
            f"   subq    ${max(self._stack, 16)}, %rsp",
            "",
        ]

        # ── Body ────────────────────────────────────────────
        for instr in code:
            asm.append(f"    # {instr}")
            asm += self._emit_instr(instr)
            asm.append("")

        # ── Epilogue ─────────────────────────────────────────
        asm += [
            "    movq    $0, %rax",
            "    movq    %rbp, %rsp",
            "    popq    %rbp",
            "    ret",
        ]

        return "\n".join(asm)

    # ── variable layout ──────────────────────────────────────
    def _collect_vars(self, code: List[TACInstr]):
        names: Set[str] = set()
        for instr in code:
            if isinstance(instr, TACAssign):
                names.add(instr.dest)
            elif isinstance(instr, TACBinOp):
                names.add(instr.dest)
            elif isinstance(instr, TACUnary):
                names.add(instr.dest)
            elif isinstance(instr, TACRead):
                names.add(instr.dest)
        for n in sorted(names):
            self._stack += 8
            self._vars[n] = self._stack

    def _addr(self, name: str) -> str:
        """Returns memory operand for variable."""
        if name not in self._vars:
            self._stack += 8
            self._vars[name] = self._stack
        return f"-{self._vars[name]}(%rbp)"

    def _load(self, operand: str, reg: str) -> List[str]:
        """Load operand into register."""
        if operand == 'true':
            return [f"    movq    $1, {reg}"]
        if operand == 'false':
            return [f"    movq    $0, {reg}"]
        try:
            int(operand)
            return [f"    movq    ${operand}, {reg}"]
        except ValueError:
            pass
        if operand.startswith('"'):
            lbl = f".Lstr{self._str_cnt}"
            self._str_cnt += 1
            self._strings.append(f'    {lbl}: .string {operand}')
            return [f"    leaq    {lbl}(%rip), {reg}"]
        return [f"    movq    {self._addr(operand)}, {reg}"]

    def _store(self, reg: str, dest: str) -> List[str]:
        return [f"    movq    {reg}, {self._addr(dest)}"]

    # ── instruction emission ─────────────────────────────────
    def _emit_instr(self, instr: TACInstr) -> List[str]:
        lines: List[str] = []

        if isinstance(instr, TACAssign):
            lines += self._load(instr.src, "%rax")
            lines += self._store("%rax", instr.dest)

        elif isinstance(instr, TACBinOp):
            lines += self._load(instr.left, "%rax")
            lines += self._load(instr.right, "%rbx")

            if   instr.op == '+':
                lines.append("    addq    %rbx, %rax")
            elif instr.op == '-':
                lines.append("    subq    %rbx, %rax")
            elif instr.op == '*':
                lines.append("    imulq   %rbx, %rax")
            elif instr.op == '/':
                lines += ["    cqto", "    idivq   %rbx"]
            elif instr.op in ('<', '>', '<=', '>=', '==', '!='):
                map_ = {'<':'l','>'  :'g','<=':'le','>=':'ge','==':'e','!=':'ne'}
                cc   = map_[instr.op]
                lines += [
                    "    cmpq    %rbx, %rax",
                    f"   set{cc}    %al",
                    "    movzbq  %al, %rax",
                ]
            elif instr.op == '&&':
                lines += ["    andq    %rbx, %rax", "    andq    $1, %rax"]
            elif instr.op == '||':
                lines += ["    orq     %rbx, %rax", "    andq    $1, %rax"]
            elif instr.op == '==':
                lines += ["    cmpq    %rbx, %rax", "    sete    %al",
                          "    movzbq  %al, %rax"]

            lines += self._store("%rax", instr.dest)

        elif isinstance(instr, TACUnary):
            lines += self._load(instr.src, "%rax")
            if instr.op == '-':
                lines.append("    negq    %rax")
            elif instr.op == '!':
                lines += ["    xorq    $1, %rax", "    andq    $1, %rax"]
            lines += self._store("%rax", instr.dest)

        elif isinstance(instr, TACLabel):
            lines.append(f"{instr.name}:")

        elif isinstance(instr, TACGoto):
            lines.append(f"    jmp     {instr.label}")

        elif isinstance(instr, TACIfFalse):
            lines += self._load(instr.cond, "%rax")
            lines += ["    testq   %rax, %rax",
                      f"   je      {instr.label}"]

        elif isinstance(instr, TACPrint):
            # Simplified: treat everything as integer
            lines += self._load(instr.src, "%rsi")
            lines += [
                "    leaq    fmt_int(%rip), %rdi",
                "    xorq    %rax, %rax",
                "    call    printf@PLT",
            ]

        elif isinstance(instr, TACRead):
            lines += [
                "    leaq    fmt_read(%rip), %rdi",
                f"   leaq    {self._addr(instr.dest)}, %rsi",
                "    xorq    %rax, %rax",
                "    call    scanf@PLT",
            ]

        return lines
