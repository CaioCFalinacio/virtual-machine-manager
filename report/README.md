# Relatório de Teste de Regressão — Task 3.1

## 1. Verificação de Pré-condições (Prompt 1)

**Data:** 2026-06-30
**SO:** Windows 11 / PowerShell

---

### 1.1 Compilação

| Item | Status | Detalhe |
|---|---|---|
| `gcc` disponível | RESOLVIDO | GCC 16.1.0 (MinGW-W64) instalado em `C:\mingw64\mingw64\bin` |
| `make` no PATH | N/A | Compilação realizada diretamente via `gcc` (equivalente ao Makefile) |

**Resultado: COMPILAÇÃO BEM-SUCEDIDA — sem erros e sem warnings.**

---

### 1.2 Arquivo `data/BACKING_STORE.bin`

| Item | Status | Detalhe |
|---|---|---|
| `data/BACKING_STORE.bin` | RESOLVIDO | Gerado via `python generate_data.py` (seed 42) |

---

### 1.3 Arquivo de endereços de entrada

| Arquivo | Status |
|---|---|
| `data/addresses_random.txt` | RESOLVIDO — gerado via `generate_data.py` (10.000 endereços) |
| `data/addresses_location.txt` | RESOLVIDO — gerado via `generate_data.py` |

Nota: O projeto não usa `addresses.txt` como nome de arquivo. Os arquivos de entrada são gerados pelo `generate_data.py` do próprio repositório. O arquivo `addresses_random.txt` foi utilizado como entrada para o teste de regressão.

---

### 1.4 Binário `vm`

| Item | Status |
|---|---|
| `vm.exe` (Windows) | RESOLVIDO — compilado com GCC sem erros |

---

## 2. Resumo — Pré-condições para o Prompt 2

| # | Pré-condição | Resolvida? |
|---|---|---|
| 1 | Compilador C (gcc) instalado | SIM — GCC 16.1.0 MinGW-W64 |
| 2 | `data/BACKING_STORE.bin` gerado | SIM — `generate_data.py` executado |
| 3 | Arquivo de endereços de entrada disponível | SIM — `addresses_random.txt` (10.000 endereços) |
| 4 | `correct.txt` (saída de referência) disponível | NÃO — ausente no repositório (diff não executado) |
| 5 | Binário `vm.exe` compilado com sucesso | SIM — sem erros ou warnings |

---

## 3. Execução e Comparação (Prompt 2) — Atualizado após instalação de ferramentas

**Data:** 2026-06-30
**SO:** Windows 11 / PowerShell
**Compilador:** GCC 16.1.0 (MinGW-W64 x86_64-ucrt-posix-seh)
**Python:** 3.14.6

---

### 3.1 Compilação

Comando executado:
```
gcc -Wall -Wextra -O2 -std=c11 -Iinclude src/main.c src/tlb.c src/page_table.c src/memory.c src/statistics.c -o vm.exe
```

| Item | Resultado |
|---|---|
| Erros de compilação | NENHUM |
| Warnings | NENHUM |
| Binário gerado | `vm.exe` na raiz do projeto |

---

### 3.2 Geração dos dados de entrada

Comando executado dentro de `data/`:
```
python generate_data.py
```

| Arquivo gerado | Status |
|---|---|
| `data/BACKING_STORE.bin` | GERADO (seed 42) |
| `data/addresses_random.txt` | GERADO |
| `data/addresses_location.txt` | GERADO |

Nota: O projeto não possui `addresses.txt` com esse nome exato. O arquivo utilizado foi `addresses_random.txt`, equivalente ao arquivo de endereços aleatórios da especificação.

---

### 3.3 Execução e captura de saída

Comando executado (equivalente PowerShell ao `./vm < addresses.txt > output.txt`):
```
Get-Content data\addresses_random.txt | .\vm.exe | Out-File -Encoding utf8 output.txt
```

| Item | Resultado |
|---|---|
| Execução | SUCESSO (exit code 0) |
| `output.txt` gerado | SIM — raiz do projeto |

---

### 3.4 Verificação de arquivo de referência

| Arquivo procurado | Encontrado? |
|---|---|
| `correct.txt` | NÃO |
| `expected_output.txt` | NÃO |

**Conclusão:** Nenhum arquivo de referência disponível no repositório. Diff não executado.

**Status:** SEM REFERÊNCIA DISPONÍVEL

---

### 3.5 Métricas operacionais (saída real do programa)

Entrada: `data/addresses_random.txt` (10.000 endereços, seed 42)

| Métrica | Valor |
|---|---|
| Total de endereços traduzidos | 10.000 |
| Page Faults | 4.958 |
| **Page Fault Rate** | **0.496 (49,6%)** |
| TLB Hits | 654 |
| **TLB Hit Rate** | **0.065 (6,5%)** |

---

### 3.6 Resumo final da Task 3.1

| Etapa | Status |
|---|---|
| Compilação (`gcc`) | OK — sem erros ou warnings |
| Geração de dados (`generate_data.py`) | OK |
| Execução com captura de saída | OK — `output.txt` gerado |
| Verificação de referência (`correct.txt`) | AUSENTE — sem referência disponível |
| Comparação (`diff`) | NÃO EXECUTADO — sem arquivo de referência |
| Documentação de discrepâncias | N/A — sem referência para comparar |
