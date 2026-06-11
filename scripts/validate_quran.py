# -*- coding: utf-8 -*-
"""
validate_quran.py — يفحص الاقتباسات داخل صناديق `> "..."` في صفحات السور،
ويبلغ عن أي اقتباس لا يطابق نص القرآن المعتمد (Tanzil Uthmani).

ينزّل ملف القرآن مرّة واحدة في scripts/data/quran.json (مُتجاهل في git)،
ثم يقارن الاقتباسات بعد تجريد التشكيل والعلامات الخاصّة.

التشغيل:
    python validate_quran.py
    python validate_quran.py --include-fajr   # افحص ملاحظات الفجر أيضًا
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "quran.json"
PROJECT = ROOT.parent
QURAN_DIR = PROJECT / "surahs" / "quran"
FAJR_DIR = PROJECT / "surahs" / "fajr"
VERSES_DIR = PROJECT / "surahs" / "verses"

URL = "https://api.alquran.cloud/v1/quran/quran-simple-clean"
# نسخة "simple-clean" بالإملاء العربي الحديث (دون خصوصيات الرسم العثماني المختصر)

# علامات قرآنية صغيرة وحروف خاصة تُحذف للمقارنة
SPECIAL_RE = re.compile(
    r"["
    r"ؗ-ؚ"          # علامات قرآنية
    r"ً-ْ"          # تشكيل
    r"ٰ"                 # ألف خنجرية
    r"ۖ-ۭ"          # علامات وقف وسجدة قرآنية
    r"ـ"                 # تطويل (kashida)
    r"​-‏"          # zero-width
    r"ۜ۟۠ۢۥۦۨ"
    r"۪-۬"
    r"]"
)


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = SPECIAL_RE.sub("", s)
    s = s.replace("ٱ", "ا").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = s.replace("ى", "ي").replace("ئ", "ي").replace("ؤ", "و")
    s = re.sub(r"[«»\"'()،.:؛؟!ـ]+", " ", s)
    # علامات نهاية الآية، فواصل الاقتباسات المتعددة، الأقواس المعقوفة، وأرقام الآيات
    s = re.sub(r"[*۝۞{}0-9٠-٩]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_quran() -> dict[int, str]:
    if not DATA.exists():
        DATA.parent.mkdir(parents=True, exist_ok=True)
        print(f"⤓ تنزيل {URL}")
        urllib.request.urlretrieve(URL, DATA)
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    surahs = raw["data"]["surahs"]  # تنسيق alquran.cloud
    out: dict[int, str] = {}
    for sura in surahs:
        sid = sura["number"]
        out[sid] = " ".join(normalize(a["text"]) for a in sura["ayahs"])
    return out


QUOTE_RE = re.compile(r'^\s*>\s*(.+?)\s*$')          # سطر اقتباس (كل ما بعد >)
QUOTED_SPAN_RE = re.compile(r'["«]([^"»]+)["»]')     # نصّ داخل علامتي تنصيص "..." أو «...»
BRACE_SPAN_RE = re.compile(r'\{+\s*(.+?)\s*\}+')     # نصّ داخل أقواس معقوفة {{...}} أو {...}
SURAH_FNAME_RE = re.compile(r"^(\d{3})-(.+)\.md$")


def extract_quote(raw: str) -> str:
    """يستخرج نصّ الآية من سطر اقتباس بأيٍّ من الصيغ المستعملة:
    «النصّ» (مرجع) — "النصّ" — *{{النصّ}}* — {النصّ} [مرجع]."""
    raw = raw.strip().strip("*")            # أزل التوكيد/التظليل المحيط *...*
    m = QUOTED_SPAN_RE.search(raw) or BRACE_SPAN_RE.search(raw)
    if m:                                   # محدَّد بعلامات/أقواس — خُذ ما بداخلها وتجاهل المرجع
        return m.group(1).strip().strip("*")
    # غير محدَّد: احذف مرجعًا ملحقًا بين قوسين () أو [] في النهاية
    raw = re.sub(r"\s*[(\[][^)\]]*[)\]]\s*$", "", raw)
    return raw.strip().strip("\"'«»*{}")

# نعدّ السطر اقتباسًا قرآنيًا إذا كان أغلبه حروفًا عربيّة وطوله معقول
def looks_quranic(text: str) -> bool:
    norm = normalize(text)
    if len(norm) < 8:
        return False
    arabic = sum(1 for c in norm if "ء" <= c <= "ي")
    return arabic / max(1, len(norm.replace(" ", ""))) > 0.7


def scan(path: Path, sid: int, haystack: str, results: list) -> int:
    text = path.read_text(encoding="utf-8")
    n = 0
    in_comment = in_fence = False
    for ln, line in enumerate(text.split("\n"), 1):
        # تخطّي كتل الكود وتعليقات HTML (قوالب الإدخال والأمثلة توضع فيها)
        if re.match(r"^\s*(```|~~~)", line):
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
        m = QUOTE_RE.match(line)
        if not m:
            continue
        quote = extract_quote(m.group(1))
        if not looks_quranic(quote):
            continue
        n += 1
        if normalize(quote) not in haystack:
            results.append((path.relative_to(PROJECT).as_posix(), ln, sid, quote))
    return n


def main() -> None:
    include_fajr = "--include-fajr" in sys.argv
    quran = load_quran()
    # نفحص مقابل القرآن كاملًا: النموذج يقتبس آياتٍ من سورٍ أخرى عند بيان الترابط
    all_text = " ".join(quran.values())

    total = 0
    issues: list[tuple[str, int, int, str]] = []

    # 1) صفحات السور
    for f in sorted(QURAN_DIR.glob("[0-9]*.md")):
        m = SURAH_FNAME_RE.match(f.name)
        if not m:
            continue
        sid = int(m.group(1))
        if sid not in quran:
            continue
        total += scan(f, sid, all_text, issues)

    # 2) ملفات تدبر الآيات (اسم الملف يحدد السورة)
    if VERSES_DIR.exists():
        for page in VERSES_DIR.glob("*.md"):
            if page.name == "index.md":
                continue
            dm = re.match(r"^(\d{3})-", page.name)
            if not dm:
                continue
            sid = int(dm.group(1))
            if sid not in quran:
                continue
            total += scan(page, sid, all_text, issues)

    # 3) (اختياري) ملاحظات الفجر — نفس الفحص في كامل القرآن (sid=0)
    if include_fajr and FAJR_DIR.exists():
        for page in FAJR_DIR.glob("*.md"):
            total += scan(page, 0, all_text, issues)

    print(f"✓ فحصتُ {total} اقتباس آية.")
    if not issues:
        print("✓ كل الاقتباسات تطابق نص القرآن المعتمد.")
        return
    print(f"⚠ {len(issues)} اقتباس لا يطابق:")
    for src, ln, sid, q in issues[:40]:
        head = q if len(q) <= 90 else q[:87] + "…"
        sid_label = f"[{sid:03d}] " if sid else ""
        print(f"  • {src}:{ln}  {sid_label}«{head}»")
    if len(issues) > 40:
        print(f"  … و {len(issues) - 40} إضافيًّا.")


if __name__ == "__main__":
    main()
