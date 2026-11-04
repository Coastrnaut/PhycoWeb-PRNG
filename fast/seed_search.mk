# Feature 004: the FUT-SEC-8 search tool (research R2, R16). Build in WSL:
#     make -C fast -f seed_search.mk
# Its own build file: a new target in fast/Makefile could rebuild the binary that feature 003's
# freeze records. Relative paths and no debug information, so that the same source gives the same
# binary in any directory. EXTRA is for the tests' small builds, in directories of their own.

CC := gcc
CFLAGS := -O2 -std=c99 -Wall -Wextra -Werror -pthread
BUILD := build
SOURCE_SHA256 := $(shell sha256sum seed_search.c | cut -d' ' -f1)

$(BUILD)/seed_search: seed_search.c lut_table.h seed_search.mk | $(BUILD)
	$(CC) $(CFLAGS) $(EXTRA) -DSOURCE_SHA256='"$(SOURCE_SHA256)"' -o $@ seed_search.c

$(BUILD):
	mkdir -p $(BUILD)
