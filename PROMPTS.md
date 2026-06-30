# 📋 Planejamento de Engenharia de Prompts (Metodologia SDD)

[cite_start]Este documento descreve a estratégia de engenharia de prompts utilizada para o desenvolvimento incremental e modular do simulador de memória virtual, seguindo rigorosamente o modelo **Spec-Driven Development (SDD)** exigido pelas diretrizes do projeto. 

Em vez de gerar o código de uma única vez, o escopo foi fragmentado em tarefas menores e sequenciais. [cite_start]Isso garante o controle total sobre as estruturas de dados, evita códigos redundantes e respeita todas as restrições arquiteturais impostas.

---

## 🛠️ Restrições Globais Aplicadas (Configuração dos Agentes)
Todos os prompts gerados impõem as seguintes regras fundamentais:
* **Linguagem:** Codificação estritamente em C.
* **Idioma:** Nomenclatura de novas variáveis e funções obrigatoriamente em inglês.
* **Código Limpo:** Proibição de comentários automáticos ou explicações redundantes no meio do código.
* [cite_start]**Integridade:** Proibição de refatorar códigos legados ou modificar arquivos das pastas protegidas (`include/`, `report/` e `data/`).

---

## 🚀 Fases do Desenvolvimento Incremental

### 📂 Fase 1: Extração de Endereços e Mascaramento
* [cite_start]**Objetivo:** Isolar os componentes de endereçamento a partir do endereço lógico de 32 bits lido do arquivo de entrada.
* [cite_start]**Escopo:** * Aplicação de máscara binária para considerar apenas os 16 bits da extrema direita.
  * [cite_start]Separação dos 8 bits mais significativos para o **Número de Página** e dos 8 bits menos significativos para o **Deslocamento (Offset)**.

### 🗂️ Fase 2: Estruturas de Mapeamento Principal (Tabela de Páginas)
* [cite_start]**Objetivo:** Manipular os estados de residência das páginas na memória física.
* **Escopo:**
  * **Busca (`page_table_lookup`):** Verificar o bit de validade; retornar o quadro correspondente se ativo ou `-1` em caso de falha (*page fault*).
  * [cite_start]**Modificação (`page_table_update` & `page_table_invalidate`):** Atualizar mapeamentos página $\rightarrow$ quadro, gerenciar bits de validade e inicializar metadados para as políticas de substituição.

### 💾 Fase 3: Memória Secundária e Paginação por Demanda
* [cite_start]**Objetivo:** Orquestrar o fluxo de dados entre o armazenamento em disco e a memória volátil quando ocorre uma falha de página.
* **Escopo:**
  * [cite_start]Leitura aleatória via `fseek` e `fread` de blocos exatos de 256 bytes do arquivo `BACKING_STORE.bin`.
  * [cite_start]Verificação de quadros livres na memória física (limite estrito de 128 quadros) antes de injetar os dados.

### 🔄 Fase 4: Políticas de Substituição (Aging & FIFO)
* [cite_start]**Objetivo:** Substituir dados de forma inteligente quando os limites de hardware simulado forem atingidos.
* **Escopo:**
  * [cite_start]**Substituição de Páginas (Algoritmo de Envelhecimento):** Atualização periódica de contadores de 8 bits a cada acesso utilizando operadores *bitwise* (`counter >> 1`), inserindo o bit de referência no MSB e removendo a página de menor valor numérico.
  * [cite_start]**Substituição no TLB (Política FIFO):** Controle de cache com capacidade de 16 entradas, descartando a entrada mais antiga em cenários de saturação.

### 📊 Fase 5: Métricas Operacionais e Finalização
* [cite_start]**Objetivo:** Consolidar os dados operacionais ao término da simulação para emissão do relatório analítico.
* **Escopo:**
  * [cite_start]Cálculo exato do valor do byte sinalizado contido no endereço físico resultante.
  * [cite_start]Computação exata da **Taxa de Erros de Página** (*Page Fault Rate*) e da **Taxa de Sucesso do TLB** (*TLB Hit Rate*).

---
[cite_start]_Nota: A documentação completa com o conteúdo textual de cada prompt enviado durante o desenvolvimento pode ser consultada na seção correspondente do relatório técnico em PDF