"""
=============================================================
  SUITE DE TESTES
  Testa todas as fases do compilador com programas válidos
  e inválidos, verificando corretude léxica, sintática e
  semântica.
=============================================================
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from compiler import compile_source


# ── helpers ───────────────────────────────────────────────────
PASS = "\033[32m✓ PASSOU\033[0m"
FAIL = "\033[31m✗ FALHOU\033[0m"

def run_test(name: str, source: str, expect_success: bool):
    result = compile_source(source, verbose=False, optimize=True)
    ok = result["success"] == expect_success
    status = PASS if ok else FAIL
    print(f"  [{status}] {name}")
    if not ok:
        print(f"         erros: {result['errors']}")
    return ok


# ── test programs ─────────────────────────────────────────────
TESTS_VALID = [

    ("Declaração e print simples", """
int x = 42;
print(x);
"""),

    ("Operações aritméticas", """
int a = 10;
int b = 3;
int c = a * b + 2;
print(c);
"""),

    ("If-else básico", """
int n = 7;
bool ok = n > 5;
if (ok) {
    print(n);
} else {
    int zero = 0;
    print(zero);
}
"""),

    ("Loop while com acumulador", """
int i = 0;
int soma = 0;
while (i < 5) {
    soma = soma + i;
    i = i + 1;
}
print(soma);
"""),

    ("Operadores relacionais e lógicos", """
int x = 10;
int y = 20;
bool resultado = (x < y) && (y != 15);
print(resultado);
"""),

    ("Negação booleana", """
bool flag = true;
bool inv = !flag;
print(inv);
"""),

    ("Declaração sem inicialização", """
int x;
x = 99;
print(x);
"""),

    ("Variáveis booleanas", """
bool a = true;
bool b = false;
bool c = a || b;
print(c);
"""),

    ("Expressões aninhadas", """
int r = (3 + 4) * (10 - 2) / 2;
print(r);
"""),

    ("While com condicional interno", """
int n = 10;
int i = 1;
while (i <= n) {
    if (i == 5) {
        print(i);
    }
    i = i + 1;
}
"""),

    ("Comentários ignorados", """
// isto é um comentário
int x = 5; /* outro comentário */
print(x);
"""),
]

TESTS_INVALID = [

    ("Variável não declarada", """
print(x);
"""),

    ("Tipo incompatível: int ← bool", """
int x = true;
"""),

    ("Tipo incompatível na atribuição", """
int x = 5;
x = false;
"""),

    ("Operador aritmético com bool", """
bool a = true;
bool b = false;
int c = a + b;
"""),

    ("Condição if não-booleana", """
int n = 5;
if (n) {
    print(n);
}
"""),

    ("Variável redeclarada no mesmo escopo", """
int x = 1;
int x = 2;
"""),

    ("Token inválido (caractere @)", """
int x @= 5;
"""),

    ("Falta ponto-e-vírgula", """
int x = 5
print(x);
"""),
]


# ── main ──────────────────────────────────────────────────────
def main():
    print("\n" + "═"*54)
    print("  SUITE DE TESTES — MiniCompiler")
    print("═"*54)

    passed = 0; total = 0

    print("\n── Programas Válidos (devem compilar sem erros) ──")
    for name, src in TESTS_VALID:
        if run_test(name, src, expect_success=True):
            passed += 1
        total += 1

    print("\n── Programas Inválidos (devem reportar erros) ──")
    for name, src in TESTS_INVALID:
        if run_test(name, src, expect_success=False):
            passed += 1
        total += 1

    print(f"\n{'═'*54}")
    color = "\033[32m" if passed == total else "\033[31m"
    print(f"  {color}Resultado: {passed}/{total} testes passaram\033[0m")
    print("═"*54 + "\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
