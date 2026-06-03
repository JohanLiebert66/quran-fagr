# -*- coding: utf-8 -*-
"""
note_types.py — MkDocs hook يُلصق «شارة نوع» (chip) على كل سطر ملاحظة
بناءً على موقع الصفحة، دون تعديل ملفات المصدر.

النوع يُستنتج من مكان الملاحظة:
    verses/*           → تأمل   (reflection)
    fajr/أسئلة…        → سؤال   (question)
    fajr/…لغوية        → لغة    (linguistic)
    fajr/…بلاغية       → بلاغة  (linguistic)
    fajr/…فقهية        → فقه    (research)
    fajr/تجويد         → تجويد  (research)

الشارة عنصر <span> سطري يُحقن قبل سطر الملاحظة (*التاريخ · … *)؛
تنسيقها في stylesheets/extra.css (الأصناف note-type--*).

يُسجَّل في mkdocs.yml تحت:
    hooks:
      - scripts/hooks/note_types.py
"""
from __future__ import annotations

import re

# (مُطابِق جزئي في المسار) -> (نص الشارة، صنف اللون)
RULES: list[tuple[str, tuple[str, str]]] = [
    ("verses/", ("تأمل", "reflection")),
    ("أسئلة", ("سؤال", "question")),
    ("لغوية", ("لغة", "linguistic")),
    ("بلاغية", ("بلاغة", "linguistic")),
    ("فقهية", ("فقه", "research")),
    ("تجويد", ("تجويد", "research")),
]

# سطر ملاحظة = يبدأ بـ * ثم تاريخ YYYY-MM-DD
NOTE_LINE_RE = re.compile(r"^(\s*)(\*\s*\d{4}-\d{2}-\d{2}\b.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _classify(src_path: str) -> tuple[str, str] | None:
    p = src_path.replace("\\", "/")
    for needle, result in RULES:
        if needle in p:
            return result
    return None


def on_page_markdown(markdown: str, *, page, config, files) -> str:
    kind = _classify(page.file.src_path)
    if kind is None:
        return markdown

    label, css = kind
    chip = f'<span class="note-type note-type--{css}">{label}</span>'

    out: list[str] = []
    in_fence = False
    in_comment = False
    for line in markdown.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if "-->" in line:
                in_comment = False
            out.append(line)
            continue
        if not in_fence:
            m = NOTE_LINE_RE.match(line)
            if m:
                out.append(f"{m.group(1)}{chip}{m.group(2)}")
                continue
        out.append(line)
    return "\n".join(out)
