#include <unistd.h>
#include <fcntl.h>
#include "build_config.h"

char buf[1];

int main(int argc, char **argv)
{
	int fd = open("build/read_file.txt", O_RDONLY);
	if(0 > fd) {
		return 2;
	}
	for(long i = 0; i < ITERATIONS; i++) {
		if(sizeof(buf) != read(fd, buf, sizeof(buf))) {
			return 1;
		}
	}
	return 0;
}
