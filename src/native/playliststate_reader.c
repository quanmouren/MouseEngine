/* Copyright (c) 2026, CIF3
 * SPDX-License-Identifier: BSD-3-Clause

 * 用于解析 Wallpaper Engine playliststate.bin 当前多显示器播放列表。
 *
 * 公共 API：
 *   char* we_get_current_ids_json(const char* wallpaper_engine_root);
 *   void  we_free_string(char* value);
 *
 * 输入示例：
 *   d:/application/steam/steamapps/common/wallpaper_engine
 *
 * 该函数读取：
 *   <wallpaper_engine_root>/bin/playliststate.bin
 *
 * 返回值：
 *   一个由 malloc 分配的 JSON 数组字符串，按解析出的 MonitorN 索引排序：
 *   ["300948573","345656434"]
 */

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#define WE_EXPORT __declspec(dllexport)
#else
#define WE_EXPORT
#endif

#define WORKSHOP_ID "431960"
#define MIN_PRINTABLE_STRING 4

typedef struct MonitorCurrent {
    int monitor_index;
    char id[64];
    int has_id;
} MonitorCurrent;

static int is_slash(char ch) {
    return ch == '/' || ch == '\\';
}

static char *dup_json_error(const char *message) {
    size_t needed = strlen(message) + 16;
    char *out = (char *)malloc(needed);
    if (!out) {
        return NULL;
    }
    snprintf(out, needed, "{\"error\":\"%s\"}", message);
    return out;
}

static char *join_playliststate_path(const char *root) {
    const char *suffix = "bin/playliststate.bin";
    size_t root_len;
    size_t needed;
    char *path;

    if (!root || !root[0]) {
        return NULL;
    }

    root_len = strlen(root);
    while (root_len > 0 && (root[root_len - 1] == '"' || root[root_len - 1] == '\'')) {
        root_len--;
    }
    while (root_len > 0 && isspace((unsigned char)root[root_len - 1])) {
        root_len--;
    }

    needed = root_len + 1 + strlen(suffix) + 1;
    path = (char *)malloc(needed);
    if (!path) {
        return NULL;
    }

    memcpy(path, root, root_len);
    path[root_len] = '\0';
    if (root_len > 0 && !is_slash(path[root_len - 1])) {
        strcat(path, "/");
    }
    strcat(path, suffix);
    return path;
}

static unsigned char *read_file_bytes(const char *path, size_t *size_out) {
    FILE *file;
    long file_size;
    unsigned char *data;

    *size_out = 0;
    file = fopen(path, "rb");
    if (!file) {
        return NULL;
    }
    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return NULL;
    }
    file_size = ftell(file);
    if (file_size <= 0) {
        fclose(file);
        return NULL;
    }
    rewind(file);

    data = (unsigned char *)malloc((size_t)file_size);
    if (!data) {
        fclose(file);
        return NULL;
    }
    if (fread(data, 1, (size_t)file_size, file) != (size_t)file_size) {
        free(data);
        fclose(file);
        return NULL;
    }
    fclose(file);
    *size_out = (size_t)file_size;
    return data;
}

static int parse_monitor_index(const char *text) {
    int index = 0;
    int i = 7; /* strlen("Monitor") */

    if (strncmp(text, "Monitor", 7) != 0) {
        return -1;
    }
    if (!isdigit((unsigned char)text[i])) {
        return -1;
    }
    while (isdigit((unsigned char)text[i])) {
        index = index * 10 + (text[i] - '0');
        i++;
    }
    return index;
}

static int extract_workshop_id(const char *text, char *out, size_t out_size) {
    const char *cursor = text;
    const char *hit = NULL;
    size_t workshop_len = strlen(WORKSHOP_ID);
    size_t i = 0;

    while ((cursor = strstr(cursor, WORKSHOP_ID)) != NULL) {
        char before = cursor == text ? '/' : cursor[-1];
        char after = cursor[workshop_len];
        if (is_slash(before) && is_slash(after)) {
            hit = cursor + workshop_len + 1;
            break;
        }
        cursor += workshop_len;
    }

    if (!hit) {
        return 0;
    }

    while (isdigit((unsigned char)hit[i]) && i + 1 < out_size) {
        out[i] = hit[i];
        i++;
    }
    out[i] = '\0';
    return i > 0;
}

static MonitorCurrent *find_or_add_monitor(
    MonitorCurrent **items,
    size_t *count,
    size_t *capacity,
    int monitor_index
) {
    size_t i;
    MonitorCurrent *grown;

    for (i = 0; i < *count; i++) {
        if ((*items)[i].monitor_index == monitor_index) {
            return &(*items)[i];
        }
    }

    if (*count >= *capacity) {
        size_t new_capacity = *capacity == 0 ? 8 : (*capacity * 2);
        grown = (MonitorCurrent *)realloc(*items, new_capacity * sizeof(MonitorCurrent));
        if (!grown) {
            return NULL;
        }
        *items = grown;
        *capacity = new_capacity;
    }

    (*items)[*count].monitor_index = monitor_index;
    (*items)[*count].id[0] = '\0';
    (*items)[*count].has_id = 0;
    (*count)++;
    return &(*items)[*count - 1];
}

static int compare_monitor_current(const void *left, const void *right) {
    const MonitorCurrent *a = (const MonitorCurrent *)left;
    const MonitorCurrent *b = (const MonitorCurrent *)right;
    return a->monitor_index - b->monitor_index;
}

static char *build_json_array(MonitorCurrent *items, size_t count) {
    size_t i;
    size_t needed = 3;
    char *out;

    for (i = 0; i < count; i++) {
        if (items[i].has_id) {
            needed += strlen(items[i].id) + 4;
        }
    }

    out = (char *)malloc(needed);
    if (!out) {
        return NULL;
    }
    out[0] = '[';
    out[1] = '\0';

    for (i = 0; i < count; i++) {
        if (!items[i].has_id) {
            continue;
        }
        if (out[1] != '\0') {
            strcat(out, ",");
        }
        strcat(out, "\"");
        strcat(out, items[i].id);
        strcat(out, "\"");
    }
    strcat(out, "]");
    return out;
}

WE_EXPORT char *we_get_current_ids_json(const char *wallpaper_engine_root) {
    char *path = NULL;
    unsigned char *data = NULL;
    size_t data_size = 0;
    size_t pos = 0;
    int current_monitor = -1;
    MonitorCurrent *items = NULL;
    size_t count = 0;
    size_t capacity = 0;
    char *result = NULL;

    path = join_playliststate_path(wallpaper_engine_root);
    if (!path) {
        return dup_json_error("invalid_root");
    }

    data = read_file_bytes(path, &data_size);
    free(path);
    if (!data) {
        return dup_json_error("read_playliststate_failed");
    }

    while (pos < data_size) {
        if (data[pos] >= 32 && data[pos] <= 126) {
            size_t start = pos;
            size_t len;
            char *text;
            int monitor_index;

            while (pos < data_size && data[pos] >= 32 && data[pos] <= 126) {
                pos++;
            }
            len = pos - start;
            if (len < MIN_PRINTABLE_STRING) {
                continue;
            }

            text = (char *)malloc(len + 1);
            if (!text) {
                free(data);
                free(items);
                return dup_json_error("out_of_memory");
            }
            memcpy(text, data + start, len);
            text[len] = '\0';

            monitor_index = parse_monitor_index(text);
            if (monitor_index >= 0) {
                current_monitor = monitor_index;
                find_or_add_monitor(&items, &count, &capacity, monitor_index);
            } else if (current_monitor >= 0 && strstr(text, WORKSHOP_ID)) {
                MonitorCurrent *item = find_or_add_monitor(&items, &count, &capacity, current_monitor);
                if (item && !item->has_id && extract_workshop_id(text, item->id, sizeof(item->id))) {
                    item->has_id = 1;
                }
            }
            free(text);
        } else {
            pos++;
        }
    }

    free(data);
    qsort(items, count, sizeof(MonitorCurrent), compare_monitor_current);
    result = build_json_array(items, count);
    free(items);
    return result ? result : dup_json_error("out_of_memory");
}

WE_EXPORT void we_free_string(char *value) {
    free(value);
}

