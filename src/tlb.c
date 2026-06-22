#include "tlb.h"
#include "config.h"

static tlb_entry_t tlb[TLB_SIZE];

/*
 * Índice da próxima posição a ser substituída.
 * Essa variável implementa FIFO no TLB.
 */
static int fifo_next = 0;

void tlb_init(void)
{
    for (int i = 0; i < TLB_SIZE; i++) {
        tlb[i].page = -1;
        tlb[i].frame = -1;
        tlb[i].valid = 0;
    }

    fifo_next = 0;
}

int tlb_lookup(int page)
{
    /*
     * TODO:
     * Procurar a página no TLB.
     * Se encontrar uma entrada válida, retornar o quadro.
     * Caso contrário, retornar -1.
     */

    (void) page;
    return -1;
}

void tlb_insert(int page, int frame)
{
    for (int i = 0; i < TLB_SIZE; i++) {
        if (tlb[i].valid && tlb[i].page == page) {
            tlb[i].frame = frame;
            return;
        }
    }

    for (int i = 0; i < TLB_SIZE; i++) {
        if (!tlb[i].valid) {
            tlb[i].page = page;
            tlb[i].frame = frame;
            tlb[i].valid = 1;
            return;
        }
    }

    tlb[fifo_next].page = page;
    tlb[fifo_next].frame = frame;
    tlb[fifo_next].valid = 1;
    fifo_next = (fifo_next + 1) % TLB_SIZE;
}

void tlb_remove(int page)
{
    /*
     * TODO:
     * Invalidar uma entrada do TLB associada à página informada.
     * Essa função deve ser usada quando uma página for removida
     * da memória física.
     */

    (void) page;
}

void tlb_clear(void)
{
    tlb_init();
}