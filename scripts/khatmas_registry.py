# -*- coding: utf-8 -*-
"""
khatmas_registry.py — مصدر واحد لقراءة سجل الختمات وتحديد ختمة تاريخٍ ما.

السجل جدول Markdown داخل surahs/khatmas/index.md بالأعمدة:
    | الرقم | الاسم | البدء | الانتهاء |

تستخدمه كلٌّ من build_khatmas.py (صفحات الختمات) وhook note_types.py
(شارة الختمة على سطر الملاحظة) حتى لا يتكرر منطق المطابقة.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# صف بيانات داخل جدول Markdown: |a|b|c|d|  (وليس صف الفواصل ---)
_ROW_RE = re.compile(r"^\s*\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|\s*$", re.MULTILINE)
_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _to_date(s: str) -> date | None:
    m = _DATE_RE.search(s)
    if not m:
        return None
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def parse_registry(registry_path: Path) -> list[dict]:
    """يُعيد قائمة ختمات مرتّبة بالرقم: {number, name, start, end(None للجارية)}."""
    if not registry_path.exists():
        return []
    text = registry_path.read_text(encoding="utf-8")
    out: list[dict] = []
    for m in _ROW_RE.finditer(text):
        a, b, c, d = (x.strip() for x in m.groups())
        if not a.isdigit():          # تجاهَل صف الرؤوس
            continue
        start = _to_date(c)
        if not start:
            continue
        out.append({
            "number": int(a),
            "name": b,
            "start": start,
            "end": _to_date(d),      # قد تكون None (ختمة جارية)
        })
    return sorted(out, key=lambda k: k["number"])


def in_range(d: date, k: dict, today: date | None = None) -> bool:
    today = today or date.today()
    if d < k["start"]:
        return False
    if k["end"] is None:
        return d <= today
    return d <= k["end"]


def khatma_for(d: date, khatmas: list[dict], today: date | None = None) -> dict | None:
    """أوّل ختمة يقع تاريخها ضمن مدّتها، أو None."""
    for k in khatmas:
        if in_range(d, k, today):
            return k
    return None
