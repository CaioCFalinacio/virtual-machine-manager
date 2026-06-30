#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "config.h"
#include "page_table.h"
#include "tlb.h"
#include "memory.h"
#include "statistics.h"

void test_frame_saturation_aging(void)
{
    page_table_init();
    tlb_init();
    
    FILE *dummy_backing = fopen(BACKING_STORE_PATH, "rb");
    if (dummy_backing == NULL) {
        return;
    }
    memory_init(dummy_backing);
    
    for (int i = 0; i < NUM_FRAMES; i++) {
        int frame = handle_page_fault(i);
        tlb_insert(i, frame);
        page_table_set_reference(i);
        page_table_update_aging();
    }
    
    int new_page = NUM_FRAMES;
    int frame = handle_page_fault(new_page);
    tlb_insert(new_page, frame);
    
    assert(page_table_is_valid(0) == 0);
    assert(page_table_get_frame(0) == -1);
    assert(tlb_lookup(0) == -1);
    
    fclose(dummy_backing);
}

void test_consecutive_tlb_hits(void)
{
    page_table_init();
    tlb_init();
    statistics_init();
    
    int test_page = 5;
    int test_frame = 10;
    
    page_table_update(test_page, test_frame);
    tlb_insert(test_page, test_frame);
    
    int num_hits = 5;
    for (int i = 0; i < num_hits; i++) {
        int frame = tlb_lookup(test_page);
        if (frame != -1) {
            count_tlb_hit();
        }
        page_table_set_reference(test_page);
    }
    
    assert(get_tlb_hits() == num_hits);
}

void test_null_address_translation(void)
{
    int logical_address = 0x00000000;
    
    int masked_address = logical_address & 0xFFFF;
    int page = (masked_address >> 8) & 0xFF;
    int offset = masked_address & 0xFF;
    
    assert(page == 0);
    assert(offset == 0);
    
    FILE *dummy_backing = fopen(BACKING_STORE_PATH, "rb");
    if (dummy_backing == NULL) {
        return;
    }
    
    memory_init(dummy_backing);
    page_table_init();
    tlb_init();
    
    int frame = handle_page_fault(page);
    
    signed char value = read_memory(frame, offset);
    (void) value; 
    
    assert(page_table_is_valid(page) == 1);
    assert(page_table_get_frame(page) == frame);
    
    fclose(dummy_backing);
}
