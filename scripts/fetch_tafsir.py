# -*- coding: utf-8 -*-
"""
fetch_tafsir.py — جلب نصوص التفاسير الأصلية والمحققة مباشرة من API موثوق (Quran.com)
لكل آية، لاستخراج نص التفسير الحرفي دون الاعتماد على ذاكرة النموذج فقط.

التفاسير المعتمدة:
  • 91: تفسير السعدي (تيسير الكريم الرحمن)
  • 15: تفسير الطبري (جامع البيان)
  • 93: التفسير الوسيط (لطنطاوي)
  • 14: تفسير ابن كثير (تفسير القرآن العظيم)
  • 90: تفسير القرطبي (الجامع لأحكام القرآن)
  • 94: تفسير البغوي (معالم التنزيل)

الاستخدام:
  python scripts/fetch_tafsir.py 10 90
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

TAFSIR_MAP = {
    "saadi": (91, "تفسير السعدي (تيسير الكريم الرحمن)"),
    "tabari": (15, "تفسير الطبري (جامع البيان)"),
    "wasit": (93, "التفسير الوسيط (لطنطاوي)"),
    "ibnkathir": (14, "تفسير ابن كثير (تفسير القرآن العظيم)"),
    "qurtubi": (90, "تفسير القرطبي (الجامع لأحكام القرآن)"),
    "baghawi": (94, "تفسير البغوي (معالم التنزيل)"),
}

def clean_html(raw_html: str) -> str:
    clean = re.sub(r"<[^>]+>", "", raw_html)
    clean = clean.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    clean = clean.replace("&nbsp;", " ")
    return clean.strip()

def get_tafsir(surah: int, ayah: int, tafsir_id: int) -> str | None:
    url = f"https://api.quran.com/api/v4/tafsirs/{tafsir_id}/by_ayah/{surah}:{ayah}"
    req = urllib.request.Request(url, headers={"User-Agent": "quran-fagr-researcher/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_text = data.get("tafsir", {}).get("text", "")
            if raw_text:
                return clean_html(raw_text)
    except Exception as e:
        print(f"Error fetching tafsir {tafsir_id} for {surah}:{ayah}: {e}", file=sys.stderr)
    return None

def fetch_all(surah: int, ayah: int, keys: list[str] | None = None) -> dict[str, str]:
    target_keys = keys or ["saadi", "tabari", "wasit", "ibnkathir"]
    results = {}
    for k in target_keys:
        if k in TAFSIR_MAP:
            tid, name = TAFSIR_MAP[k]
            text = get_tafsir(surah, ayah, tid)
            if text:
                results[name] = text
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="جلب نصوص التفاسير الأصلية لآية محددة.")
    parser.add_argument("surah", type=int, help="رقم السورة")
    parser.add_argument("ayah", type=int, help="رقم الآية")
    parser.add_argument("--tafsir", "-t", choices=list(TAFSIR_MAP.keys()), help="تفسير محدد فقط")
    args = parser.parse_args()

    keys = [args.tafsir] if args.tafsir else ["saadi", "tabari", "wasit", "ibnkathir"]
    res = fetch_all(args.surah, args.ayah, keys)
    for name, content in res.items():
        print("=" * 60)
        print(f"📖 {name} — [{args.surah}:{args.ayah}]")
        print("=" * 60)
        print(content)
        print("\n")
