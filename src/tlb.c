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
    for (int i = 0; i < TLB_SIZE; i++) {
        if (tlb[i].valid && tlb[i].page == page) {
            return tlb[i].frame;
        }
    }
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

    if (fifo_next < 0 || fifo_next >= TLB_SIZE) {
        fifo_next = 0;
    }
    tlb[fifo_next].page = page;
    tlb[fifo_next].frame = frame;
    tlb[fifo_next].valid = 1;
    fifo_next = (fifo_next + 1) % TLB_SIZE;
}

void tlb_remove(int page)
{
    for (int i = 0; i < TLB_SIZE; i++) {
        if (tlb[i].valid == 1 && tlb[i].page == page) {
            tlb[i].valid = 0;
            tlb[i].page = -1;
            tlb[i].frame = -1;
            break;
        }
    }
}

void tlb_clear(void)
{
    tlb_init();
}