# -*- coding: utf-8 -*-
"""
build_surah_index.py — يُولّد فهرسًا عكسيًا: لكل سورة وردت في الملاحظات،
قائمة الإدخالات التي تشير إليها.

يجمع من مصدرين:
1. مشاركات حلقة الفجر (`surahs/fajr/*.md`):
   عبر روابط Markdown صريحة من نوع `[البقرة:255](../quran/002-البقرة.md)`.
2. تدبر الآيات (`surahs/verses/NNN-name.md`):
   كل ملف يخص سورته (يُستنتج من الاسم)، وكل عنوان H2 داخله = ملاحظة على آية.

النتيجة: `surahs/notes-by-surah.md`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT = Path(__file__).resolve().parent.parent
FAJR = PROJECT / "surahs" / "fajr"
VERSES = PROJECT / "surahs" / "verses"
OUT = PROJECT / "surahs" / "notes-by-surah.md"

LINK_RE = re.compile(r"\[([^\]]+)\]\(\.\./quran/(\d{3}-[^\)]+)\.md\)")
HEAD_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
VERSES_FILE_RE = re.compile(r"^(\d{3}-[^.]+)\.md$")


def main() -> None:
    # كل إدخال: (المسار النسبي للصفحة، عنوان الإدخال، تسمية المصدر، مرجع إضافي اختياري)
    by_surah: dict[str, list[tuple[str, str, str, str]]] = {}

    # ===== 1) فحص ملاحظات الفجر بحثًا عن روابط لصفحات السور =====
    if FAJR.exists():
        for page in sorted(FAJR.glob("*.md")):
            text = page.read_text(encoding="utf-8")
            heads = [(m.start(), m.group(1).strip()) for m in HEAD_RE.finditer(text)]
            for m in LINK_RE.finditer(text):
                link_text = m.group(1).strip()
                surah_slug = m.group(2)
                preceding = [h for h in heads if h[0] < m.start()]
                note_title = preceding[-1][1] if preceding else "(بدون عنوان)"
                by_surah.setdefault(surah_slug, []).append((
                    f"fajr/{page.stem}.md",
                    note_title,
                    page.stem,
                    link_text,
                ))

    # ===== 2) فحص تدبر الآيات (ملف لكل سورة، H2 لكل آية) =====
    if VERSES.exists():
        for page in sorted(VERSES.glob("*.md")):
            if page.name == "index.md":
                continue
            m = VERSES_FILE_RE.match(page.name)
            if not m:
                continue
            surah_slug = m.group(1)
            text = page.read_text(encoding="utf-8")
            for h in HEAD_RE.finditer(text):
                verse_title = h.group(1).strip()
                by_surah.setdefault(surah_slug, []).append((
                    f"verses/{page.stem}.md",
                    verse_title,
                    "تدبر آية",
                    "",
                ))

    sorted_keys = sorted(by_surah.keys(), key=lambda s: int(s.split("-", 1)[0]))
    total = sum(len(v) for v in by_surah.values())

    lines = [
        "# فهرس الملاحظات حسب السورة\n",
        "تجميعٌ تلقائي: لكل سورة وردت في **مشاركات حلقة الفجر** أو في **تدبر الآيات**، "
        "قائمة الملاحظات التي تخصّها.\n",
        "للإضافة: اكتب رابطًا مثل `[البقرة:255](../quran/002-البقرة.md)` في ملاحظة فجر، "
        "أو أنشئ/حدّث ملف `surahs/verses/NNN-name.md` وأضف عنوان `## آية N: ...`.\n",
    ]

    if not sorted_keys:
        lines.append("\n*لا توجد ملاحظات تربط بسور بعد.*")
    else:
        for key in sorted_keys:
            num = key.split("-", 1)[0].lstrip("0") or "0"
            name = key.split("-", 1)[1].replace("-", " ")
            lines.append(f"\n## [{num} — سورة {name}](quran/{key}.md)\n")
            for src_rel, title, label, ref in by_surah[key]:
                ref_part = f" (المرجع: **{ref}**)" if ref else ""
                lines.append(f"- [{title}]({src_rel}) — *{label}*{ref_part}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✓ {OUT.name} — {len(sorted_keys)} سورة، {total} ملاحظة")


if __name__ == "__main__":
    main()
