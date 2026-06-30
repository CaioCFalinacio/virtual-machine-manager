#include "page_table.h"
#include "config.h"

static page_table_entry_t page_table[PAGE_TABLE_SIZE];

void page_table_init(void)
{
    for (int i = 0; i < PAGE_TABLE_SIZE; i++) {
        page_table[i].frame = -1;
        page_table[i].valid = 0;
        page_table[i].reference_bit = 0;
        page_table[i].aging_counter = 0;
    }
}

int page_table_lookup(int page)
{
    if (page >= 0 && page < PAGE_TABLE_SIZE && page_table[page].valid) {
        return page_table[page].frame;
    }
    return -1;
}

void page_table_update(int page, int frame)
{
    if (page >= 0 && page < PAGE_TABLE_SIZE) {
        page_table[page].frame = frame;
        page_table[page].valid = 1;
        page_table[page].reference_bit = 0;
        page_table[page].aging_counter = 0;
    }
}

void page_table_invalidate(int page)
{
    if (page >= 0 && page < PAGE_TABLE_SIZE) {
        page_table[page].valid = 0;
        page_table[page].frame = -1;
    }
}

void page_table_set_reference(int page)
{
<<<<<<< HEAD
    if (page >= 0 && page < PAGE_TABLE_SIZE) {
=======
    if (page >= 0 && page < PAGE_TABLE_SIZE && page_table[page].valid) {
>>>>>>> 5969e3f5d3ef0b3440bea494471f5a1a5e8cd091
        page_table[page].reference_bit = 1;
    }
}

void page_table_update_aging(void)
{
    for (int i = 0; i < PAGE_TABLE_SIZE; i++) {
<<<<<<< HEAD
        if (page_table[i].valid == 1) {
            page_table[i].aging_counter >>= 1;
            if (page_table[i].reference_bit == 1) {
                page_table[i].aging_counter |= 0x80;
            }
            page_table[i].reference_bit = 0;
        }
=======
        if (!page_table[i].valid) {
            continue;
        }

        page_table[i].aging_counter >>= 1;

        if (page_table[i].reference_bit) {
            page_table[i].aging_counter |= 0x80;
        }

        page_table[i].reference_bit = 0;
>>>>>>> 5969e3f5d3ef0b3440bea494471f5a1a5e8cd091
    }
}

int page_table_get_frame(int page)
{
    if (page < 0 || page >= PAGE_TABLE_SIZE) {
        return -1;
    }

    return page_table[page].frame;
}

int page_table_is_valid(int page)
{
    if (page < 0 || page >= PAGE_TABLE_SIZE) {
        return 0;
    }

    return page_table[page].valid;
}

unsigned char page_table_get_aging_counter(int page)
{
    if (page < 0 || page >= PAGE_TABLE_SIZE) {
        return 0;
    }

    return page_table[page].aging_counter;
}
