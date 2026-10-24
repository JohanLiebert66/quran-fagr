# -*- coding: utf-8 -*-
"""
tafsir_local.py — محرك استعلام التفسير المحلي وفائق السرعة
يقرأ التفسير مباشرة من ملفات JSON المحلية داخل data/tafsir/ في جزء من الثانية (Offline)،
وإذا لم يجد الكتاب محلياً، يستدعي fetch_tafsir.py لجلبها وحفظها تلقائياً.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_TAFSIR_DIR = PROJECT_ROOT / "data" / "tafsir"

BOOK_NAMES = {
    "saadi": "تفسير السعدي (تيسير الكريم الرحمن)",
    "tabari": "تفسير الطبري (جامع البيان)",
    "wasit": "التفسير الوسيط (لطنطاوي)",
    "tanweer": "التحرير والتنوير (ابن عاشور)",
    "ibnkathir": "تفسير ابن كثير (تفسير القرآن العظيم)",
    "qurtubi": "تفسير القرطبي (الجامع لأحكام القرآن)",
    "baghawi": "تفسير البغوي (معالم التنزيل)",
}

_CACHE: dict[str, dict[str, str]] = {}

def get_tafsir_text(surah: int, ayah: int, book: str = "saadi") -> str | None:
    json_file = DATA_TAFSIR_DIR / f"{book}.json"
    key = f"{surah}:{ayah}"

    if book not in _CACHE:
        if json_file.exists():
            try:
                _CACHE[book] = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[!] خطأ في قراءة ملف {json_file}: {e}", file=sys.stderr)
                _CACHE[book] = {}
        else:
            _CACHE[book] = {}

    if key in _CACHE[book]:
        return _CACHE[book][key]

    # إذا لم يوجد محلياً، الاستدعاء الاحتياطي عبر fetch_tafsir
    try:
        from fetch_tafsir import get_tafsir, TAFSIR_MAP
        if book in TAFSIR_MAP:
            tid, _ = TAFSIR_MAP[book]
            remote_text = get_tafsir(surah, ayah, tid)
            if remote_text:
                return remote_text
    except Exception:
        pass

    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="استعلام سريع عن تفسير آية من الكتب المحلية.")
    parser.add_argument("surah", type=int, help="رقم السورة")
    parser.add_argument("ayah", type=int, help="رقم الآية")
    parser.add_argument("--book", "-b", default="saadi", choices=list(BOOK_NAMES.keys()), help="اسم كتاب التفسير")
    args = parser.parse_args()

    text = get_tafsir_text(args.surah, args.ayah, args.book)
    name = BOOK_NAMES.get(args.book, args.book)
    if text:
        print("=" * 60)
        print(f"📖 {name} — [{args.surah}:{args.ayah}] (استرجاع محلي)")
        print("=" * 60)
        print(text)
    else:
        print(f"[!] لم يُعثر على تفسير لـ [{args.surah}:{args.ayah}] في {name}.")
