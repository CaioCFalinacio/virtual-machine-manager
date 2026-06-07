# Especificação Técnica: Gerenciador de Memória Virtual

Este documento estabelece as especificações técnicas, restrições de arquitetura e requisitos funcionais para o desenvolvimento do simulador de memória virtual em C.

---

## 1. Mapeamento e Estrutura de Endereçamento

O programa realiza a tradução de endereços lógicos (virtuais) de 32 bits, operando sob as seguintes restrições de espaço:

* **Espaço de Endereçamento Virtual:** $2^{16} = 65.536$ bytes
* **Mascaramento:** Apenas os 16 bits da extrema direita de cada endereço lógico de 32 bits devem ser considerados
* **Divisão do Endereço Lógico (16 bits):**
  * **Número de Página:** 8 bits mais significativos (bits 8 a 15)
  * **Deslocamento (Offset):** 8 bits menos significativos (bits 0 a 7)

---

## 2. Dimensionamento dos Componentes do Sistema

O simulador deve obedecer rigorosamente às seguintes dimensões de hardware simulado:

* **Tamanho da Página Virtual:** 256 bytes
* **Tamanho do Quadro Físico (Frame):** 256 bytes
* **Número de Entradas na Tabela de Páginas:** 256 entradas
* **Capacidade da Memória Física:** 32.768 bytes (mapeados em exatamente **128 quadros**)
* **Capacidade do TLB (Translation Lookaside Buffer):** 16 entradas

---

## 3. Fluxo de Tradução de Endereços

Para cada endereço lógico lido, o fluxo de tradução deve seguir a ordem abaixo:

1. **Consulta ao TLB:** O número da página extraído é buscado no TLB
   * **TLB Hit:** O número do quadro físico é extraído diretamente do TLB.
2. **Consulta à Tabela de Páginas:** Em caso de *TLB Miss* (omissão), a Tabela de Páginas deve ser consultada.
   * **Page Hit:** O número do quadro correspondente é recuperado da tabela.
   * **Page Fault:** Se a página não estiver residente na memória física, o mecanismo de paginação por demanda deve ser acionado.

---

## 4. Mecanismo de Paginação por Demanda e Memória de Retaguarda

* **Arquivo de Backup:** A memória secundária é representada pelo arquivo binário `BACKING_STORE.bin` (tamanho fixo de 65.536 bytes).
* **Tratamento de Page Fault:**
  1. A página faltante deve ser localizada no arquivo `BACKING_STORE.bin` por meio de busca de acesso aleatório (usando comandos como `fseek` e `fread`). O bloco a ser lido possui exatamente 256 bytes (calculado por $Nº\_da\_Página \times 256$).
  2. O bloco lido deve ser armazenado em um quadro disponível na memória física.
  3. A Tabela de Páginas e o TLB devem ser atualizados com o novo mapeamento página $\rightarrow$ quadro.

---

## 5. Políticas de Substituição e Atualização

Como a memória física (128 quadros) é menor que o espaço virtual (256 páginas), mecanismos de substituição de dados devem ser executados quando o sistema atingir a capacidade máxima.

### 5.1 Substituição de Páginas na Memória Física: Algoritmo de Envelhecimento (*Aging*)
Para cada página residente na memória física, o simulador deve manter:
* Um **bit de referência (R)**.
* Um **contador de envelhecimento (aging counter) de 8 bits**.

**Regras de operação do Aging:**
* **Acesso:** Sempre que uma página for referenciada (leitura), seu bit de referência $R$ deve ser marcado como `1`.
* **Atualização Periódica:** A cada intervalo de atualização (a cada acesso à memória), todos os contadores de envelhecimento do sistema devem ser atualizados seguindo os passos:
  1. O contador de 8 bits é deslocado uma posição para a direita (`counter >> 1`).
  2. O valor atual do bit de referência ($R$) é inserido no bit mais significativo (MSB) do contador.
  3. O bit de referência ($R$) é zerado ($R = 0$).
* **Seleção para Remoção:** Quando ocorrer um *page fault* e não houver quadros livres, a página que contiver o **menor valor numérico** em seu contador de envelhecimento deve ser escolhida para remoção.
* **Invalidação:** Ao remover a página escolhida, sua entrada correspondente na Tabela de Páginas deve ser invalidada. Se houver uma entrada correspondente ativa no TLB, ela também deve ser invalidada ou removida.

### 5.2 Substituição de Entradas no TLB: Política FIFO
* Quando o TLB estiver cheio (16 entradas ocupadas) e uma nova tradução precisar ser injetada nele (decorrente de uma consulta à Tabela de Páginas), a substituição de entradas do TLB deve seguir estritamente a política **First-In, First-Out (FIFO)**.

---

## 6. Operações de Saída e Métricas Corporativas

O programa limita-se exclusivamente a **operações de leitura** no espaço endereçável (não há suporte para escrita em memória). Após o processamento do arquivo de entrada contendo os endereços, o sistema deve computar e exibir as seguintes estatística:

1. **Valor do Byte:** O valor do byte sinalizado contido no endereço físico resultante de cada tradução.
2. **Taxa de Erros de Página (Page Fault Rate):** Percentual de referências de endereços que resultaram em falhas de página.
3. **Taxa de Sucesso do TLB (TLB Hit Rate):** Percentual de referências de endereços resolvidas diretamente por meio do TLB.
  