CC := gcc
CFLAGS := -g
BUILD_DIR := ./build

all: $(BUILD_DIR)/read $(BUILD_DIR)/read_local $(BUILD_DIR)/getcwd $(BUILD_DIR)/sched_yield

$(BUILD_DIR)/read_file.txt:
	python3 -c "with open('$(BUILD_DIR)/read_file.txt', 'w') as f: f.write('.'*2000000)"

$(BUILD_DIR)/read: read.c build_config.h
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) -o $@ $<

$(BUILD_DIR)/read_local: read_local.c build_config.h $(BUILD_DIR)/read_file.txt
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) -o $@ $<

$(BUILD_DIR)/getcwd: getcwd.c build_config.h
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) -o $@ $<

$(BUILD_DIR)/sched_yield: sched_yield.c build_config.h
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) -o $@ $<

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)
