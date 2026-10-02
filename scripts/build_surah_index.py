# -*- coding: utf-8 -*-
"""
build_surah_index.py — يُولّد فهرسًا عكسيًا: لكل سورة وردت في الملاحظات،
قائمة الإدخالات التي تشير إليها مع روابط مباشرة للملاحظات (Anchors).

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
H3_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
ATTR_ID_RE = re.compile(r"\{:\s*#([^\s}]+)\s*\}")
AYAH_RE = re.compile(r"آية\s*(\d+)")
VERSES_FILE_RE = re.compile(r"^(\d{3}-[^.]+)\.md$")


def clean_text_content(text: str) -> str:
    """إزالة التعليقات وكتل الكود لتجنب فهرسة قوالب الإدخال والأمثلة."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return text


def main() -> None:
    # كل إدخال: (المسار النسبي للصفحة مع الـ anchor، عنوان الإدخال، تسمية المصدر، مرجع إضافي اختياري)
    by_surah: dict[str, list[tuple[str, str, str, str]]] = {}

    # ===== 1) فحص ملاحظات الفجر بحثًا عن روابط لصفحات السور =====
    if FAJR.exists():
        for page in sorted(FAJR.glob("*.md")):
            if page.name == "index.md":
                continue
            raw_text = page.read_text(encoding="utf-8")
            text = clean_text_content(raw_text)

            heads = [(m.start(), m.group(1).strip()) for m in HEAD_RE.finditer(text)]
            for m in LINK_RE.finditer(text):
                link_text = m.group(1).strip()
                surah_slug = m.group(2)
                preceding = [h for h in heads if h[0] < m.start()]
                if not preceding:
                    continue
                raw_head = preceding[-1][1]

                # استخراج المعرف الصريح {: #id } إن وُجد
                id_m = ATTR_ID_RE.search(raw_head)
                anchor = id_m.group(1) if id_m else ""
                clean_title = ATTR_ID_RE.sub("", raw_head).strip()

                src_rel = f"fajr/{page.stem}.md#{anchor}" if anchor else f"fajr/{page.stem}.md"
                by_surah.setdefault(surah_slug, []).append((
                    src_rel,
                    clean_title,
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
            raw_text = page.read_text(encoding="utf-8")
            text = clean_text_content(raw_text)

            heads = list(HEAD_RE.finditer(text))
            for i, h in enumerate(heads):
                raw = h.group(1).strip()
                sec_end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
                sec_text = text[h.end():sec_end]

                id_m = ATTR_ID_RE.search(raw)
                ayah_m = AYAH_RE.search(raw)

                anchor = ""
                if id_m:
                    anchor = id_m.group(1)
                    raw = ATTR_ID_RE.sub("", raw).strip()
                elif ayah_m:
                    anchor = ayah_m.group(1)

                h3_m = H3_RE.search(sec_text)
                title = raw
                if ayah_m:
                    ayah_num = ayah_m.group(1)
                    # إزالة مطلع "آية N:" إذا كان موجوداً لاستخلاص النص الفرعي
                    cleaned_raw = re.sub(r"^آية\s*\d+\s*[:\-—]?\s*", "", raw).strip()
                    if cleaned_raw:
                        title = f"آية {ayah_num}: {cleaned_raw}"
                    elif h3_m:
                        sub = h3_m.group(1).strip()
                        sub = ATTR_ID_RE.sub("", sub).strip()
                        title = f"آية {ayah_num}: {sub}"
                    else:
                        title = f"آية {ayah_num}"

                src_rel = f"verses/{page.stem}.md#{anchor}" if anchor else f"verses/{page.stem}.md"
                by_surah.setdefault(surah_slug, []).append((
                    src_rel,
                    title,
                    "تدبر آية",
                    "",
                ))

    sorted_keys = sorted(by_surah.keys(), key=lambda s: int(s.split("-", 1)[0]))
    total = sum(len(v) for v in by_surah.values())

    lines = [
        "# فهرس الملاحظات حسب السورة\n",
        "تجميعٌ تلقائي: لكل سورة وردت في **مشاركات حلقة الفجر** أو في **تدبر الآيات**، "
        "قائمة الملاحظات التي تخصّها مع روابط مباشرة لكل آية وفائدة.\n",
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
