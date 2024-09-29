#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include "3dmm.h"

void print_hex_dump(const char *data, long size) {
    char line[100];
    int index = 0;

    for (long i = 0; i < size; i++) {
        int written = snprintf(&line[index], sizeof(line) - index, "%02X ", (unsigned char)data[i]);
        if (written < 0) {
            printf("Error in formatting\n");
            return;
        }
        index += written;
        if ((i + 1) % 16 == 0 || i == size - 1) {
            line[index] = '\0';
            printf("%s\n", line);
            index = 0;
        }
    }
}


int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <filename>\n", argv[0]);
        return 1;
    }

    ChunkFile cfl = {0};

    cfl.file = fopen(argv[1], "rb");
    if (cfl.file == NULL) {
        perror("Error opening file");
        return 1;
    }

    fseek(cfl.file, 0, SEEK_END);
    long file_size = ftell(cfl.file);
    fseek(cfl.file, 0, SEEK_SET);

    char *data_array = (char *)malloc(file_size);
    if (data_array == NULL) {
        perror("Memory allocation error");
        fclose(cfl.file);
        return 1;
    }

    fread(data_array, 1, file_size, cfl.file);

    void *p = &data_array[0];
    printf("Magic: %.*s\n", 4, (char*)p);

  //int version;
  //int headerSize;
  //int fileSize;

    //print_hex_dump(data_array, file_size);

    //MMHeader *header;
    //header = (MMHeader*)data_array;
    //printf("Magic: %.*s\n", 4, header->magic);
    //printf("Version: %lu\n", header->version);
    //printf("Header Size: %lu\n", header->header_size);
    //printf("File Size: %lu\n", header->file_size);

    //printf("%zu\n", offsetof(MMHeader, magic));
    //printf("%zu\n", offsetof(MMHeader, version));
    //printf("%zu\n", offsetof(MMHeader, header_size));
    //printf("%zu\n", offsetof(MMHeader, file_size));

    free(data_array);
    fclose(cfl.file);
    return 0;
}
