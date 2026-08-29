# Copyright (c) 2025, CIF3
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

try:
    from PIL import Image
except ImportError:
    Image = None

from Tlog import TLog

log = TLog("thumbnail_cache")

WEBP_QUALITY = 75

DEFAULT_WORKERS = 4


def ensure_thumbnail(
    src_path: str,
    dst_path: str,
    size: int = 240,
    quality: int = WEBP_QUALITY,
) -> bool:
    if Image is None:
        log.error("PIL 未安装, 缩略图生成不可用")
        return False

    if not src_path or not os.path.exists(src_path):
        return False

    try:
        src_mtime = os.path.getmtime(src_path)
        if os.path.exists(dst_path) and os.path.getmtime(dst_path) >= src_mtime:
            return True
    except OSError:
        pass

    try:
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    except OSError as e:
        log.error(f"创建缩略图目录失败: {dst_path} - {e}")
        return False

    try:
        with Image.open(src_path) as im:
            im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
            im.thumbnail((size, size), Image.Resampling.LANCZOS)
            tmp_path = dst_path + ".tmp"
            im.save(tmp_path, "WEBP", quality=quality, method=4)
            os.replace(tmp_path, dst_path)
        try:
            os.utime(dst_path, (src_mtime, src_mtime))
        except OSError:
            pass
        return True
    except Exception as e:
        log.error(f"缩略图生成失败: {src_path} -> {dst_path} - {e}")
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        return False


def _ensure_one(item: tuple) -> tuple:
    item_id, src_path, thumb_dir, size, html_root = item
    dst_name = f"{item_id}_{size}.webp"
    dst_abs = os.path.join(thumb_dir, dst_name)
    if ensure_thumbnail(src_path, dst_abs, size=size):
        rel = os.path.relpath(dst_abs, html_root).replace("\\", "/")
        return (item_id, rel)
    return (item_id, "")


def ensure_thumbnails_batch(
    items: Iterable,
    thumb_dir: str,
    html_root: str,
    size: int = 240,
    workers: int = DEFAULT_WORKERS,
) -> dict:
    if Image is None:
        return {}

    try:
        os.makedirs(thumb_dir, exist_ok=True)
    except OSError as e:
        log.error(f"创建缩略图目录失败: {thumb_dir} - {e}")
        return {}

    tasks = [(item_id, src_path, thumb_dir, size, html_root) for item_id, src_path in items]
    if not tasks:
        return {}

    result: dict = {}
    if workers <= 1 or len(tasks) == 1:
        for t in tasks:
            item_id, rel = _ensure_one(t)
            result[item_id] = rel
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_ensure_one, t): t[0] for t in tasks}
            for fut in as_completed(futures):
                item_id, rel = fut.result()
                result[item_id] = rel
    return result


def clear_thumbnail_cache(thumb_dir: str) -> int:
    if not os.path.isdir(thumb_dir):
        return 0
    count = 0
    try:
        for name in os.listdir(thumb_dir):
            path = os.path.join(thumb_dir, name)
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    count += 1
                elif os.path.isdir(path):
                    removed = sum(1 for _ in _rmtree_files(path))
                    count += removed
            except OSError as e:
                log.error(f"删除失败: {path} - {e}")
    except OSError as e:
        log.error(f"列出缩略图目录失败: {thumb_dir} - {e}")
    return count


def _rmtree_files(root: str) -> Iterable[str]:
    for dirpath, _dirs, files in os.walk(root, topdown=False):
        for fn in files:
            p = os.path.join(dirpath, fn)
            try:
                os.remove(p)
                yield p
            except OSError:
                pass
        try:
            os.rmdir(dirpath)
        except OSError:
            pass
