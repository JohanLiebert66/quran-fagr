# -*- coding: utf-8 -*-
"""
validate_hadith.py — مدقق الأحاديث النبوية وتخريجها في صحيحي البخاري ومسلم.
يفحص أي نص مدخل أو يدقق ملفات الملاحظات وتدبرات الفجر لاستخراج الأحاديث المقتبسة
والتأكد من صحتها وثبوتها في الصحيحين وتنسيق شارة التخريج تلقائياً.

الاستخدام:
    python scripts/validate_hadith.py "إنما الأعمال بالنيات"
    python scripts/validate_hadith.py --file surahs/fajr/001-fatiha.md
    python scripts/validate_hadith.py --check-notes
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# استيراد محرك التخريج
try:
    from hadith_local import verify_hadith, normalize_text
except ImportError:
    from scripts.hadith_local import verify_hadith, normalize_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FAJR_DIR = PROJECT_ROOT / "surahs" / "fajr"

# أنماط استخراج الأحاديث النبوية من النصوص والملاحظات
HADITH_PATTERNS = [
    re.compile(r'(?:قال\s+(?:رسول\s+الله|النبي|صلى\s+الله\s+عليه\s+وسلم|ﷺ)|عن\s+النبي\s+ﷺ)\s*[:：]?\s*[«"\'“]([^»"\'”]{10,250})[»"\'”]', re.MULTILINE),
    re.compile(r'(?:وفي\s+الحديث|حديث)\s*[:：]?\s*[«"\'“]([^»"\'”]{10,250})[»"\'”]', re.MULTILINE),
]

def clean_quote(q: str) -> str:
    """تنظيف الاقتباس من علامات التنسيق مثل النجوم والأقواس."""
    q = re.sub(r"[\*_~`#]", "", q)
    return q.strip()

def extract_hadith_quotes(text: str) -> list[str]:
    """استخراج نصوص الأحاديث المحتملة من النص أو ملف الملاحظات."""
    quotes = set()
    for pattern in HADITH_PATTERNS:
        for match in pattern.finditer(text):
            q = clean_quote(match.group(1))
            # تجنب أرقام الآيات أو العبارات القصيرة جداً أو روابط
            if len(q) >= 12 and not q.startswith("http") and not q.startswith("أخرجه"):
                quotes.add(q)
    return list(quotes)

def check_single_text(text: str, enrich: bool = False) -> None:
    """فحص نص حديث وتوليد بطاقة التخريج المعتمدة."""
    print("=" * 70)
    print(f"🔍 فحص الحديث: \"{text}\"")
    print("=" * 70)

    res = verify_hadith(text, enrich=enrich)
    print(res["citation_badge"])

    if res["status"] == "muttafaq_alayh":
        print("✅ الحكم: صحيح، متفق عليه في أعلى درجات الصحة.")
    elif res["status"] in ("bukhari_only", "muslim_only"):
        print("✅ الحكم: صحيح، ثابت في أصح دواوين السنة النبوية.")
    else:
        print("⚠️ تنبيه: لم يُعثر على هذا اللفظ في صحيحي البخاري ومسلم.")
        print("   يُنصح بمراجعة كتب السنن الأربعة أو مجمع الزوائد أو التأكد من سلامة اللفظ المنقول.")

    if res["bukhari_sample"]:
        print(f"\n[البخاري]: {res['bukhari_sample'][:180]}...")
    if res["muslim_sample"] and not res["bukhari_sample"]:
        print(f"\n[مسلم]: {res['muslim_sample'][:180]}...")
    print("\n")

def audit_file(file_path: Path) -> int:
    """تدقيق ملف Markdown للتحقق من الأحاديث الواردة فيه."""
    if not file_path.exists():
        print(f"[!] الملف غير موجود: {file_path}", file=sys.stderr)
        return 0

    content = file_path.read_text(encoding="utf-8")
    quotes = extract_hadith_quotes(content)

    print(f"📄 فحص الملف: {file_path.name} (عدد الأحاديث المكتشفة: {len(quotes)})")
    unverified = 0

    for q in quotes:
        res = verify_hadith(q)
        if res["status"] in ("muttafaq_alayh", "bukhari_only", "muslim_only"):
            print(f"  [✓] موثق: \"{q[:45]}...\" -> {res['takhrij']}")
        else:
            print(f"  [?] غير مؤكد في الصحيحين: \"{q[:45]}...\"")
            unverified += 1

    return unverified

def audit_notes_directory(dir_path: Path) -> None:
    """تدقيق شامل لكافة ملفات مجلد ملاحظات الفجر."""
    if not dir_path.exists():
        print(f"[!] المجلد غير موجود: {dir_path}", file=sys.stderr)
        return

    md_files = sorted(dir_path.glob("*.md"))
    print(f"🚀 بدء التدقيق الشامل للأحاديث في {len(md_files)} ملفات ملاحظات...")
    total_unverified = 0
    checked_files = 0

    for md in md_files:
        content = md.read_text(encoding="utf-8")
        quotes = extract_hadith_quotes(content)
        if quotes:
            checked_files += 1
            uv = audit_file(md)
            total_unverified += uv

    print("-" * 70)
    print(f"📊 الخلاصة: تم فحص {checked_files} ملفاً تحوي أحاديث. (غير المؤكد في الصحيحين: {total_unverified})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="تدقيق وتخريج الأحاديث في صحيحي البخاري ومسلم.")
    parser.add_argument("query", nargs="?", type=str, help="نص الحديث للتحقق منه وتخريجه")
    parser.add_argument("--file", "-f", type=Path, help="مسار ملف Markdown للتدقيق")
    parser.add_argument("--check-notes", "-n", action="store_true", help="فحص جميع ملاحظات الفجر في surahs/fajr/")
    parser.add_argument("--enrich", "-e", action="store_true", help="استرجاع بيانات إضافية من UmmahAPI")
    args = parser.parse_args()

    if args.query:
        check_single_text(args.query, enrich=args.enrich)
    elif args.file:
        audit_file(args.file)
    elif args.check_notes:
        audit_notes_directory(FAJR_DIR)
    else:
        parser.print_help()
