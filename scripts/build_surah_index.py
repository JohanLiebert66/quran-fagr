# -*- coding: utf-8 -*-
"""
build_surah_index.py — يُولّد فهرسًا عكسيًا: لكل سورة وردت في "مشاركات حلقة الفجر"،
قائمة الملاحظات التي تشير إليها (عبر رابط Markdown إلى صفحة السورة).

النتيجة: surahs/notes-by-surah.md — صفحة "فهرس حسب السورة" تظهر في الشريط الجانبي.

القاعدة التي يلتقطها السكربت:
    [البقرة:255](../quran/002-البقرة.md)

اكتب رقم الآية داخل نصّ الرابط (مثل `البقرة:255`) ليظهر بوضوح في الفهرس.
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
OUT = PROJECT / "surahs" / "notes-by-surah.md"

LINK_RE = re.compile(r"\[([^\]]+)\]\(\.\./quran/(\d{3}-[^\)]+)\.md\)")
HEAD_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def main() -> None:
    by_surah: dict[str, list[tuple[str, str, str]]] = {}
    for page in sorted(FAJR.glob("*.md")):
        text = page.read_text(encoding="utf-8")
        heads = [(m.start(), m.group(1).strip()) for m in HEAD_RE.finditer(text)]
        for m in LINK_RE.finditer(text):
            link_text = m.group(1).strip()
            surah_slug = m.group(2)
            preceding = [h for h in heads if h[0] < m.start()]
            note_title = preceding[-1][1] if preceding else "(بدون عنوان)"
            by_surah.setdefault(surah_slug, []).append(
                (page.stem, note_title, link_text)
            )

    sorted_keys = sorted(by_surah.keys(), key=lambda s: int(s.split("-", 1)[0]))
    total_notes = sum(len(v) for v in by_surah.values())

    lines = [
        "# فهرس الملاحظات حسب السورة\n",
        "تجميعٌ تلقائي: لكل سورة وردت في **مشاركات حلقة الفجر**، قائمة الملاحظات التي تشير إليها.\n",
        "للإضافة، اكتب داخل أي ملاحظة رابطًا بصيغة `[البقرة:255](../quran/002-البقرة.md)` "
        "وسيظهر هنا تلقائيًا عند إعادة بناء الموقع.\n",
    ]

    if not sorted_keys:
        lines.append("\n*لا توجد ملاحظات تربط بسور بعد.*")
    else:
        for key in sorted_keys:
            num = key.split("-", 1)[0].lstrip("0") or "0"
            name = key.split("-", 1)[1].replace("-", " ")
            lines.append(f"\n## [{num} — سورة {name}](quran/{key}.md)\n")
            for cat, title, link_text in by_surah[key]:
                lines.append(
                    f"- [{title}](fajr/{cat}.md) — *{cat}* "
                    f"(المرجع: **{link_text}**)"
                )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✓ {OUT.name} — {len(sorted_keys)} سورة، {total_notes} ملاحظة")


if __name__ == "__main__":
    main()
