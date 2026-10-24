# -*- coding: utf-8 -*-
"""
download_tafsirs.py — تنزيل ودمج كتب التفاسير الكاملة من مستودع spa5k/tafsir_api
محلياً بصيغة JSON نظيفة وسريعة داخل مجلد data/tafsir/
"""
import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_TAFSIR_DIR = PROJECT_ROOT / "data" / "tafsir"
DATA_TAFSIR_DIR.mkdir(parents=True, exist_ok=True)

EDITIONS = {
    "saadi": {
        "slug": "ar-tafseer-al-saddi",
        "name": "تفسير السعدي (تيسير الكريم الرحمن)",
        "author": "عبد الرحمن بن ناصر السعدي",
    },
    "tabari": {
        "slug": "ar-tafsir-al-tabari",
        "name": "تفسير الطبري (جامع البيان)",
        "author": "محمد بن جرير الطبري",
    },
    "wasit": {
        "slug": "ar-tafsir-al-wasit",
        "name": "التفسير الوسيط",
        "author": "محمد سيد طنطاوي",
    },
    "tanweer": {
        "slug": "ar-tafseer-tahrir-al-tanwir",
        "name": "التحرير والتنوير",
        "author": "محمد الطاهر بن عاشور",
    },
    "ibnkathir": {
        "slug": "ar-tafsir-ibn-kathir",
        "name": "تفسير ابن كثير (تفسير القرآن العظيم)",
        "author": "إسماعيل بن كثير",
    },
}

def clean_html(raw_html: str) -> str:
    clean = re.sub(r"<[^>]+>", "", raw_html)
    clean = clean.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    clean = clean.replace("&nbsp;", " ")
    return clean.strip()

def download_surah(slug: str, surah: int) -> tuple[int, list[dict] | None]:
    url = f"https://raw.githubusercontent.com/spa5k/tafsir_api/main/tafsir/{slug}/{surah}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "quran-fagr-downloader/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return surah, data
        except Exception:
            time.sleep(1)
    return surah, None

def download_and_consolidate(key: str) -> bool:
    info = EDITIONS[key]
    slug = info["slug"]
    name = info["name"]
    out_file = DATA_TAFSIR_DIR / f"{key}.json"

    print(f"[*] جاري تنزيل {name} ({slug})...")
    consolidated: dict[str, str] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_surah, slug, s): s for s in range(1, 115)}
        for future in concurrent.futures.as_completed(futures):
            surah, data = future.result()
            if data:
                for item in data:
                    ayah = item.get("ayah")
                    text = clean_html(item.get("text", ""))
                    if ayah is not None and text:
                        consolidated[f"{surah}:{ayah}"] = text

    if len(consolidated) < 6000:
        print(f"[!] تحذير: عدد الآيات المسترجعة لـ {key} هو {len(consolidated)} (أقل من المتوقع).")
    
    out_file.write_text(json.dumps(consolidated, ensure_ascii=False, indent=2), encoding="utf-8")
    file_size_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"[✓] تم حفظ {name} في {out_file.name} ({len(consolidated)} آية، {file_size_mb:.2f} MB)")
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    keys = [target] if target in EDITIONS else list(EDITIONS.keys())
    for k in keys:
        download_and_consolidate(k)
