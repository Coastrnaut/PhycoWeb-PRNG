# Feature 004: the ARX trail search (research R12, R16, R18). Build in WSL, from the repository's root:
#     make -f research/004/tools/trails/arx_search.mk
# Relative paths and no debug information, so that the same source gives the same binary in any directory.

CC := gcc
CFLAGS := -O2 -std=c99 -Wall -Wextra -Werror
DIRECTORY := research/004/tools/trails
BUILD := $(DIRECTORY)/build
SOURCE_SHA256 := $(shell sha256sum $(DIRECTORY)/arx_search.c | cut -d' ' -f1)

$(BUILD)/arx_search: $(DIRECTORY)/arx_search.c $(DIRECTORY)/arx_search.mk | $(BUILD)
	$(CC) $(CFLAGS) -DSOURCE_SHA256='"$(SOURCE_SHA256)"' -o $@ $(DIRECTORY)/arx_search.c

$(BUILD):
	mkdir -p $(BUILD)
