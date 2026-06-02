# -*- coding: utf-8 -*-
"""
note.py — يُولِّد سطر الـ metadata لملاحظة جاهزًا للنسخ والإلصاق.

الاستخدام:
    python note.py 6 93 لغة                  # سورة الأنعام، آية 93، وسم #لغة
    python note.py 2 255 توحيد آية-الكرسي    # عدة وسوم
    python note.py 6 93                       # بلا وسوم
    python note.py لغة بلاغة                  # بلا سورة (لملاحظة عامة في فجر/)
    python note.py 6 93 لغة | clip            # نسخ مباشر للحافظة (Windows)

الناتج مثل:
    *2026-06-02 · #لغة · [الأنعام:93](../quran/006-الأنعام.md)*
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from surahs import BY_NUMBER


def slug(name: str) -> str:
    return name.strip().replace(" ", "-")


def main() -> None:
    args = sys.argv[1:]
    surah: int | None = None
    ayah: int | None = None
    tags: list[str] = []
    for a in args:
        s = a.strip().lstrip("#")
        if s.isdigit():
            n = int(s)
            if surah is None and 1 <= n <= 114:
                surah = n
            elif ayah is None:
                ayah = n
            else:
                tags.append(s)
        else:
            tags.append(s)

    today = date.today().isoformat()
    parts: list[str] = [today]
    for t in tags:
        parts.append(f"#{t}")

    if surah is not None:
        name = BY_NUMBER.get(surah, "")
        if name:
            ref = f"{name}:{ayah}" if ayah is not None else name
            link = f"../quran/{surah:03d}-{slug(name)}.md"
            parts.append(f"[{ref}]({link})")

    print(f"*{' · '.join(parts)}*")


if __name__ == "__main__":
    main()
