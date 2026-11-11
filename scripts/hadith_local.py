# -*- coding: utf-8 -*-
"""
hadith_local.py — محرك البحث والتخريج فائق السرعة لصحيحي البخاري ومسلم
يقرأ نصوص الأحاديث محلياً من data/hadith/ وينفذ بحثاً دقيقاً مع معالجة
التشكيل واختلافات الرسم، ويصيغ التخريج المعتمد (متفق عليه / البخاري / مسلم).
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_HADITH_DIR = PROJECT_ROOT / "data" / "hadith"

# علامات التشكيل والحركات والرموز الخاصة
TASHKEEL_RE = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06EDـ\u200c\u200d\u200e\u200f]")
PUNCT_RE = re.compile(r"[\.,;:!\?\"'«»\(\)\[\]،؛:\؟]")

_CACHE: dict[str, list[dict]] = {}

def normalize_text(text: str) -> str:
    """تجريد النص العربي من التشكيل وتوحيد الحروف للمطابقة الدقيقة."""
    if not text:
        return ""
    s = TASHKEEL_RE.sub("", text)
    s = PUNCT_RE.sub(" ", s)
    s = re.sub(r"[إأآا]", "ا", s)
    s = re.sub(r"[يى]", "ي", s)
    s = re.sub(r"ة", "ه", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def stem_word(w: str) -> str:
    """جذع بسيط للكلمات الشائعة لمعالجة الزوائد وحروف العطف والجمع والمفرد."""
    # إزالة السوابق: و، ف، ل، ك، ب، الـ
    w = re.sub(r"^[وفلكب]?(ال)?", "", w)
    # إزالة اللواحق: ات، ون، ين، ه، ي، نا، كم، هم، ها
    w = re.sub(r"(ات|ون|ين|ه|ي|نا|كم|هم|ها)$", "", w)
    return w

def load_collection(name: str) -> list[dict]:
    """تحميل فهرس أحاديث كتاب معين وتجهيز جذور كلماته في الذاكرة."""
    if name in _CACHE:
        return _CACHE[name]

    filepath = DATA_HADITH_DIR / f"{name}.json"
    if not filepath.exists():
        try:
            from download_hadiths import download_collection
            download_collection(name)
        except Exception as e:
            print(f"[!] تعذر تنزيل كتاب {name}: {e}", file=sys.stderr)
            return []

    try:
        raw_list = json.loads(filepath.read_text(encoding="utf-8"))
        indexed = []
        for item in raw_list:
            text = item.get("text", "")
            norm = normalize_text(text)
            words = norm.split()
            stems = {stem_word(w) for w in words if len(w) > 2}
            indexed.append({
                "number": item.get("hadithnumber"),
                "arabicnumber": item.get("arabicnumber"),
                "raw_text": text,
                "norm_text": norm,
                "stems": stems,
                "reference": item.get("reference", {}),
            })
        _CACHE[name] = indexed
        return indexed
    except Exception as e:
        print(f"[!] خطأ في قراءة ملف {filepath}: {e}", file=sys.stderr)
        return []

def search_in_book(book_name: str, query: str, max_results: int = 5) -> list[dict]:
    """
    البحث عن نص حديث داخل كتاب محدد بثلاث طبقات:
    1. مطابقة العبارة المتصلة.
    2. مطابقة الكلمات كاملة.
    3. مطابقة جذوع الكلمات (لتغطية صيغ الجمع/المفرد واختلافات الروايات).
    """
    items = load_collection(book_name)
    norm_q = normalize_text(query)
    if not norm_q:
        return []

    # 1. مطابقة العبارة المتصلة
    results = [h for h in items if norm_q in h["norm_text"]]
    if results:
        return results[:max_results]

    words = [w for w in norm_q.split() if len(w) > 2]
    if not words:
        return []

    # 2. مطابقة جميع الكلمات الأساسية
    results = [h for h in items if all(w in h["norm_text"] for w in words)]
    if results:
        return results[:max_results]

    # 3. مطابقة جذوع الكلمات
    q_stems = [stem_word(w) for w in words if len(stem_word(w)) >= 2]
    if len(q_stems) >= 2:
        results = [h for h in items if all(s in h["stems"] for s in q_stems)]
        if results:
            return results[:max_results]

    return []

def enrich_from_ummahapi(collection: str, hadith_number: int) -> dict | None:
    """استعلام اختياري من UmmahAPI لتأكيد الرتبة والباب والمطابقة."""
    url = f"https://ummahapi.com/api/hadith/{collection}/{hadith_number}"
    req = urllib.request.Request(url, headers={"User-Agent": "quran-fagr/1.0"})
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("success"):
                d = data.get("data", {})
                return {
                    "grade": d.get("grade", "Sahih"),
                    "english": d.get("english", ""),
                    "chapter": d.get("chapter", ""),
                }
    except Exception:
        pass
    return None

def verify_hadith(query: str, enrich: bool = False) -> dict:
    """
    فحص الحديث في صحيحي البخاري ومسلم، وتحديد ما إذا كان متفقاً عليه أو منفرداً.
    """
    bukhari_matches = search_in_book("bukhari", query, max_results=3)
    muslim_matches = search_in_book("muslim", query, max_results=3)

    is_in_bukhari = len(bukhari_matches) > 0
    is_in_muslim = len(muslim_matches) > 0

    bukhari_nums = [m["number"] for m in bukhari_matches]
    muslim_nums = [m["number"] for m in muslim_matches]

    status = "not_found"
    takhrij_text = ""

    if is_in_bukhari and is_in_muslim:
        status = "muttafaq_alayh"
        b_str = ", ".join(str(n) for n in bukhari_nums[:2])
        m_str = ", ".join(str(n) for n in muslim_nums[:2])
        takhrij_text = f"**متفق عليه** — أخرجه البخاري (رقم: {b_str})، ومسلم (رقم: {m_str})"
    elif is_in_bukhari:
        status = "bukhari_only"
        b_str = ", ".join(str(n) for n in bukhari_nums[:2])
        takhrij_text = f"أخرجه البخاري (رقم: {b_str}) — صحيح"
    elif is_in_muslim:
        status = "muslim_only"
        m_str = ", ".join(str(n) for n in muslim_nums[:2])
        takhrij_text = f"أخرجه مسلم (رقم: {m_str}) — صحيح"
    else:
        status = "not_in_sahihayn"
        takhrij_text = "لم يُعثر عليه في صحيحي البخاري ومسلم (يتطلب مراجعة دواوين السنة الأخرى)"

    enriched_info = {}
    if enrich and (is_in_bukhari or is_in_muslim):
        col = "bukhari" if is_in_bukhari else "muslim"
        num = bukhari_nums[0] if is_in_bukhari else muslim_nums[0]
        extra = enrich_from_ummahapi(col, num)
        if extra:
            enriched_info = extra

    return {
        "status": status,
        "is_muttafaq_alayh": status == "muttafaq_alayh",
        "in_bukhari": is_in_bukhari,
        "in_muslim": is_in_muslim,
        "bukhari_numbers": bukhari_nums,
        "muslim_numbers": muslim_nums,
        "bukhari_sample": bukhari_matches[0]["raw_text"] if is_in_bukhari else None,
        "muslim_sample": muslim_matches[0]["raw_text"] if is_in_muslim else None,
        "takhrij": takhrij_text,
        "citation_badge": f"📜 **تخريج الحديث**: {takhrij_text}",
        "enriched": enriched_info,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="فحص وتخريج الأحاديث في صحيحي البخاري ومسلم.")
    parser.add_argument("query", type=str, help="نص الحديث أو جزء منه للبحث والتخريج")
    parser.add_argument("--enrich", "-e", action="store_true", help="طلب بيانات إضافية من UmmahAPI")
    args = parser.parse_args()

    t0 = time.time()
    res = verify_hadith(args.query, enrich=args.enrich)
    t1 = time.time()

    print("=" * 65)
    print(res["citation_badge"])
    print("=" * 65)
    print(f"⏱️ زمن المعالجة: {(t1 - t0) * 1000:.1f} مللي ثانية")
    if res["bukhari_sample"]:
        print("\n📖 نص الحديث عند البخاري:")
        print(res["bukhari_sample"][:250] + "...")
    if res["muslim_sample"]:
        print("\n📖 نص الحديث عند مسلم:")
        print(res["muslim_sample"][:250] + "...")
