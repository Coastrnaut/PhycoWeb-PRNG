# Feature 003 fast tooling (research R4, R7). Build in WSL: make -C fast
# The TestU01 driver needs TESTU01_DIR (default ~/testu01, from fast/build_tools.sh).

CC ?= gcc
CFLAGS := -O2 -std=c99 -Wall -Wextra -Werror
BUILD := build
TESTU01_DIR ?= $(HOME)/testu01

all: $(BUILD)/phyco_stream

$(BUILD)/phyco_stream: phyco_stream.c lut_table.h | $(BUILD)
	$(CC) $(CFLAGS) -o $@ phyco_stream.c

$(BUILD)/testu01_driver: testu01_driver.c | $(BUILD)
	$(CC) -O2 -std=gnu99 -Wall -Wextra -Werror -I$(TESTU01_DIR)/include -o $@ testu01_driver.c \
		-L$(TESTU01_DIR)/lib -Wl,-rpath,$(TESTU01_DIR)/lib -ltestu01 -lprobdist -lmylib -lm

$(BUILD):
	mkdir -p $(BUILD)

clean:
	rm -rf $(BUILD)

.PHONY: all clean
