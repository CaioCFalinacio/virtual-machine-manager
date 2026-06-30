#include <stdio.h>
#include <stdlib.h>
#include "memory.h"
#include "config.h"
#include "page_table.h"
#include "tlb.h"

static signed char physical_memory[NUM_FRAMES][FRAME_SIZE];

/*
 * Indica qual página está carregada em cada quadro.
 * Valor -1 indica quadro livre.
 */
static int frame_to_page[NUM_FRAMES];

static FILE *backing = NULL;

void memory_init(FILE *backing_store)
{
    backing = backing_store;

    for (int i = 0; i < NUM_FRAMES; i++) {
        frame_to_page[i] = -1;

        for (int j = 0; j < FRAME_SIZE; j++) {
            physical_memory[i][j] = 0;
        }
    }
}

static int find_free_frame(void)
{
    for (int i = 0; i < NUM_FRAMES; i++) {
        if (frame_to_page[i] == -1) {
            return i;
        }
    }

    return -1;
}

int handle_page_fault(int page)
{
    int frame = find_free_frame();

    if (frame == -1) {
        int victim_page = select_victim_page();

        frame = page_table_get_frame(victim_page);
        frame_to_page[frame] = -1;
        page_table_invalidate(victim_page);
        tlb_remove(victim_page);
    }

    if (backing == NULL) {
        fprintf(stderr, "Erro interno: BACKING_STORE nao inicializado.\n");
        exit(1);
    }

    if ((page * PAGE_SIZE + PAGE_SIZE) > (PAGE_TABLE_SIZE * PAGE_SIZE)) {
        fprintf(stderr, "Erro: page %d fora dos limites do BACKING_STORE.\n", page);
        exit(1);
    }

    if (frame < 0 || frame >= NUM_FRAMES) {
        fprintf(stderr, "Erro: frame %d invalido para escrita em physical_memory.\n", frame);
        exit(1);
    }

    fseek(backing, page * PAGE_SIZE, SEEK_SET);
    fread(physical_memory[frame], 1, PAGE_SIZE, backing);
    
    frame_to_page[frame] = page;
    page_table_update(page, frame);

    return frame;
}

int select_victim_page(void)
{
    int victim = -1;
    unsigned char min_counter = 0xFF;

    for (int i = 0; i < PAGE_TABLE_SIZE; i++) {
        if (!page_table_is_valid(i)) {
            continue;
        }

        unsigned char counter = page_table_get_aging_counter(i);

        if (victim == -1 || counter < min_counter) {
            min_counter = counter;
            victim = i;
        }
    }

    return victim;
}

signed char read_memory(int frame, int offset)
{
    if (frame < 0 || frame >= NUM_FRAMES || offset < 0 || offset >= FRAME_SIZE) {
        return 0;
    }

    return physical_memory[frame][offset];
}

int get_page_loaded_in_frame(int frame)
{
    if (frame < 0 || frame >= NUM_FRAMES) {
        return -1;
    }

    return frame_to_page[frame];
}
