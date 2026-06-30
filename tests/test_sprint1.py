"""
Testes de integracao para as tasks da Sprint 1.

Tasks cobertas:
  T1.1 - Extracao correta de pagina e offset (Bitmask 16 bits)
  T1.2 - Leitura do byte da memoria fisica (casting signed char)
  T1.3 - Consulta e atualizacao da tabela de paginas
  T1.4 - Leitura de paginas do BACKING_STORE.bin e gerenciamento de frames
  T1.5 - Estatisticas finais

Como rodar:
    python tests/test_sprint1.py
"""

import subprocess
import os
import sys
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def find_compiler():
    """Localiza o compilador C disponível no sistema."""
    for candidate in ("gcc", "cc", "cl"):
        if shutil.which(candidate):
            return candidate

    for path in (
        r"C:\msys64\ucrt64\bin\gcc.exe",
        r"C:\msys64\mingw64\bin\gcc.exe",
        r"C:\MinGW\bin\gcc.exe",
    ):
        if os.path.isfile(path):
            return path
    return None


def build_project():
    """Compila o projeto chamando gcc diretamente, sem precisar do make."""
    compiler = find_compiler()
    if compiler is None:
        print("ERRO: nenhum compilador C encontrado no sistema.")
        sys.exit(1)

    src_dir = os.path.join(PROJECT_ROOT, "src")
    inc_dir = os.path.join(PROJECT_ROOT, "include")
    out_exe = os.path.join(PROJECT_ROOT, "vm.exe")

    sources = [
        os.path.join(src_dir, f)
        for f in os.listdir(src_dir)
        if f.endswith(".c")
    ]

    cmd = [compiler, "-Wall", "-Wextra", "-O2", "-std=c11",
           f"-I{inc_dir}", *sources, "-o", out_exe]

    build = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if build.returncode != 0:
        print("ERRO: falha ao compilar o projeto.")
        print(build.stderr)
        sys.exit(1)

    return out_exe


def run_simulation(input_file):
    exe_path = build_project()

    with open(input_file, "r") as f_in:
        result = subprocess.run(
            [exe_path],
            stdin=f_in,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT,
        )
    return result.stdout.strip().split("\n")


def generate_backing_store(data_dir):
    """Gera o BACKING_STORE.bin deterministicamente (byte N = N % 256)."""
    os.makedirs(data_dir, exist_ok=True)
    backing_path = os.path.join(data_dir, "BACKING_STORE.bin")
    with open(backing_path, "wb") as f:
        for i in range(65536):
            f.write(bytes([i % 256]))


def write_input_file(path, addresses):
    with open(path, "w", encoding="utf-8") as f:
        for addr in addresses:
            f.write(f"{addr}\n")


# -----------------------------------------------------------------------------
# --- TESTE 1 --- Traducao de enderecos basica e estatisticas (T1.1 a T1.5)
#
# Objetivo
# ---------
# Verificar a correta traducao de enderecos virtuais de 32 bits mascarados para 
# 16 bits, o correto tratamento de page faults carregando dados do BACKING_STORE, 
# a leitura adequada de signed chars e o calculo correto das metricas finais.
#
# Sequencia:
#   1. Endereco 305414676 (0x12344214): Mascara isola 0x4214 (16916). Pagina 66, offset 20. 
#      Causa TLB Miss e Page Fault, carregando para o Frame 0. Byte retornado = 20.
#   2. Endereco 17096: Pagina 66, offset 200. Gera um TLB Hit (pois a pagina 66 foi
#      inserida no TLB no acesso anterior). Retorna o byte correspondente como signed char (-56).
#   3. Endereco 32768: Pagina 128, offset 0. Causa TLB Miss e Page Fault, carregando para o Frame 1. 
#      Byte retornado = 0.
#   4. Endereco 32768: Pagina 128, offset 0. Gera um TLB Hit. Byte retornado = 0.
#
# Estatisticas esperadas:
#   Total = 4, Page Faults = 2, TLB Hits = 2
#   Page Fault Rate = 0.500, TLB Hit Rate = 0.500
# -----------------------------------------------------------------------------
def test_sprint1():
    print("Iniciando testes da Sprint 1...")

    data_dir = os.path.join(PROJECT_ROOT, "data")
    generate_backing_store(data_dir)

    input_path = os.path.join(PROJECT_ROOT, "test_input.txt")
    addresses = [305414676, 17096, 32768, 32768]
    write_input_file(input_path, addresses)

    expected_outputs = [
        "Logical address: 16916 Physical address: 20 Value: 20",
        "Logical address: 17096 Physical address: 200 Value: -56",
        "Logical address: 32768 Physical address: 256 Value: 0",
        "Logical address: 32768 Physical address: 256 Value: 0",
        "Number of Translated Addresses = 4",
        "Page Faults = 2",
        "Page Fault Rate = 0.500",
        "TLB Hits = 2",
        "TLB Hit Rate = 0.500",
    ]

    try:
        actual_outputs = run_simulation(input_path)
    except subprocess.CalledProcessError as e:
        print("Erro ao compilar ou executar o programa.")
        print(e.stderr)
        sys.exit(1)

    passed = True
    for i, expected in enumerate(expected_outputs):
        actual = actual_outputs[i].strip() if i < len(actual_outputs) else ""
        if actual == expected:
            print(f"[PASS] Linha {i+1}: {expected}")
        else:
            print(f"[FAIL] Linha {i+1}")
            print(f"       Esperado: '{expected}'")
            print(f"       Recebido: '{actual}'")
            passed = False

    print("\n--- Resultado Final ---")
    if passed:
        print("Todos os testes da Sprint 1 PASSARAM!")
    else:
        print("Alguns testes FALHARAM. Verifique os itens acima.")
    
    return passed


if __name__ == "__main__":
    success = test_sprint1()
    sys.exit(0 if success else 1)
