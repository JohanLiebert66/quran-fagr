# -*- coding: utf-8 -*-
"""
note_types.py — MkDocs hook لتنسيق الملاحظات وقت البناء، دون تعديل المصدر.

يفعل أمرين:
  1) شارة نوع (chip) على كل سطر ملاحظة حسب موقع الصفحة:
        verses/*  → تأمل      fajr/…لغوية → لغة     fajr/…بلاغية → بلاغة
        fajr/…فقهية → فقه     fajr/تجويد → تجويد    fajr/أسئلة… → سؤال
  2) شارة الختمة (مثل «ختمة ١») مستنتَجة من تاريخ الملاحظة عبر سجل
     surahs/khatmas/index.md (نفس منطق build_khatmas).
  3) على صفحات الآيات (verses/) فقط: يلفّ كل ملاحظة في <div class="tl-note">
     ويُدرِج فاصل ختمة عند تغيّرها — ليرسم extra.css خطًّا زمنيًا رأسيًا.

يُسجَّل في mkdocs.yml تحت hooks:.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

# (مُطابِق جزئي في المسار) -> (نص الشارة، صنف اللون)
RULES: list[tuple[str, tuple[str, str]]] = [
    ("verses/", ("تأمل", "reflection")),
    ("أسئلة", ("سؤال", "question")),
    ("لغوية", ("لغة", "linguistic")),
    ("بلاغية", ("بلاغة", "linguistic")),
    ("فقهية", ("فقه", "research")),
    ("تجويد", ("تجويد", "research")),
]

H2_RE = re.compile(r"^##\s+\S")
NOTE_LINE_RE = re.compile(r"^(\s*)(\*\s*\d{4}-\d{2}-\d{2}\b.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

_KHATMAS: list[dict] = []   # سجل الختمات، يُحمَّل مرّة في on_config
_khatma_for = None          # دالة المطابقة من khatmas_registry


def on_config(config):
    """يحمّل سجل الختمات مرّة واحدة عند بدء البناء."""
    global _KHATMAS, _khatma_for
    scripts_dir = Path(__file__).resolve().parent.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from khatmas_registry import parse_registry, khatma_for
    _khatma_for = khatma_for
    registry = Path(config["docs_dir"]) / "khatmas" / "index.md"
    _KHATMAS = parse_registry(registry)
    return config


def _classify(src_path: str) -> tuple[str, str] | None:
    p = src_path.replace("\\", "/")
    for needle, result in RULES:
        if needle in p:
            return result
    return None


def _ar(n: int) -> str:
    return str(n).translate(_AR_DIGITS)


def _date_of(meta_text: str) -> date | None:
    m = DATE_RE.search(meta_text)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def on_page_markdown(markdown: str, *, page, config, files) -> str:
    kind = _classify(page.file.src_path)
    if kind is None:
        return markdown
    label, css = kind
    chip = f'<span class="note-type note-type--{css}">{label}</span>'
    is_verses = "verses/" in page.file.src_path.replace("\\", "/")

    lines = markdown.split("\n")
    n = len(lines)

    # تمييز الأسطر مع تجاهل كتل الكود وتعليقات HTML
    h2 = [False] * n
    meta = [False] * n
    in_fence = in_comment = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if H2_RE.match(line):
            h2[i] = True
        elif NOTE_LINE_RE.match(line):
            meta[i] = True

    # حقن الشارة (+ شارة الختمة) على أسطر الميتاداتا، وحفظ ختمة كل سطر
    meta_khatma: dict[int, dict | None] = {}
    for i in range(n):
        if not meta[i]:
            continue
        m = NOTE_LINE_RE.match(lines[i])
        d = _date_of(m.group(2))
        k = _khatma_for(d, _KHATMAS) if (d and _khatma_for) else None
        meta_khatma[i] = k
        badge = ""
        if k:
            badge = f'<span class="note-type note-type--khatma">ختمة {_ar(k["number"])}</span>'
        lines[i] = f'{m.group(1)}{chip}{badge}{m.group(2)}'

    if not is_verses:
        return "\n".join(lines)

    # صفحات الآيات: لفّ كل ملاحظة + فاصل ختمة عند التغيّر
    h2_idx = [i for i in range(n) if h2[i]]
    if not h2_idx:
        return "\n".join(lines)

    out: list[str] = list(lines[: h2_idx[0]])   # ما قبل أول عنوان ملاحظة
    prev_khatma: int | None = None
    for s, start in enumerate(h2_idx):
        end = h2_idx[s + 1] if s + 1 < len(h2_idx) else n
        section = lines[start:end]

        meta_idx = next((j for j in range(start, end) if meta[j]), None)
        if meta_idx is None:
            out.extend(section)          # قسم بلا ملاحظة — اتركه كما هو
            continue

        k = meta_khatma.get(meta_idx)
        if k is not None and k["number"] != prev_khatma:
            nm = re.sub(r"^ختمة\s+", "", k["name"]).strip()   # تفادي تكرار كلمة «ختمة»
            out += ["", f'<div class="tl-sep">ختمة {_ar(k["number"])} · {nm}</div>', ""]
            prev_khatma = k["number"]

        out.append(f'<div class="tl-note tl-note--{css}" markdown="1">')
        out.append("")
        out.extend(section)
        out.append("")
        out.append("</div>")
    return "\n".join(out)
