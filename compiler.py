"""
=============================================================
  COMPILADOR PRINCIPAL (Driver)
  Orquestra todas as fases:
    1. Análise Léxica
    2. Análise Sintática (AST)
    3. Análise Semântica
    4. Geração de IR (TAC)
    5. Otimização + Geração de Código Final (x86-64)
=============================================================
"""

import sys
import os
import argparse

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from lexer         import Lexer,   LexerError
from parser        import Parser,  ParserError
from semantic      import SemanticAnalyzer
from ast_nodes     import ast_to_str
from ir_generator  import IRGenerator
from codegen       import Optimizer, X86Generator


# ── ANSI colors ───────────────────────────────────────────────
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner(title: str, color: str = CYAN):
    w = 52
    print(f"\n{color}{BOLD}{'═'*w}")
    print(f"  {title}")
    print(f"{'═'*w}{RESET}")


def compile_source(source: str, verbose: bool = True, optimize: bool = True) -> dict:
    result = {
        "tokens":    None,
        "ast":       None,
        "tac":       None,
        "asm":       None,
        "errors":    [],
        "success":   False,
    }

    # ──────────────────────────────────────────────────────────
    # FASE 1: Análise Léxica
    # ──────────────────────────────────────────────────────────
    if verbose: banner("FASE 1 — ANÁLISE LÉXICA", CYAN)
    try:
        lexer  = Lexer(source)
        tokens = lexer.tokenize()
        result["tokens"] = tokens
        if verbose:
            print(f"{GREEN}✓ {len(tokens)} tokens gerados{RESET}")
            for tok in tokens:
                print(f"  {tok}")
    except LexerError as e:
        result["errors"].append(str(e))
        if verbose: print(f"{RED}✗ {e}{RESET}")
        return result

    # ──────────────────────────────────────────────────────────
    # FASE 2: Análise Sintática
    # ──────────────────────────────────────────────────────────
    if verbose: banner("FASE 2 — ANÁLISE SINTÁTICA (AST)", CYAN)
    try:
        parser = Parser(tokens)
        ast    = parser.parse()
        result["ast"] = ast
        if verbose:
            print(f"{GREEN}✓ AST construída com sucesso{RESET}")
            print(ast_to_str(ast))
    except ParserError as e:
        result["errors"].append(str(e))
        if verbose: print(f"{RED}✗ {e}{RESET}")
        return result

    # ──────────────────────────────────────────────────────────
    # FASE 3: Análise Semântica
    # ──────────────────────────────────────────────────────────
    if verbose: banner("FASE 3 — ANÁLISE SEMÂNTICA", CYAN)
    analyzer = SemanticAnalyzer()
    sem_errors = analyzer.analyze(ast)
    if verbose:
        print(analyzer.symbol_table_report())
    if sem_errors:
        for e in sem_errors:
            result["errors"].append(str(e))
            if verbose: print(f"{RED}✗ {e}{RESET}")
        return result
    if verbose:
        print(f"{GREEN}✓ Sem erros semânticos{RESET}")

    # ──────────────────────────────────────────────────────────
    # FASE 4: Geração de IR (TAC)
    # ──────────────────────────────────────────────────────────
    if verbose: banner("FASE 4 — CÓDIGO INTERMEDIÁRIO (TAC)", CYAN)
    ir_gen = IRGenerator()
    tac    = ir_gen.generate(ast)
    result["tac"] = tac
    if verbose:
        print(ir_gen.dump())

    # ──────────────────────────────────────────────────────────
    # FASE 5: Otimização + Geração de Código Final
    # ──────────────────────────────────────────────────────────
    if verbose: banner("FASE 5 — OTIMIZAÇÃO + CÓDIGO FINAL (x86-64)", CYAN)
    if optimize:
        opt = Optimizer()
        tac = opt.optimize(tac)
        if verbose:
            print(f"{YELLOW}Após otimização: {len(tac)} instruções{RESET}")

    x86 = X86Generator()
    asm = x86.generate(tac)
    result["asm"]     = asm
    result["success"] = True
    if verbose:
        print(asm)

    return result


# ── CLI ───────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="MiniCompiler — Compilador educacional para a linguagem Mini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python compiler.py programa.mini
  python compiler.py programa.mini -o saida.s
  python compiler.py programa.mini --no-opt --verbose
        """
    )
    ap.add_argument("source",          help="Arquivo fonte (.mini)")
    ap.add_argument("-o", "--output",  help="Arquivo de saída Assembly (.s)", default=None)
    ap.add_argument("--no-opt",        help="Desabilitar otimizações",  action="store_true")
    ap.add_argument("-q", "--quiet",   help="Sem saída verbosa",         action="store_true")
    args = ap.parse_args()

    try:
        with open(args.source, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"{RED}Arquivo não encontrado: {args.source}{RESET}")
        sys.exit(1)

    print(f"\n{BOLD}MiniCompiler v1.0{RESET}")
    print(f"Compilando: {args.source}")

    result = compile_source(
        source,
        verbose  = not args.quiet,
        optimize = not args.no_opt,
    )

    if result["errors"]:
        print(f"\n{RED}{BOLD}Compilação falhou com {len(result['errors'])} erro(s):{RESET}")
        for e in result["errors"]:
            print(f"  {RED}{e}{RESET}")
        sys.exit(1)

    if args.output and result["asm"]:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result["asm"])
        print(f"\n{GREEN}✓ Assembly salvo em: {args.output}{RESET}")

    print(f"\n{GREEN}{BOLD}✓ Compilação concluída com sucesso!{RESET}")


if __name__ == "__main__":
    main()
