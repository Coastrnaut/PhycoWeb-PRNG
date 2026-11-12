# Feature 005: the ARX trail search's companion (research R7), built as feature 004's tool is. Build in WSL, from the repository's root:
#     make -f research/005/tools/trails/arx_search_ops.mk
# Relative paths and no debug information, so that the same source gives the same binary in any directory.

CC := gcc
CFLAGS := -O2 -std=c99 -Wall -Wextra -Werror
DIRECTORY := research/005/tools/trails
BUILD := $(DIRECTORY)/build
SOURCE_SHA256 := $(shell sha256sum $(DIRECTORY)/arx_search_ops.c | cut -d' ' -f1)

$(BUILD)/arx_search_ops: $(DIRECTORY)/arx_search_ops.c $(DIRECTORY)/arx_search_ops.mk | $(BUILD)
	$(CC) $(CFLAGS) -DSOURCE_SHA256='"$(SOURCE_SHA256)"' -o $@ $(DIRECTORY)/arx_search_ops.c

$(BUILD):
	mkdir -p $(BUILD)
