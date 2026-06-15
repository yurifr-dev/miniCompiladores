# 🛠️ MiniCompiler

Compilador completo para a linguagem **Mini**, desenvolvido como projeto da disciplina de **Compiladores**.

O compilador percorre todas as fases clássicas de tradução, desde a leitura do código-fonte até a geração de Assembly x86-64.

---

## 📋 Fases Implementadas

| # | Fase | Módulo | Teoria Aplicada |
|---|------|--------|-----------------|
| 1 | Análise Léxica | `lexer.py` | Expressões Regulares + AFD |
| 2 | Análise Sintática | `parser.py` | Parser Descendente Recursivo + AST |
| 3 | Análise Semântica | `semantic.py` | Tabela de Símbolos + Type Checking |
| 4 | Geração de IR | `ir_generator.py` | Código de Três Endereços (TAC) |
| 5 | Geração de Código Final | `codegen.py` | Assembly x86-64 + Otimizações |

---

## 🗣️ A Linguagem Mini

### Tipos suportados
- `int` — inteiros de 64 bits
- `bool` — valores `true` e `false`

### Estruturas de controle
- `if / else`
- `while`

### Operadores
- Aritméticos: `+` `-` `*` `/`
- Relacionais: `==` `!=` `<` `>` `<=` `>=`
- Lógicos: `&&` `||` `!`

### Entrada e Saída
- `print(expr)` — imprime um valor
- `read(var)` — lê um valor do usuário

### Exemplo de programa
```mini
// Fibonacci iterativo
int n = 10;
int a = 0;
int b = 1;
int i = 0;

while (i < n) {
    int temp = a + b;
    a = b;
    b = temp;
    i = i + 1;
}

print(a);
```

---

## 📁 Estrutura do Projeto

```
miniCompiladores/
├── compiler.py         # Driver principal (CLI)
├── lexer.py            # Análise léxica — AFD
├── ast_nodes.py        # Nós da Árvore de Sintaxe Abstrata
├── parser.py           # Parser Descendente Recursivo
├── semantic.py         # Análise semântica + Tabela de Símbolos
├── ir_generator.py     # Geração de código intermediário (TAC)
├── codegen.py          # Otimizador + Gerador Assembly x86-64
├── test_compiler.py    # Suite de testes automatizados
├── fibonacci.mini      # Programa exemplo: Fibonacci
└── even_sum.mini       # Programa exemplo: Soma de pares
```

---

## 🚀 Como Usar

### Pré-requisitos
- Python 3.10+

### Compilar um programa
```bash
python compiler.py fibonacci.mini
```

### Salvar o Assembly gerado
```bash
python compiler.py fibonacci.mini -o saida.s
```

### Compilar sem otimizações
```bash
python compiler.py fibonacci.mini --no-opt
```

### Modo silencioso (sem saída verbosa)
```bash
python compiler.py fibonacci.mini -q
```

---

## ✅ Testes

```bash
python test_compiler.py
```

**Resultado: 19/19 testes passando (100%)**

```
── Programas Válidos (devem compilar sem erros) ──
  [✓ PASSOU] Declaração e print simples
  [✓ PASSOU] Operações aritméticas
  [✓ PASSOU] If-else básico
  [✓ PASSOU] Loop while com acumulador
  [✓ PASSOU] Operadores relacionais e lógicos
  [✓ PASSOU] Negação booleana
  [✓ PASSOU] Declaração sem inicialização
  [✓ PASSOU] Variáveis booleanas
  [✓ PASSOU] Expressões aninhadas
  [✓ PASSOU] While com condicional interno
  [✓ PASSOU] Comentários ignorados

── Programas Inválidos (devem reportar erros) ──
  [✓ PASSOU] Variável não declarada
  [✓ PASSOU] Tipo incompatível: int ← bool
  [✓ PASSOU] Tipo incompatível na atribuição
  [✓ PASSOU] Operador aritmético com bool
  [✓ PASSOU] Condição if não-booleana
  [✓ PASSOU] Variável redeclarada no mesmo escopo
  [✓ PASSOU] Token inválido (caractere @)
  [✓ PASSOU] Falta ponto-e-vírgula

Resultado: 19/19 testes passaram
```

---

## 🔍 Exemplo de Saída Completa

Ao compilar `fibonacci.mini`, o compilador exibe todas as fases:

**Fase 1 — Tokens gerados pelo Léxico:**
```
Token(INT, 'int', line=7, col=1)
Token(IDENTIFIER, 'n', line=7, col=5)
...
```

**Fase 2 — AST construída pelo Parser:**
```
Program:
  VarDecl(int n = 10)
  While((i < n)):
    VarDecl(int temp = (a + b))
    Assign(a = b)
    ...
```

**Fase 3 — Tabela de Símbolos:**
```
n    tipo=int   usado=✓
a    tipo=int   usado=✓
b    tipo=int   usado=✓
i    tipo=int   usado=✓
```

**Fase 4 — Código Intermediário (TAC):**
```
n = 10
a = 0
L0:
    t0 = i < n
    if_false t0 goto L1
    ...
    goto L0
L1:
    print a
```

**Fase 5 — Assembly x86-64:**
```asm
main:
    pushq   %rbp
    movq    %rsp, %rbp
    subq    $64, %rsp
    movq    $10, %rax
    movq    %rax, -32(%rbp)
    ...
```

---

## 📊 Critérios de Avaliação

| Critério | Peso | Status |
|----------|------|--------|
| Corretude Léxica/Sintática | 30% | ✅ 19/19 testes |
| Análise Semântica | 20% | ✅ Type checking + Escopo |
| Geração de Código | 30% | ✅ TAC + x86-64 + Otimizações |
| Documentação/Código | 20% | ✅ Relatório + README + Testes |

---

## 👨‍💻 Autor

**Yuri Figueiredo** — [@yurifr-dev](https://github.com/yurifr-dev)

Disciplina: Compiladores
