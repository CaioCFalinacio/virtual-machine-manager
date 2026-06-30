"""
Testes de integração para as tasks da Sprint 2.

Cada teste possui um simulador Python embutido que replica exatamente a
lógica do código C e serve de oráculo para os valores esperados.

Tasks cobertas:
  T2.1 – page_table_set_reference + page_table_update_aging (Aging/LRU)
  T2.2 – select_victim_page + substituição em handle_page_fault
  T2.3 – tlb_lookup                          (já implementado)
  T2.4 – tlb_insert com política FIFO        (já implementado)
  T2.5 – tlb_remove ao desalocar uma página  (já implementado)

Como rodar:
    python tests/test_sprint2.py
"""

import subprocess
import os
import sys
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGE_SIZE  = 256
NUM_FRAMES = 128
TLB_SIZE = 16

def find_compiler():
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
    compiler = find_compiler()
    if compiler is None:
        print("ERRO: nenhum compilador C encontrado no sistema.")
        sys.exit(1)

    src_dir = os.path.join(PROJECT_ROOT, "src")
    inc_dir = os.path.join(PROJECT_ROOT, "include")
    out_exe = os.path.join(PROJECT_ROOT, "vm.exe")

    sources = [os.path.join(src_dir, f)
               for f in os.listdir(src_dir) if f.endswith(".c")]

    build = subprocess.run(
        [compiler, "-Wall", "-Wextra", "-O2", "-std=c11",
         f"-I{inc_dir}", *sources, "-o", out_exe],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if build.returncode != 0:
        print("ERRO: falha ao compilar.")
        print(build.stderr)
        sys.exit(1)
    return out_exe


def generate_backing_store(data_dir):
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "BACKING_STORE.bin")
    with open(path, "wb") as f:
        for i in range(65536):
            f.write(bytes([i % 256]))


def run_simulation_c(exe_path, addresses):
    """Executa o binário C com a lista de endereços e retorna as linhas de saída."""
    input_text = "\n".join(str(a) for a in addresses) + "\n"
    result = subprocess.run(
        [exe_path],
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=PROJECT_ROOT,
    )
    return result.stdout.strip().split("\n")

class VMSimulator:
    def __init__(self):
        self.reset()

    def reset(self):
        self.page_table = [
            {"frame": -1, "valid": 0, "ref_bit": 0, "aging": 0}
            for _ in range(256)
        ]
        self.tlb = [
            {"page": -1, "frame": -1, "valid": 0}
            for _ in range(TLB_SIZE)
        ]
        self.fifo_next   = 0
        self.frame_to_page = [-1] * NUM_FRAMES
        self.total     = 0
        self.faults    = 0
        self.tlb_hits  = 0


    def _tlb_lookup(self, page):
        for e in self.tlb:
            if e["valid"] and e["page"] == page:
                return e["frame"]
        return -1

    def _tlb_insert(self, page, frame):
        for e in self.tlb:
            if e["valid"] and e["page"] == page:
                e["frame"] = frame
                return
        for e in self.tlb:
            if not e["valid"]:
                e.update(page=page, frame=frame, valid=1)
                return
        self.tlb[self.fifo_next].update(page=page, frame=frame, valid=1)
        self.fifo_next = (self.fifo_next + 1) % TLB_SIZE

    def _tlb_remove(self, page):
        for e in self.tlb:
            if e["valid"] and e["page"] == page:
                e.update(page=-1, frame=-1, valid=0)
                return


    def _pt_lookup(self, page):
        e = self.page_table[page]
        return e["frame"] if e["valid"] else -1

    def _pt_update(self, page, frame):
        self.page_table[page].update(frame=frame, valid=1, ref_bit=0, aging=0)

    def _pt_invalidate(self, page):
        self.page_table[page].update(valid=0, frame=-1)

    def _pt_set_reference(self, page):
        e = self.page_table[page]
        if e["valid"]:
            e["ref_bit"] = 1

    def _pt_update_aging(self):
        for e in self.page_table:
            if not e["valid"]:
                continue
            new = (e["aging"] >> 1) & 0xFF
            if e["ref_bit"]:
                new |= 0x80
            e["aging"]   = new
            e["ref_bit"] = 0


    def _find_free_frame(self):
        for i, p in enumerate(self.frame_to_page):
            if p == -1:
                return i
        return -1

    def _select_victim(self):
        """
        Percorre page_table[0..255] (não frame_to_page) para replicar
        exatamente o select_victim_page() do C, que itera i de 0 a
        PAGE_TABLE_SIZE-1 e compara aging_counter.
        """
        min_c  = 256
        victim = -1
        for i, e in enumerate(self.page_table):
            if not e["valid"]:
                continue
            if victim == -1 or e["aging"] < min_c:
                min_c  = e["aging"]
                victim = i
        return victim

    def _backing_byte(self, page, offset):
        val = (page * PAGE_SIZE + offset) % 256
        return val - 256 if val >= 128 else val

    def _handle_fault(self, page):
        frame = self._find_free_frame()
        if frame == -1:
            vpage = self._select_victim()
            frame = self.page_table[vpage]["frame"]
            self.frame_to_page[frame] = -1
            self._pt_invalidate(vpage)
            self._tlb_remove(vpage)

        self.frame_to_page[frame] = page
        self._pt_update(page, frame)
        return frame

    def access(self, logical_address):
        logical_address &= 0xFFFF
        page   = (logical_address >> 8) & 0xFF
        offset =  logical_address & 0xFF

        frame = self._tlb_lookup(page)
        if frame != -1:
            self.tlb_hits += 1
        else:
            frame = self._pt_lookup(page)
            if frame == -1:
                self.faults += 1
                frame = self._handle_fault(page)
            self._tlb_insert(page, frame)

        self._pt_set_reference(page)
        self._pt_update_aging()

        self.total += 1
        pa    = frame * PAGE_SIZE + offset
        value = self._backing_byte(page, offset)
        return logical_address, pa, value

    def run(self, addresses):
        """Retorna lista de linhas de saída, igual ao formato do programa C."""
        lines = []
        for addr in addresses:
            la, pa, v = self.access(addr)
            lines.append(f"Logical address: {la} Physical address: {pa} Value: {v}")

        rf = self.faults   / self.total if self.total else 0.0
        rt = self.tlb_hits / self.total if self.total else 0.0
        lines.append(f"Number of Translated Addresses = {self.total}")
        lines.append(f"Page Faults = {self.faults}")
        lines.append(f"Page Fault Rate = {rf:.3f}")
        lines.append(f"TLB Hits = {self.tlb_hits}")
        lines.append(f"TLB Hit Rate = {rt:.3f}")
        return lines

def compare(test_name, expected, actual, spot_check_n=10):
    """
    Compara linha a linha. Para testes com muitas linhas (128+ endereços)
    exibe apenas as primeiras 'spot_check_n' divergências para não poluir
    o terminal.
    """
    passed = True
    errors = 0
    max_errors = spot_check_n

    total = max(len(expected), len(actual))
    for i in range(total):
        exp = expected[i].strip() if i < len(expected) else "<linha ausente>"
        got = actual[i].strip()   if i < len(actual)   else "<linha ausente>"
        if exp != got:
            if errors < max_errors:
                print(f"  [FAIL] Linha {i+1}")
                print(f"         Esperado: '{exp}'")
                print(f"         Recebido: '{got}'")
            errors += 1
            passed = False

    if errors > max_errors:
        print(f"  ... e mais {errors - max_errors} divergência(s) omitida(s).")

    return passed


# ─────────────────────────────────────────────────────────────────────────────
# ─── TESTE 1 ─── TLB FIFO + tlb_lookup   (T2.3 + T2.4)
#
# Objetivo
# ─────────
# Verificar que o TLB aceita exatamente TLB_SIZE=16 entradas únicas e, ao
# transbordar, substitui a entrada mais antiga (FIFO).
#
# Sequência (19 acessos, offset=0 em tudo → valor sempre 0):
#   1.  Página 0  – TLB Miss + Page Fault → Frame 0. TLB: [p0] (1 entrada)
#   2.  Página 0  – TLB HIT  (page 0 ainda no TLB)
#   3.  Página 1  – TLB Miss + Page Fault → Frame 1. TLB: [p0, p1]
#   4.  Página 2  – TLB Miss + Page Fault → Frame 2. TLB: [p0,p1,p2]
#   ...
#  18.  Página 15 – Fault → Frame 15. TLB cheio: [p0..p15]
#  19.  Página 16 – Fault → Frame 16. TLB cheio → FIFO expulsa p0 (slot 0).
#                   TLB: [p16, p1..p15]
#  20.  Página 0  – TLB MISS (p0 foi expulso pelo FIFO)
#                   Page Table HIT (p0 ainda na memória física, frame 0)
#                   Não é fault, não é TLB hit.
#
# Estatísticas esperadas:
#  20.  Pagina 0  - TLB MISS (p0 foi expulso pelo FIFO)
#                   Page Table HIT (p0 ainda na memoria fisica, frame 0)
#                   Nao e fault, nao e TLB hit.
#
# Estatisticas esperadas:
#   Total = 19, Faults = 17, TLB Hits = 1
#   Fault Rate = 17/19 = 0.895, TLB Hit Rate = 1/19 = 0.053
# -----------------------------------------------------------------------------

def test_tlb_fifo(exe_path):
    print("\n=== Teste 1: TLB FIFO + tlb_lookup (T2.3/T2.4) ===")

    addresses = (
        [0, 0]                          
        + [p * 256 for p in range(1, 16)]  
        + [16 * 256]                    
        + [0]                           
    )

    sim = VMSimulator()
    expected = sim.run(addresses)
    actual   = run_simulation_c(exe_path, addresses)

    passed = compare("TLB FIFO", expected, actual)

    stats_lines = actual[-5:]
    checks = [
        ("Number of Translated Addresses = 19", stats_lines[0].strip()),
        ("Page Faults = 17",                   stats_lines[1].strip()),
        ("TLB Hits = 1",                        stats_lines[3].strip()),
    ]
    for exp, got in checks:
        if exp != got:
            print(f"  [FAIL STATS] Esperado '{exp}' | Recebido '{got}'")
            passed = False
        else:
            print(f"  [PASS STATS] {got}")

    return passed


# -----------------------------------------------------------------------------
# --- TESTE 2 --- Aging / LRU + Substituicao + tlb_remove  (T2.1/T2.2/T2.5)
#
# Objetivo
# ---------
# Verificar que a selecao de vitima usa o aging_counter corretamente:
# a pagina mais recentemente referenciada deve sobreviver a substituicao.
#
# Sequencia (132 acessos):
#
# Fase A (128 acessos) - Preenche todos os 128 frames:
#   Acessa paginas 0..127, cada uma uma vez, offset=0.
#   Apos a fase A:
#     - Frame K <- Pagina K  (para K=0..127)
#     - Contadores de aging (apos 128 rodadas de update_aging):
#         Pagina 0  : aging = 0x80 >> 127 = 0   (envelheceu muito)
#         Pagina 1  : aging = 0x80 >> 126 = 0
#         ...
#         Pagina 119: aging = 0x80 >> 8   = 0
#         Pagina 120: aging = 0x80 >> 7   = 0x01
#         ...
#         Pagina 127: aging = 0x80 >> 0   = 0x80 (recem-acessada)
#
# Fase B (2 acessos) - Torna a pagina 0 "quente" (T2.1 critico):
#   Acesso B1: Pagina 0
#     - TLB miss (p0 foi expulso do TLB no acesso 17)
#     - Page Table HIT (p0 ainda no frame 0)
#     - set_reference(0): ref_bit=1
#     - update_aging(): p0 aging = 0x80 (ref_bit era 1)
#   Acesso B2: Pagina 0
#     - TLB HIT (p0 foi reinserido no TLB no acesso B1)
#     - set_reference(0): ref_bit=1 novamente
#     - update_aging(): p0 aging = 0xC0 (0x80>>1=0x40; |0x80=0xC0)
#   Depois dos acessos B: p0.aging = 0xC0; p1.aging = 0 (e pages 1..120 = 0)
#
# Fase C (1 acesso) - Dispara a substituicao (T2.2 critico):
#   Acesso C: Pagina 128 -> TLB miss + Page Fault (memoria cheia)
#     - select_victim: percorre page_table[0..255], acha primeiro com menor aging
#       - p0: 0xC0  <- quente, nao sera vitima
#       - p1: 0x00  <- VITIMA (aging minimo, primeira encontrada no loop)
#     - Vitima = pagina 1 (frame 1)
#     - page_table_invalidate(1); tlb_remove(1)   (T2.5)
#     - Frame 1 <- Pagina 128
#
# Fase D (2 acessos) - Confirmacao dos resultados:
#   Acesso D1: Pagina 0
#     - Deve ser TLB HIT (p0 foi re-inserido no TLB no acesso B1)
#     - NAO deve gerar page fault (p0 ainda esta em memoria)
#   Acesso D2: Pagina 1
#     - TLB miss + Page Table MISS -> PAGE FAULT
#       (p1 foi desalocada na fase C)
#     - Isso prova que o aging preservou p0 e escolheu p1 como vitima.
# -----------------------------------------------------------------------------

def test_aging_and_substitution(exe_path):
    print("\n=== Teste 2: Aging/LRU + Substituicao + tlb_remove (T2.1/T2.2/T2.5) ===")

    phase_a = [p * 256 for p in range(128)]      
    phase_b = [0, 0]                              
    phase_c = [128 * 256]                         
    phase_d = [0, 1 * 256]                        

    addresses = phase_a + phase_b + phase_c + phase_d  # 133 enderecos

    sim = VMSimulator()
    expected = sim.run(addresses)
    actual   = run_simulation_c(exe_path, addresses)

    passed = compare("Aging + Substituicao", expected, actual)

    # Verificacoes explicitas nas ultimas 4 linhas de traducao (fase D)
    # e nas estatisticas.
    #
    # Fase D, acesso D1 (linha 130 = indice 129 da saida):
    #   p0 deve ser TLB hit  -> physical address = 0  (frame 0, offset 0)
    # Fase D, acesso D2 (linha 131 = indice 130 da saida):
    #   p1 deve ser fault     -> physical address = 1*256 = 256 (frame 1, offset 0)
    #
    # Estatisticas (ultimas 5 linhas):
    #   Total  = 132
    #   Faults = 128 (fase A) + 0 (fase B) + 1 (fase C) + 0 (D1) + 1 (D2) = 130
    #   TLB Hits = 1 (fase B, acesso B2) + 1 (fase D, acesso D1) = 2

    stats_lines = actual[-5:]
    checks = [
        ("Number of Translated Addresses = 133", stats_lines[0].strip()),
        ("Page Faults = 130",                    stats_lines[1].strip()),
        ("TLB Hits = 2",                         stats_lines[3].strip()),
    ]
    for exp, got in checks:
        if exp != got:
            print(f"  [FAIL STATS] Esperado '{exp}' | Recebido '{got}'")
            passed = False
        else:
            print(f"  [PASS STATS] {got}")

    # Verificacao da linha D1 (acesso 130 -> indice 129)
    exp_d1 = expected[129].strip()
    got_d1 = actual[129].strip() if len(actual) > 129 else "<ausente>"
    label  = "D1 - p0 nao e fault (TLB hit)"
    if exp_d1 == got_d1:
        print(f"  [PASS] {label}: '{got_d1}'")
    else:
        print(f"  [FAIL] {label}")
        print(f"         Esperado: '{exp_d1}'")
        print(f"         Recebido: '{got_d1}'")
        passed = False

    # Verificacao da linha D2 (acesso 131 -> indice 130)
    exp_d2 = expected[130].strip()
    got_d2 = actual[130].strip() if len(actual) > 130 else "<ausente>"
    label  = "D2 - p1 e fault (foi expulsa pela vitima LRU)"
    if exp_d2 == got_d2:
        print(f"  [PASS] {label}: '{got_d2}'")
    else:
        print(f"  [FAIL] {label}")
        print(f"         Esperado: '{exp_d2}'")
        print(f"         Recebido: '{got_d2}'")
        passed = False

    return passed


# -----------------------------------------------------------------------------
# --- TESTE 3 --- tlb_remove na desalocacao  (T2.5 isolado)
#
# Objetivo
# ---------
# Verificar que, ao remover uma pagina da memoria fisica durante substituicao,
# a entrada correspondente e INVALIDADA no TLB. Se tlb_remove nao funcionar,
# o TLB pode retornar um frame antigo (ja reatribuido a outra pagina),
# causando leitura de dado errado.
#
# Sequencia (35 acessos):
#
# Fase A (16 acessos) - Preenche o TLB com p0..p15:
#   Acessa paginas 0..15, cada uma 1x.
#   TLB cheio: slots 0..15 = p0..p15.
#
# Fase B (1 acesso) - Re-acessa p0 para tela no TLB e quente:
#   - TLB HIT -> p0.ref_bit = 1
#   -> p0.aging fica alto apos update_aging.
#
# Fase C (112 acessos) - Preenche frames restantes (p16..p127):
#   128 frames total - 16 ja ocupados = 112 novos frames.
#   Cada acesso e um page fault; o TLB FIFO vai expulsando p0..p15
#   mas p0..p15 permanecem na memoria fisica.
#
# Fase D (1 acesso) - Re-acessa p0 para reinserir no TLB:
#   - TLB miss (p0 foi expulso do TLB durante a fase C)
#   - Page Table HIT (p0 ainda na memoria)
#   -> p0 reinserida no TLB, p0.ref_bit = 1, aging sobe para 0x80.
#
# Fase E (1 acesso) - Dispara substituicao com p128:
#   - Page fault + memoria cheia
#   - Vitima: pagina com menor aging_counter
#     - p0 tem aging alto (fase B + D = 0xC0 aprox)  -> sobrevive
#     - p1 tem aging = 0 (so 1 acesso, ha muito tempo)  -> VITIMA
#   - tlb_remove(p1): se p1 estivesse no TLB, deve ser removida.
#   - Frame de p1 <- p128.
#
# Fase F (2 acessos) - Verificacao:
#   F1: Pagina 0 -> deve ser TLB hit ou page table hit, nunca fault.
#   F2: Pagina 1 -> deve ser page fault (foi desalocada na fase E).
# -----------------------------------------------------------------------------

def test_tlb_remove_on_eviction(exe_path):
    print("\n=== Teste 3: tlb_remove na desalocacao (T2.5 isolado) ===")

    phase_a = [p * 256 for p in range(16)]        
    phase_b = [0]                                 
    phase_c = [p * 256 for p in range(16, 128)]   
    phase_d = [0]                                  
    phase_e = [128 * 256]                         
    phase_f = [0, 1 * 256]                         

    addresses = phase_a + phase_b + phase_c + phase_d + phase_e + phase_f

    sim = VMSimulator()
    expected = sim.run(addresses)
    actual   = run_simulation_c(exe_path, addresses)

    passed = compare("tlb_remove", expected, actual)

    stats_lines = actual[-5:]
    checks = [
        ("Number of Translated Addresses = 133", stats_lines[0].strip()),
        ("Page Faults = 130",                    stats_lines[1].strip()),
    ]
    for exp, got in checks:
        if exp != got:
            print(f"  [FAIL STATS] Esperado '{exp}' | Recebido '{got}'")
            passed = False
        else:
            print(f"  [PASS STATS] {got}")

    return passed


# -----------------------------------------------------------------------------
# Ponto de entrada
# -----------------------------------------------------------------------------

def main():
    print("=======================================")
    print("  Testes da Sprint 2")
    print("=======================================")

    generate_backing_store(os.path.join(PROJECT_ROOT, "data"))
    exe = build_project()
    print(f"Binario: {exe}")

    results = {
        "Teste 1 - TLB FIFO + tlb_lookup":               test_tlb_fifo(exe),
        "Teste 2 - Aging/LRU + Substituicao + tlb_remove": test_aging_and_substitution(exe),
        "Teste 3 - tlb_remove isolado":                   test_tlb_remove_on_eviction(exe),
    }

    print("\n=======================================")
    print("  Resultado Final")
    print("=======================================")
    all_passed = True
    for name, ok in results.items():
        status = "[PASSOU]" if ok else "[FALHOU]"
        print(f"  {status}  {name}")
        if not ok:
            all_passed = False

    print()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
