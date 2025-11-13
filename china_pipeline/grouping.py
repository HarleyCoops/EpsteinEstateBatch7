#!/usr/bin/env python3
"""
Deterministic letter grouping without narrative or envelope detection.

Core idea:
- Extract OCR for every image first (German), preserving the base filename.
- Sort images by capture time (EXIF DateTimeOriginal), fallback to file mtime.
- Create groups by simple, auditable rules:
  - Start a new group when the time gap between pages exceeds a threshold, OR
  - The lexical similarity between adjacent pages is below a threshold.
- Allow manual overrides via a simple breakpoint file when needed.

Outputs are consumed by the strict pipeline to assemble per-letter files.
"""
from __future__ import annotations

import os
import re
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ExifTags
import unicodedata


@dataclass
class Page:
    image_path: str
    base: str  # stem without extension
    german_txt_path: str
    timestamp: Optional[datetime]
    text: str


def _read_exif_datetime(path: str) -> Optional[datetime]:
    try:
        with Image.open(path) as img:
            exif = getattr(img, "_getexif", lambda: None)()
            if not exif:
                return None
            tagmap = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
            for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                v = tagmap.get(key)
                if isinstance(v, str):
                    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
                        try:
                            return datetime.strptime(v, fmt)
                        except Exception:
                            pass
        return None
    except Exception:
        return None


def _file_mtime_datetime(path: str) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(os.path.getmtime(path))
    except Exception:
        return None


def _is_word_char(ch: str) -> bool:
    # Treat any Unicode letter or number as token content
    cat = unicodedata.category(ch)
    return cat and cat[0] in ("L", "N")


def _tokenize(text: str) -> List[str]:
    # Unicode-aware tokenizer without regex \p escapes
    tokens: List[str] = []
    buf: List[str] = []
    for ch in text:
        if _is_word_char(ch):
            buf.append(ch)
        else:
            if buf:
                tokens.append("".join(buf).casefold())
                buf.clear()
    if buf:
        tokens.append("".join(buf).casefold())
    return tokens


def jaccard_similarity(a: str, b: str) -> float:
    ta, tb = set(_tokenize(a)), set(_tokenize(b))
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def build_pages(
    image_paths: Sequence[str],
    german_text_by_base: Dict[str, str],
    german_path_by_base: Dict[str, str],
) -> List[Page]:
    pages: List[Page] = []
    for p in image_paths:
        base = os.path.splitext(os.path.basename(p))[0]
        ts = _read_exif_datetime(p) or _file_mtime_datetime(p)
        text = german_text_by_base.get(base, "")
        pages.append(Page(
            image_path=p,
            base=base,
            german_txt_path=german_path_by_base.get(base, ""),
            timestamp=ts,
            text=text,
        ))
    # Sort by timestamp then by name for stability
    pages.sort(key=lambda pg: ((pg.timestamp or datetime.min), pg.base))
    return pages


def _time_gap_seconds(prev: Optional[datetime], cur: Optional[datetime]) -> Optional[float]:
    if prev is None or cur is None:
        return None
    return (cur - prev).total_seconds()


def propose_breakpoints(
    pages: Sequence[Page],
    time_gap_threshold: int = 180,
    sim_threshold: float = 0.08,
) -> List[int]:
    """
    Return indices i where a break is proposed between pages[i-1] and pages[i].
    """
    breaks: List[int] = []
    prev_ts: Optional[datetime] = None
    prev_text: Optional[str] = None
    for i, pg in enumerate(pages):
        if i == 0:
            prev_ts, prev_text = pg.timestamp, pg.text
            continue
        gap = _time_gap_seconds(prev_ts, pg.timestamp)
        sim = jaccard_similarity(prev_text or "", pg.text or "")
        if (gap is not None and gap > time_gap_threshold) or sim < sim_threshold:
            breaks.append(i)
        prev_ts, prev_text = pg.timestamp, pg.text
    return breaks


def apply_overrides(
    breaks: List[int],
    pages: Sequence[Page],
    overrides_path: Optional[str],
) -> List[int]:
    if not overrides_path or not os.path.exists(overrides_path):
        return breaks
    try:
        with open(overrides_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Supported schema:
        # { "break_after": ["BASE1", "BASE2"], "force_group": {"BASE": "L0003", ...} }
        forced_after = set(data.get("break_after", []))
        name_to_index = {pg.base: i for i, pg in enumerate(pages)}
        for base in forced_after:
            idx = name_to_index.get(base)
            if idx is not None and idx + 1 <= len(pages) - 1:
                if (idx + 1) not in breaks:
                    breaks.append(idx + 1)
        breaks.sort()
    except Exception:
        # If overrides fail to parse, ignore silently to keep pipeline robust
        pass
    return breaks


def group_pages(
    pages: Sequence[Page],
    breaks: Sequence[int],
) -> List[dict]:
    groups: List[dict] = []
    start = 0
    gid = 1
    for b in list(sorted(set(breaks))) + [len(pages)]:
        if b <= start:
            continue
        group_pages = pages[start:b]
        group_id = f"L{gid:04d}"
        groups.append({
            "id": group_id,
            "pages": [
                {
                    "image_path": pg.image_path,
                    "base": pg.base,
                    "german_txt_path": pg.german_txt_path,
                    "timestamp": pg.timestamp.isoformat() if pg.timestamp else None,
                }
                for pg in group_pages
            ],
        })
        gid += 1
        start = b
    return groups


__all__ = [
    "Page",
    "build_pages",
    "propose_breakpoints",
    "apply_overrides",
    "group_pages",
    "jaccard_similarity",
]
