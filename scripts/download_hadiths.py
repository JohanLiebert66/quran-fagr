# -*- coding: utf-8 -*-
"""
download_hadiths.py — تنزيل وحفظ نصوص صحيحي البخاري ومسلم الكاملة
محلياً بصيغة JSON داخل مجلد data/hadith/ للبحث الفوري دون الحاجة للإنترنت.
المصدر: مستودع fawazahmed0/hadith-api الموثق والمفهرس.
"""
from __future__ import annotations

import json
import ssl
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_HADITH_DIR = PROJECT_ROOT / "data" / "hadith"
DATA_HADITH_DIR.mkdir(parents=True, exist_ok=True)

COLLECTIONS = {
    "bukhari": {
        "name": "صحيح البخاري",
        "url": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-bukhari.min.json",
        "expected_min": 7000,
    },
    "muslim": {
        "name": "صحيح مسلم",
        "url": "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-muslim.min.json",
        "expected_min": 7000,
    },
}

def download_collection(key: str) -> bool:
    info = COLLECTIONS[key]
    out_file = DATA_HADITH_DIR / f"{key}.json"
    name = info["name"]
    url = info["url"]

    print(f"[*] جاري تنزيل {name} من {url}...")
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": "quran-fagr-hadith-downloader/1.0"})

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hadiths = data.get("hadiths", [])
                if len(hadiths) < info["expected_min"]:
                    print(f"[!] تحذير: عدد الأحاديث المسترجعة ({len(hadiths)}) أقل من المتوقع لـ {name}.")
                
                out_file.write_text(json.dumps(hadiths, ensure_ascii=False, indent=2), encoding="utf-8")
                size_mb = out_file.stat().st_size / (1024 * 1024)
                print(f"[✓] تم حفظ {name} في {out_file.name} بنجاح ({len(hadiths)} حديث، {size_mb:.2f} MB).")
                return True
        except Exception as e:
            print(f"[!] محاولة {attempt} فشلت: {e}", file=sys.stderr)
            time.sleep(2)

    return False

def download_all() -> None:
    for k in COLLECTIONS:
        download_collection(k)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target in COLLECTIONS:
        download_collection(target)
    else:
        download_all()
