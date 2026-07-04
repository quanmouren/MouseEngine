/* Copyright (c) 2026, CIF3
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Wallpaper Engine 显示器映射辅助库。
 *
 * 公共 API：
 *   char *we_get_monitor_current_ids_json(const char *wallpaper_engine_root);
 *   char *we_get_monitor_current_id_json(const char *wallpaper_engine_root, const char *monitor_key);
 *   char *we_get_monitor_details_json(const char *wallpaper_engine_root);
 *   void  we_free_string(char *value);
 *
 * 返回的字符串是 malloc 分配的 UTF-8 JSON，使用完毕后必须调用 we_free_string() 释放。
 */

#define UNICODE
#define _UNICODE

#include <windows.h>
#include <ctype.h>
#include <stdint.h>
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
#define MAX_MONITOR_KEY 32
#define MAX_ID_LEN 64
#define MAX_PATH_TEXT 1024
#define MAX_SOURCE_TEXT 64
#define MAX_DEVICE_TEXT 256
#define MAX_DISPLAY_TEXT 256

typedef struct StringBuilder {
    char *data;
    size_t len;
    size_t cap;
} StringBuilder;

typedef struct MonitorPath {
    char key[MAX_MONITOR_KEY];
    char path[MAX_PATH_TEXT];
    char id[MAX_ID_LEN];
} MonitorPath;

typedef struct MonitorPathList {
    MonitorPath *items;
    size_t count;
    size_t cap;
} MonitorPathList;

typedef struct MonitorMapEntry {
    char key[MAX_PATH_TEXT];
    int location;
} MonitorMapEntry;

typedef struct MonitorMapList {
    MonitorMapEntry *items;
    size_t count;
    size_t cap;
} MonitorMapList;

typedef struct WindowsMonitor {
    uint64_t hmonitor;
    char device_name[MAX_DEVICE_TEXT];
    char device_id[MAX_PATH_TEXT];
    char monitor_name[MAX_DISPLAY_TEXT];
    int left;
    int top;
    int right;
    int bottom;
    int is_primary;
    char we_key[MAX_MONITOR_KEY];
    char mapping_source[MAX_SOURCE_TEXT];
} WindowsMonitor;

typedef struct WindowsMonitorList {
    WindowsMonitor *items;
    size_t count;
    size_t cap;
} WindowsMonitorList;

typedef struct ConfigState {
    MonitorPathList selected;
    MonitorMapList monitor_map;
    char last_selected_monitor[MAX_MONITOR_KEY];
} ConfigState;

typedef struct MappingContext {
    ConfigState config;
    MonitorPathList playlist_raw;
    MonitorPathList playlist;
    WindowsMonitorList windows;
} MappingContext;

static int sb_init(StringBuilder *sb)
{
    sb->cap = 256;
    sb->len = 0;
    sb->data = (char *)malloc(sb->cap);
    if (!sb->data) {
        return 0;
    }
    sb->data[0] = '\0';
    return 1;
}

static int sb_reserve(StringBuilder *sb, size_t extra)
{
    size_t needed = sb->len + extra + 1;
    char *grown;
    size_t new_cap;

    if (needed <= sb->cap) {
        return 1;
    }
    new_cap = sb->cap;
    while (new_cap < needed) {
        new_cap *= 2;
    }
    grown = (char *)realloc(sb->data, new_cap);
    if (!grown) {
        return 0;
    }
    sb->data = grown;
    sb->cap = new_cap;
    return 1;
}

static int sb_append_len(StringBuilder *sb, const char *text, size_t len)
{
    if (!sb_reserve(sb, len)) {
        return 0;
    }
    memcpy(sb->data + sb->len, text, len);
    sb->len += len;
    sb->data[sb->len] = '\0';
    return 1;
}

static int sb_append(StringBuilder *sb, const char *text)
{
    return sb_append_len(sb, text, strlen(text));
}

static int sb_append_char(StringBuilder *sb, char ch)
{
    if (!sb_reserve(sb, 1)) {
        return 0;
    }
    sb->data[sb->len++] = ch;
    sb->data[sb->len] = '\0';
    return 1;
}

static int sb_append_json_string(StringBuilder *sb, const char *text)
{
    const unsigned char *p = (const unsigned char *)(text ? text : "");
    if (!sb_append_char(sb, '"')) {
        return 0;
    }
    while (*p) {
        char buf[8];
        if (*p == '"' || *p == '\\') {
            if (!sb_append_char(sb, '\\') || !sb_append_char(sb, (char)*p)) {
                return 0;
            }
        } else if (*p == '\n') {
            if (!sb_append(sb, "\\n")) {
                return 0;
            }
        } else if (*p == '\r') {
            if (!sb_append(sb, "\\r")) {
                return 0;
            }
        } else if (*p == '\t') {
            if (!sb_append(sb, "\\t")) {
                return 0;
            }
        } else if (*p < 32) {
            snprintf(buf, sizeof(buf), "\\u%04x", (unsigned int)*p);
            if (!sb_append(sb, buf)) {
                return 0;
            }
        } else if (!sb_append_char(sb, (char)*p)) {
            return 0;
        }
        p++;
    }
    return sb_append_char(sb, '"');
}

static char *sb_take(StringBuilder *sb)
{
    char *out = sb->data;
    sb->data = NULL;
    sb->len = 0;
    sb->cap = 0;
    return out;
}

static char *dup_string(const char *text)
{
    size_t len;
    char *copy;

    if (!text) {
        return NULL;
    }
    len = strlen(text);
    copy = (char *)malloc(len + 1);
    if (!copy) {
        return NULL;
    }
    memcpy(copy, text, len + 1);
    return copy;
}

static char *dup_json_error(const char *message)
{
    StringBuilder sb;
    if (!sb_init(&sb)) {
        return NULL;
    }
    if (!sb_append(&sb, "{\"error\":") ||
        !sb_append_json_string(&sb, message ? message : "unknown") ||
        !sb_append_char(&sb, '}')) {
        free(sb.data);
        return NULL;
    }
    return sb_take(&sb);
}

static int is_slash(char ch)
{
    return ch == '/' || ch == '\\';
}

static int ends_with_ascii_ci(const char *text, const char *suffix)
{
    size_t text_len;
    size_t suffix_len;
    size_t i;

    if (!text || !suffix) {
        return 0;
    }
    text_len = strlen(text);
    suffix_len = strlen(suffix);
    if (text_len < suffix_len) {
        return 0;
    }
    for (i = 0; i < suffix_len; i++) {
        char a = text[text_len - suffix_len + i];
        char b = suffix[i];
        if (tolower((unsigned char)a) != tolower((unsigned char)b)) {
            return 0;
        }
    }
    return 1;
}

static char *join_root_path(const char *root, const char *suffix)
{
    size_t root_len;
    size_t needed;
    char *path;

    if (!root || !root[0] || !suffix) {
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

static char *config_path_from_root(const char *root)
{
    if (ends_with_ascii_ci(root, "config.json")) {
        return dup_string(root);
    }
    return join_root_path(root, "config.json");
}

static char *playlist_path_from_root(const char *root)
{
    return join_root_path(root, "bin/playliststate.bin");
}

static unsigned char *read_file_bytes(const char *path, size_t *size_out)
{
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

    data = (unsigned char *)malloc((size_t)file_size + 1);
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
    data[file_size] = '\0';
    *size_out = (size_t)file_size;
    return data;
}

static void safe_copy(char *dst, size_t dst_size, const char *src)
{
    if (!dst || dst_size == 0) {
        return;
    }
    if (!src) {
        dst[0] = '\0';
        return;
    }
    strncpy(dst, src, dst_size - 1);
    dst[dst_size - 1] = '\0';
}

static int wide_to_utf8(const wchar_t *src, char *dst, size_t dst_size)
{
    int written;
    if (!dst || dst_size == 0) {
        return 0;
    }
    dst[0] = '\0';
    if (!src || !src[0]) {
        return 1;
    }
    written = WideCharToMultiByte(
        CP_UTF8,
        0,
        src,
        -1,
        dst,
        (int)dst_size,
        NULL,
        NULL
    );
    if (written <= 0) {
        dst[0] = '\0';
        return 0;
    }
    dst[dst_size - 1] = '\0';
    return 1;
}

static int monitor_path_reserve(MonitorPathList *list, size_t extra)
{
    MonitorPath *grown;
    size_t new_cap;

    if (list->count + extra <= list->cap) {
        return 1;
    }
    new_cap = list->cap ? list->cap * 2 : 8;
    while (new_cap < list->count + extra) {
        new_cap *= 2;
    }
    grown = (MonitorPath *)realloc(list->items, new_cap * sizeof(MonitorPath));
    if (!grown) {
        return 0;
    }
    list->items = grown;
    list->cap = new_cap;
    return 1;
}

static MonitorPath *find_monitor_path(MonitorPathList *list, const char *key)
{
    size_t i;
    for (i = 0; i < list->count; i++) {
        if (strcmp(list->items[i].key, key) == 0) {
            return &list->items[i];
        }
    }
    return NULL;
}

static int add_or_update_monitor_path(MonitorPathList *list, const char *key, const char *path)
{
    MonitorPath *item = find_monitor_path(list, key);
    if (!item) {
        if (!monitor_path_reserve(list, 1)) {
            return 0;
        }
        item = &list->items[list->count++];
        ZeroMemory(item, sizeof(*item));
        safe_copy(item->key, sizeof(item->key), key);
    }
    safe_copy(item->path, sizeof(item->path), path ? path : "");
    return 1;
}

static void free_monitor_path_list(MonitorPathList *list)
{
    free(list->items);
    list->items = NULL;
    list->count = 0;
    list->cap = 0;
}

static int monitor_map_reserve(MonitorMapList *list, size_t extra)
{
    MonitorMapEntry *grown;
    size_t new_cap;

    if (list->count + extra <= list->cap) {
        return 1;
    }
    new_cap = list->cap ? list->cap * 2 : 16;
    while (new_cap < list->count + extra) {
        new_cap *= 2;
    }
    grown = (MonitorMapEntry *)realloc(list->items, new_cap * sizeof(MonitorMapEntry));
    if (!grown) {
        return 0;
    }
    list->items = grown;
    list->cap = new_cap;
    return 1;
}

static int add_monitor_map_entry(MonitorMapList *list, const char *key, int location)
{
    char *p;

    if (!monitor_map_reserve(list, 1)) {
        return 0;
    }
    safe_copy(list->items[list->count].key, sizeof(list->items[list->count].key), key);
    p = list->items[list->count].key;
    while (*p) {
        if (*p == '\\') {
            *p = '/';
        }
        p++;
    }
    list->items[list->count].location = location;
    list->count++;
    return 1;
}

static void free_monitor_map_list(MonitorMapList *list)
{
    free(list->items);
    list->items = NULL;
    list->count = 0;
    list->cap = 0;
}

static int windows_monitor_reserve(WindowsMonitorList *list, size_t extra)
{
    WindowsMonitor *grown;
    size_t new_cap;

    if (list->count + extra <= list->cap) {
        return 1;
    }
    new_cap = list->cap ? list->cap * 2 : 4;
    while (new_cap < list->count + extra) {
        new_cap *= 2;
    }
    grown = (WindowsMonitor *)realloc(list->items, new_cap * sizeof(WindowsMonitor));
    if (!grown) {
        return 0;
    }
    list->items = grown;
    list->cap = new_cap;
    return 1;
}

static void free_windows_monitor_list(WindowsMonitorList *list)
{
    free(list->items);
    list->items = NULL;
    list->count = 0;
    list->cap = 0;
}

static int parse_monitor_key(const char *text, char *out, size_t out_size)
{
    size_t i = 7;
    if (!text || strncmp(text, "Monitor", 7) != 0 || !isdigit((unsigned char)text[7])) {
        return 0;
    }
    if (out_size < 9) {
        return 0;
    }
    memcpy(out, "Monitor", 7);
    while (isdigit((unsigned char)text[i]) && i + 1 < out_size) {
        out[i] = text[i];
        i++;
    }
    out[i] = '\0';
    return i > 7;
}

static int monitor_key_index(const char *key)
{
    int index = 0;
    const char *p = key;
    if (!key || strncmp(key, "Monitor", 7) != 0) {
        return 999999;
    }
    p += 7;
    if (!isdigit((unsigned char)*p)) {
        return 999999;
    }
    while (isdigit((unsigned char)*p)) {
        index = index * 10 + (*p - '0');
        p++;
    }
    return index;
}

static int compare_monitor_path_key(const void *left, const void *right)
{
    const MonitorPath *a = (const MonitorPath *)left;
    const MonitorPath *b = (const MonitorPath *)right;
    int ai = monitor_key_index(a->key);
    int bi = monitor_key_index(b->key);
    if (ai != bi) {
        return ai - bi;
    }
    return strcmp(a->key, b->key);
}

static int compare_monitor_key_text(const void *left, const void *right)
{
    const char *a = (const char *)left;
    const char *b = (const char *)right;
    int ai = monitor_key_index(a);
    int bi = monitor_key_index(b);
    if (ai != bi) {
        return ai - bi;
    }
    return strcmp(a, b);
}

static int key_exists_in_paths(const MonitorPathList *list, const char *key)
{
    size_t i;
    for (i = 0; i < list->count; i++) {
        if (strcmp(list->items[i].key, key) == 0) {
            return 1;
        }
    }
    return 0;
}

static int key_exists_in_monitor_map_locations(const MonitorMapList *list, const char *key)
{
    size_t i;
    char monitor_key[MAX_MONITOR_KEY];
    for (i = 0; i < list->count; i++) {
        snprintf(monitor_key, sizeof(monitor_key), "Monitor%d", list->items[i].location);
        if (strcmp(monitor_key, key) == 0) {
            return 1;
        }
    }
    return 0;
}

static int known_monitor_key(const ConfigState *config, const char *key)
{
    return key_exists_in_paths(&config->selected, key) ||
        key_exists_in_monitor_map_locations(&config->monitor_map, key);
}

static void canonical_monitor_key(
    const ConfigState *config,
    const char *raw_key,
    char *out,
    size_t out_size
)
{
    size_t i;
    size_t best_len = 0;
    char candidate[MAX_MONITOR_KEY];

    safe_copy(out, out_size, raw_key);
    if (known_monitor_key(config, raw_key)) {
        return;
    }
    for (i = 0; i < config->selected.count; i++) {
        const char *known = config->selected.items[i].key;
        size_t len = strlen(known);
        if (len > best_len && strncmp(raw_key, known, len) == 0) {
            best_len = len;
            safe_copy(candidate, sizeof(candidate), known);
            safe_copy(out, out_size, candidate);
        }
    }
    for (i = 0; i < config->monitor_map.count; i++) {
        snprintf(candidate, sizeof(candidate), "Monitor%d", config->monitor_map.items[i].location);
        if (!known_monitor_key(config, candidate)) {
            continue;
        }
        if (strlen(candidate) > best_len && strncmp(raw_key, candidate, strlen(candidate)) == 0) {
            best_len = strlen(candidate);
            safe_copy(out, out_size, candidate);
        }
    }
}

static int extract_workshop_id(const char *text, char *out, size_t out_size)
{
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

static const char *skip_ws(const char *p)
{
    while (p && *p && isspace((unsigned char)*p)) {
        p++;
    }
    return p;
}

static const char *json_find_string_end(const char *p)
{
    if (!p || *p != '"') {
        return NULL;
    }
    p++;
    while (*p) {
        if (*p == '\\' && p[1]) {
            p += 2;
            continue;
        }
        if (*p == '"') {
            return p;
        }
        p++;
    }
    return NULL;
}

static int json_copy_string_at(const char *quote, char *out, size_t out_size)
{
    const char *p;
    size_t len = 0;
    if (!quote || *quote != '"' || !out || out_size == 0) {
        return 0;
    }
    p = quote + 1;
    while (*p) {
        if (*p == '\\' && p[1]) {
            p++;
            if (len + 1 < out_size) {
                out[len++] = *p;
            }
            p++;
            continue;
        }
        if (*p == '"') {
            out[len] = '\0';
            return 1;
        }
        if (len + 1 < out_size) {
            out[len++] = *p;
        }
        p++;
    }
    out[len] = '\0';
    return 0;
}

static const char *json_find_key(const char *start, const char *end, const char *key)
{
    StringBuilder pattern;
    const char *p;
    char *needle;

    if (!start || !key || !sb_init(&pattern)) {
        return NULL;
    }
    if (!sb_append_char(&pattern, '"') || !sb_append(&pattern, key) || !sb_append_char(&pattern, '"')) {
        free(pattern.data);
        return NULL;
    }
    needle = sb_take(&pattern);
    p = start;
    while ((p = strstr(p, needle)) != NULL) {
        if (end && p >= end) {
            break;
        }
        free(needle);
        return p;
    }
    free(needle);
    return NULL;
}

static const char *json_value_after_key(const char *start, const char *end, const char *key)
{
    const char *p = json_find_key(start, end, key);
    if (!p) {
        return NULL;
    }
    p = json_find_string_end(p);
    if (!p) {
        return NULL;
    }
    p = skip_ws(p + 1);
    if (*p != ':') {
        return NULL;
    }
    return skip_ws(p + 1);
}

static const char *json_matching_brace(const char *open)
{
    int depth = 0;
    int in_string = 0;
    const char *p = open;
    if (!open || *open != '{') {
        return NULL;
    }
    while (*p) {
        if (in_string) {
            if (*p == '\\' && p[1]) {
                p += 2;
                continue;
            }
            if (*p == '"') {
                in_string = 0;
            }
        } else {
            if (*p == '"') {
                in_string = 1;
            } else if (*p == '{') {
                depth++;
            } else if (*p == '}') {
                depth--;
                if (depth == 0) {
                    return p;
                }
            }
        }
        p++;
    }
    return NULL;
}

static int json_read_int_value(const char *object_start, const char *object_end, const char *key, int *out)
{
    const char *p = json_value_after_key(object_start, object_end, key);
    if (!p || !out) {
        return 0;
    }
    *out = atoi(p);
    return 1;
}

static int json_read_string_value(
    const char *object_start,
    const char *object_end,
    const char *key,
    char *out,
    size_t out_size
)
{
    const char *p = json_value_after_key(object_start, object_end, key);
    if (!p || *p != '"') {
        return 0;
    }
    return json_copy_string_at(p, out, out_size);
}

static void parse_selected_wallpapers(const char *json, ConfigState *config)
{
    const char *wallpaper_config = json_value_after_key(json, NULL, "wallpaperconfig");
    const char *wallpaper_config_end;
    const char *selected;
    const char *selected_end;
    const char *p;

    if (!wallpaper_config || *wallpaper_config != '{') {
        return;
    }
    wallpaper_config_end = json_matching_brace(wallpaper_config);
    selected = json_value_after_key(wallpaper_config, wallpaper_config_end, "selectedwallpapers");
    if (!selected || *selected != '{') {
        return;
    }
    selected_end = json_matching_brace(selected);
    p = selected;
    while ((p = strstr(p, "\"Monitor")) != NULL && p < selected_end) {
        char key[MAX_MONITOR_KEY];
        const char *key_end;
        const char *value;
        const char *entry_end;
        char file[MAX_PATH_TEXT];

        key_end = json_find_string_end(p);
        if (!key_end || !parse_monitor_key(p + 1, key, sizeof(key))) {
            p++;
            continue;
        }
        value = skip_ws(key_end + 1);
        if (*value != ':') {
            p = key_end + 1;
            continue;
        }
        value = skip_ws(value + 1);
        if (*value != '{') {
            p = key_end + 1;
            continue;
        }
        entry_end = json_matching_brace(value);
        if (entry_end && json_read_string_value(value, entry_end, "file", file, sizeof(file))) {
            add_or_update_monitor_path(&config->selected, key, file);
        } else {
            add_or_update_monitor_path(&config->selected, key, "");
        }
        p = entry_end ? entry_end + 1 : key_end + 1;
    }
}

static void parse_monitor_map(const char *json, ConfigState *config)
{
    const char *monitor_map = json_value_after_key(json, NULL, "monitormap");
    const char *monitor_map_end;
    const char *p;

    if (!monitor_map || *monitor_map != '{') {
        return;
    }
    monitor_map_end = json_matching_brace(monitor_map);
    p = monitor_map + 1;
    while (p && p < monitor_map_end) {
        char key[MAX_PATH_TEXT];
        const char *key_start;
        const char *key_end;
        const char *value;
        const char *entry_end;
        int location;

        p = skip_ws(p);
        if (*p == ',') {
            p++;
            continue;
        }
        if (*p != '"') {
            p++;
            continue;
        }
        key_start = p;
        key_end = json_find_string_end(key_start);
        if (!key_end || !json_copy_string_at(key_start, key, sizeof(key))) {
            break;
        }
        value = skip_ws(key_end + 1);
        if (*value != ':') {
            p = key_end + 1;
            continue;
        }
        value = skip_ws(value + 1);
        if (*value != '{') {
            p = key_end + 1;
            continue;
        }
        entry_end = json_matching_brace(value);
        if (entry_end && json_read_int_value(value, entry_end, "location", &location)) {
            add_monitor_map_entry(&config->monitor_map, key, location);
        }
        p = entry_end ? entry_end + 1 : key_end + 1;
    }
}

static void parse_last_selected_monitor(const char *json, ConfigState *config)
{
    json_read_string_value(
        json,
        NULL,
        "lastselectedmonitor",
        config->last_selected_monitor,
        sizeof(config->last_selected_monitor)
    );
}

static void parse_config_json(const char *json, ConfigState *config)
{
    parse_selected_wallpapers(json, config);
    parse_monitor_map(json, config);
    parse_last_selected_monitor(json, config);
}

static void parse_playliststate_bytes(const unsigned char *data, size_t data_size, MonitorPathList *out)
{
    size_t pos = 0;
    char current_key[MAX_MONITOR_KEY] = "";

    while (pos < data_size) {
        if (data[pos] >= 32 && data[pos] <= 126) {
            size_t start = pos;
            size_t len;
            char text[MAX_PATH_TEXT];
            char monitor_key[MAX_MONITOR_KEY];
            char id[MAX_ID_LEN];

            while (pos < data_size && data[pos] >= 32 && data[pos] <= 126) {
                pos++;
            }
            len = pos - start;
            if (len < MIN_PRINTABLE_STRING) {
                continue;
            }
            if (len >= sizeof(text)) {
                len = sizeof(text) - 1;
            }
            memcpy(text, data + start, len);
            text[len] = '\0';

            if (parse_monitor_key(text, monitor_key, sizeof(monitor_key))) {
                safe_copy(current_key, sizeof(current_key), monitor_key);
                continue;
            }
            if (current_key[0] && strstr(text, WORKSHOP_ID) && extract_workshop_id(text, id, sizeof(id))) {
                if (!find_monitor_path(out, current_key)) {
                    add_or_update_monitor_path(out, current_key, text);
                }
            }
        } else {
            pos++;
        }
    }
}

static void fill_ids_for_paths(MonitorPathList *list)
{
    size_t i;
    for (i = 0; i < list->count; i++) {
        extract_workshop_id(list->items[i].path, list->items[i].id, sizeof(list->items[i].id));
    }
}

static int normalize_playlist_keys(const ConfigState *config, const MonitorPathList *raw, MonitorPathList *normalized)
{
    MonitorPathList sorted = {0};
    size_t i;

    if (!monitor_path_reserve(&sorted, raw->count)) {
        return 0;
    }
    memcpy(sorted.items, raw->items, raw->count * sizeof(MonitorPath));
    sorted.count = raw->count;
    qsort(sorted.items, sorted.count, sizeof(MonitorPath), compare_monitor_path_key);

    for (i = 0; i < sorted.count; i++) {
        char key[MAX_MONITOR_KEY];
        MonitorPath *existing;
        canonical_monitor_key(config, sorted.items[i].key, key, sizeof(key));
        existing = find_monitor_path(normalized, key);
        if (!existing || strcmp(sorted.items[i].key, key) == 0) {
            add_or_update_monitor_path(normalized, key, sorted.items[i].path);
        }
    }
    free_monitor_path_list(&sorted);
    fill_ids_for_paths(normalized);
    return 1;
}

static int compare_windows_monitor(const void *left, const void *right)
{
    const WindowsMonitor *a = (const WindowsMonitor *)left;
    const WindowsMonitor *b = (const WindowsMonitor *)right;
    if (a->top != b->top) {
        return a->top - b->top;
    }
    if (a->left != b->left) {
        return a->left - b->left;
    }
    return strcmp(a->device_name, b->device_name);
}

static BOOL CALLBACK enum_monitor_proc(HMONITOR hmonitor, HDC hdc, LPRECT rect, LPARAM data)
{
    WindowsMonitorList *list = (WindowsMonitorList *)data;
    MONITORINFOEXW info;
    DISPLAY_DEVICEW device;
    WindowsMonitor *item;

    (void)hdc;
    (void)rect;

    if (!windows_monitor_reserve(list, 1)) {
        return FALSE;
    }
    item = &list->items[list->count];
    ZeroMemory(item, sizeof(*item));

    ZeroMemory(&info, sizeof(info));
    info.cbSize = sizeof(info);
    if (!GetMonitorInfoW(hmonitor, (MONITORINFO *)&info)) {
        return TRUE;
    }
    item->hmonitor = (uint64_t)(uintptr_t)hmonitor;
    item->left = info.rcMonitor.left;
    item->top = info.rcMonitor.top;
    item->right = info.rcMonitor.right;
    item->bottom = info.rcMonitor.bottom;
    item->is_primary = (info.dwFlags & MONITORINFOF_PRIMARY) ? 1 : 0;
    wide_to_utf8(info.szDevice, item->device_name, sizeof(item->device_name));

    ZeroMemory(&device, sizeof(device));
    device.cb = sizeof(device);
    if (EnumDisplayDevicesW(info.szDevice, 0, &device, 0)) {
        wide_to_utf8(device.DeviceString, item->monitor_name, sizeof(item->monitor_name));
        wide_to_utf8(device.DeviceID, item->device_id, sizeof(item->device_id));
    }
    list->count++;
    return TRUE;
}

static int enumerate_windows_monitors(WindowsMonitorList *list)
{
    if (!EnumDisplayMonitors(NULL, NULL, enum_monitor_proc, (LPARAM)list)) {
        return 0;
    }
    qsort(list->items, list->count, sizeof(WindowsMonitor), compare_windows_monitor);
    return 1;
}

static void slash_normalize(char *text)
{
    while (text && *text) {
        if (*text == '\\') {
            *text = '/';
        }
        text++;
    }
}

static int find_location_for_monitor(const ConfigState *config, const WindowsMonitor *monitor, int *location_out)
{
    size_t i;
    char hardware_key[MAX_PATH_TEXT];
    char display_key[MAX_DEVICE_TEXT];

    safe_copy(hardware_key, sizeof(hardware_key), monitor->device_id);
    slash_normalize(hardware_key);
    safe_copy(display_key, sizeof(display_key), monitor->device_name);
    slash_normalize(display_key);

    for (i = 0; i < config->monitor_map.count; i++) {
        if (hardware_key[0] && strcmp(config->monitor_map.items[i].key, hardware_key) == 0) {
            *location_out = config->monitor_map.items[i].location;
            return 1;
        }
    }
    for (i = 0; i < config->monitor_map.count; i++) {
        if (display_key[0] && strcmp(config->monitor_map.items[i].key, display_key) == 0) {
            *location_out = config->monitor_map.items[i].location;
            return 1;
        }
    }
    return 0;
}

static int key_in_known_array(char keys[][MAX_MONITOR_KEY], size_t count, const char *key)
{
    size_t i;
    for (i = 0; i < count; i++) {
        if (strcmp(keys[i], key) == 0) {
            return 1;
        }
    }
    return 0;
}

static size_t collect_known_we_keys(const MappingContext *ctx, char keys[][MAX_MONITOR_KEY], size_t max_keys)
{
    size_t count = 0;
    size_t i;
    char key[MAX_MONITOR_KEY];

    for (i = 0; i < ctx->config.selected.count && count < max_keys; i++) {
        if (!key_in_known_array(keys, count, ctx->config.selected.items[i].key)) {
            safe_copy(keys[count++], MAX_MONITOR_KEY, ctx->config.selected.items[i].key);
        }
    }
    for (i = 0; i < ctx->playlist.count && count < max_keys; i++) {
        if (!key_in_known_array(keys, count, ctx->playlist.items[i].key)) {
            safe_copy(keys[count++], MAX_MONITOR_KEY, ctx->playlist.items[i].key);
        }
    }
    for (i = 0; i < ctx->config.monitor_map.count && count < max_keys; i++) {
        snprintf(key, sizeof(key), "Monitor%d", ctx->config.monitor_map.items[i].location);
        if (!key_in_known_array(keys, count, key)) {
            safe_copy(keys[count++], MAX_MONITOR_KEY, key);
        }
    }
    qsort(keys, count, MAX_MONITOR_KEY, compare_monitor_key_text);
    return count;
}

static int location_claimed(int *claimed, size_t claimed_count, int location)
{
    size_t i;
    for (i = 0; i < claimed_count; i++) {
        if (claimed[i] == location) {
            return 1;
        }
    }
    return 0;
}

static void map_windows_to_we(MappingContext *ctx)
{
    char known_keys[128][MAX_MONITOR_KEY];
    size_t known_count = collect_known_we_keys(ctx, known_keys, 128);
    int claimed[128];
    size_t claimed_count = 0;
    size_t i;

    if (ctx->windows.count == 1 &&
        ctx->config.last_selected_monitor[0] &&
        key_in_known_array(known_keys, known_count, ctx->config.last_selected_monitor)) {
        safe_copy(ctx->windows.items[0].we_key, sizeof(ctx->windows.items[0].we_key), ctx->config.last_selected_monitor);
        safe_copy(ctx->windows.items[0].mapping_source, sizeof(ctx->windows.items[0].mapping_source), "browser-lastselected-single-active");
        return;
    }
    if (ctx->windows.count == 1 && ctx->playlist.count == 1) {
        safe_copy(ctx->windows.items[0].we_key, sizeof(ctx->windows.items[0].we_key), ctx->playlist.items[0].key);
        safe_copy(ctx->windows.items[0].mapping_source, sizeof(ctx->windows.items[0].mapping_source), "playliststate-single-active");
        return;
    }

    for (i = 0; i < ctx->windows.count; i++) {
        int location;
        char key[MAX_MONITOR_KEY];
        if (find_location_for_monitor(&ctx->config, &ctx->windows.items[i], &location)) {
            snprintf(key, sizeof(key), "Monitor%d", location);
            if (key_in_known_array(known_keys, known_count, key) &&
                !location_claimed(claimed, claimed_count, location)) {
                safe_copy(ctx->windows.items[i].we_key, sizeof(ctx->windows.items[i].we_key), key);
                safe_copy(ctx->windows.items[i].mapping_source, sizeof(ctx->windows.items[i].mapping_source), "monitormap-exact");
                claimed[claimed_count++] = location;
            }
        }
    }

    for (i = 0; i < ctx->windows.count; i++) {
        size_t j;
        if (ctx->windows.items[i].we_key[0]) {
            continue;
        }
        for (j = 0; j < known_count; j++) {
            int loc = monitor_key_index(known_keys[j]);
            if (!location_claimed(claimed, claimed_count, loc)) {
                safe_copy(ctx->windows.items[i].we_key, sizeof(ctx->windows.items[i].we_key), known_keys[j]);
                safe_copy(ctx->windows.items[i].mapping_source, sizeof(ctx->windows.items[i].mapping_source), "geometry-fallback");
                claimed[claimed_count++] = loc;
                break;
            }
        }
    }
}

static const MonitorPath *find_const_path(const MonitorPathList *list, const char *key)
{
    size_t i;
    for (i = 0; i < list->count; i++) {
        if (strcmp(list->items[i].key, key) == 0) {
            return &list->items[i];
        }
    }
    return NULL;
}

static void get_id_for_key(
    const MappingContext *ctx,
    const char *key,
    const char **current_id,
    const char **playlist_id,
    const char **config_id,
    const char **source
)
{
    const MonitorPath *playlist = find_const_path(&ctx->playlist, key);
    const MonitorPath *config = find_const_path(&ctx->config.selected, key);

    *playlist_id = playlist ? playlist->id : "";
    *config_id = config ? config->id : "";
    if (*playlist_id && (*playlist_id)[0]) {
        *current_id = *playlist_id;
        *source = "playliststate.bin";
    } else if (*config_id && (*config_id)[0]) {
        *current_id = *config_id;
        *source = "config.json";
    } else {
        *current_id = "";
        *source = "fallback";
    }
}

static void free_context(MappingContext *ctx)
{
    free_monitor_path_list(&ctx->config.selected);
    free_monitor_map_list(&ctx->config.monitor_map);
    free_monitor_path_list(&ctx->playlist_raw);
    free_monitor_path_list(&ctx->playlist);
    free_windows_monitor_list(&ctx->windows);
}

static int load_context(const char *root, MappingContext *ctx)
{
    char *config_path;
    char *playlist_path;
    unsigned char *config_bytes;
    unsigned char *playlist_bytes;
    size_t config_size;
    size_t playlist_size;

    ZeroMemory(ctx, sizeof(*ctx));
    config_path = config_path_from_root(root);
    playlist_path = playlist_path_from_root(root);
    if (!config_path || !playlist_path) {
        free(config_path);
        free(playlist_path);
        return 0;
    }

    config_bytes = read_file_bytes(config_path, &config_size);
    playlist_bytes = read_file_bytes(playlist_path, &playlist_size);
    free(config_path);
    free(playlist_path);
    if (!config_bytes || !playlist_bytes) {
        free(config_bytes);
        free(playlist_bytes);
        return 0;
    }

    parse_config_json((const char *)config_bytes, &ctx->config);
    parse_playliststate_bytes(playlist_bytes, playlist_size, &ctx->playlist_raw);
    fill_ids_for_paths(&ctx->config.selected);
    fill_ids_for_paths(&ctx->playlist_raw);
    normalize_playlist_keys(&ctx->config, &ctx->playlist_raw, &ctx->playlist);
    enumerate_windows_monitors(&ctx->windows);
    map_windows_to_we(ctx);

    free(config_bytes);
    free(playlist_bytes);
    (void)config_size;
    return 1;
}

static char *build_current_ids_json(const MappingContext *ctx)
{
    StringBuilder sb;
    char keys[128][MAX_MONITOR_KEY];
    size_t count = collect_known_we_keys(ctx, keys, 128);
    size_t i;
    int first = 1;

    if (!sb_init(&sb) || !sb_append_char(&sb, '{')) {
        return NULL;
    }
    for (i = 0; i < count; i++) {
        const char *current_id;
        const char *playlist_id;
        const char *config_id;
        const char *source;
        get_id_for_key(ctx, keys[i], &current_id, &playlist_id, &config_id, &source);
        if (!current_id || !current_id[0]) {
            continue;
        }
        if (!first && !sb_append_char(&sb, ',')) {
            free(sb.data);
            return NULL;
        }
        first = 0;
        if (!sb_append_json_string(&sb, keys[i]) ||
            !sb_append_char(&sb, ':') ||
            !sb_append_json_string(&sb, current_id)) {
            free(sb.data);
            return NULL;
        }
    }
    if (!sb_append_char(&sb, '}')) {
        free(sb.data);
        return NULL;
    }
    return sb_take(&sb);
}

static char *build_current_id_json(const MappingContext *ctx, const char *requested_key)
{
    StringBuilder sb;
    char key[MAX_MONITOR_KEY];
    const char *current_id;
    const char *playlist_id;
    const char *config_id;
    const char *source;

    if (!requested_key || !parse_monitor_key(requested_key, key, sizeof(key))) {
        return dup_json_error("invalid_monitor_key");
    }
    canonical_monitor_key(&ctx->config, key, key, sizeof(key));
    get_id_for_key(ctx, key, &current_id, &playlist_id, &config_id, &source);

    if (!sb_init(&sb) ||
        !sb_append(&sb, "{\"we_monitor\":") ||
        !sb_append_json_string(&sb, key) ||
        !sb_append(&sb, ",\"current_id\":") ||
        !sb_append_json_string(&sb, current_id) ||
        !sb_append(&sb, ",\"playliststate_id\":") ||
        !sb_append_json_string(&sb, playlist_id) ||
        !sb_append(&sb, ",\"config_id\":") ||
        !sb_append_json_string(&sb, config_id) ||
        !sb_append(&sb, ",\"wallpaper_source\":") ||
        !sb_append_json_string(&sb, source) ||
        !sb_append_char(&sb, '}')) {
        free(sb.data);
        return NULL;
    }
    return sb_take(&sb);
}

static char *build_details_json(const MappingContext *ctx)
{
    StringBuilder sb;
    size_t i;

    if (!sb_init(&sb) || !sb_append(&sb, "{\"items\":[")) {
        return NULL;
    }
    for (i = 0; i < ctx->windows.count; i++) {
        const WindowsMonitor *monitor = &ctx->windows.items[i];
        const char *current_id;
        const char *playlist_id;
        const char *config_id;
        const char *source;
        char index_buf[64];

        get_id_for_key(ctx, monitor->we_key, &current_id, &playlist_id, &config_id, &source);
        if (i > 0 && !sb_append_char(&sb, ',')) {
            free(sb.data);
            return NULL;
        }
        snprintf(index_buf, sizeof(index_buf), "%u", (unsigned int)i);
        if (!sb_append_char(&sb, '{') ||
            !sb_append(&sb, "\"index\":") ||
            !sb_append(&sb, index_buf)) {
            free(sb.data);
            return NULL;
        }
        snprintf(index_buf, sizeof(index_buf), "%llu", (unsigned long long)monitor->hmonitor);
        if (!sb_append(&sb, ",\"hmon\":") ||
            !sb_append(&sb, index_buf) ||
            !sb_append(&sb, ",\"is_primary\":") ||
            !sb_append(&sb, monitor->is_primary ? "true" : "false") ||
            !sb_append(&sb, ",\"device_name\":") ||
            !sb_append_json_string(&sb, monitor->device_name) ||
            !sb_append(&sb, ",\"monitor_name\":") ||
            !sb_append_json_string(&sb, monitor->monitor_name) ||
            !sb_append(&sb, ",\"device_id\":") ||
            !sb_append_json_string(&sb, monitor->device_id) ||
            !sb_append(&sb, ",\"rect\":[")) {
            free(sb.data);
            return NULL;
        }
        snprintf(index_buf, sizeof(index_buf), "%d,%d,%d,%d",
            monitor->left, monitor->top, monitor->right, monitor->bottom);
        if (!sb_append(&sb, index_buf) ||
            !sb_append(&sb, "],\"we_monitor\":") ||
            !sb_append_json_string(&sb, monitor->we_key) ||
            !sb_append(&sb, ",\"mapping_source\":") ||
            !sb_append_json_string(&sb, monitor->mapping_source) ||
            !sb_append(&sb, ",\"wallpaper_source\":") ||
            !sb_append_json_string(&sb, source) ||
            !sb_append(&sb, ",\"current_id\":") ||
            !sb_append_json_string(&sb, current_id) ||
            !sb_append(&sb, ",\"config_id\":") ||
            !sb_append_json_string(&sb, config_id) ||
            !sb_append(&sb, ",\"playliststate_id\":") ||
            !sb_append_json_string(&sb, playlist_id) ||
            !sb_append_char(&sb, '}')) {
            free(sb.data);
            return NULL;
        }
    }
    if (!sb_append(&sb, "]}")) {
        free(sb.data);
        return NULL;
    }
    return sb_take(&sb);
}

WE_EXPORT char *we_get_monitor_current_ids_json(const char *wallpaper_engine_root)
{
    MappingContext ctx;
    char *result;

    if (!wallpaper_engine_root || !wallpaper_engine_root[0]) {
        return dup_json_error("invalid_root");
    }
    if (!load_context(wallpaper_engine_root, &ctx)) {
        return dup_json_error("load_context_failed");
    }
    result = build_current_ids_json(&ctx);
    free_context(&ctx);
    return result ? result : dup_json_error("out_of_memory");
}

WE_EXPORT char *we_get_monitor_current_id_json(const char *wallpaper_engine_root, const char *monitor_key)
{
    MappingContext ctx;
    char *result;

    if (!wallpaper_engine_root || !wallpaper_engine_root[0]) {
        return dup_json_error("invalid_root");
    }
    if (!load_context(wallpaper_engine_root, &ctx)) {
        return dup_json_error("load_context_failed");
    }
    result = build_current_id_json(&ctx, monitor_key);
    free_context(&ctx);
    return result ? result : dup_json_error("out_of_memory");
}

WE_EXPORT char *we_get_monitor_details_json(const char *wallpaper_engine_root)
{
    MappingContext ctx;
    char *result;

    if (!wallpaper_engine_root || !wallpaper_engine_root[0]) {
        return dup_json_error("invalid_root");
    }
    if (!load_context(wallpaper_engine_root, &ctx)) {
        return dup_json_error("load_context_failed");
    }
    result = build_details_json(&ctx);
    free_context(&ctx);
    return result ? result : dup_json_error("out_of_memory");
}

WE_EXPORT void we_free_string(char *value)
{
    free(value);
}
