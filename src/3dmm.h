typedef unsigned short u16;
typedef unsigned int   u32;
typedef signed int FilePointer;

typedef struct {
    u16 current;
    u16 oldest_backwards_compatible_version;
} DataVersion;

typedef struct {
    u32 magic;   // identifies this as a chunky file
    u32 created_by; // program that created this file
    DataVersion data_version;      // chunky file version
    short byte_order;       // byte order
    short written_by_os;      // which system wrote this

    off_t  end_of_file;          // logical end of file
    off_t  index;                // location of chunky index
    size_t index_size;             // size of chunky index
    off_t  free_space_map;       // location of free space map
    size_t size_of_free_space_map; // size of free space map (may be 0)
} ChunkyFilePointer;


typedef struct {
    FILE *file;
    ChunkyFilePointer cfp;
} ChunkFile;
