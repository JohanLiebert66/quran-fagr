# -*- coding: utf-8 -*-
"""
validate_notes.py — يفحص أسطر الـ metadata في الملاحظات داخل صفحات الموقع.

سطر الملاحظة النموذجي (يولِّده note.py):
    *2026-06-01 · #توحيد · #آية-الكرسي · [البقرة:255](../quran/002-البقرة.md)*

الفحوص:
  أخطاء (توقِف النشر):
    • تاريخ غير صالح في بداية السطر (يجب أن يكون YYYY-MM-DD صحيحًا).
    • رابط داخلي مكسور: ملف .md مشار إليه غير موجود.
    • تعارُض المرجع: نصّ الرابط يقول «البقرة» لكنه يشير إلى ملف سورة أخرى.
  تحذيرات (لا توقِف النشر):
    • رقم آية خارج نطاق السورة.
    • وسم القالب «#وسم» نُسي في ملاحظة حقيقية.

التشغيل:
    python validate_notes.py            # يفحص كل صفحات surahs/
    python validate_notes.py --strict   # يعامل التحذيرات كأخطاء أيضًا
"""
from __future__ import annotations

import difflib
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from surahs import BY_NUMBER
from tag_vocabulary import APPROVED

PROJECT = ROOT.parent
SURAHS_DIR = PROJECT / "surahs"

# عدد آيات كل سورة (عدّ الكوفة/حفص) — مرجع ثابت للتحقق من نطاق الآية
AYAH_COUNTS = {
    1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75, 9: 129,
    10: 109, 11: 123, 12: 111, 13: 43, 14: 52, 15: 99, 16: 128, 17: 111,
    18: 110, 19: 98, 20: 135, 21: 112, 22: 78, 23: 118, 24: 64, 25: 77,
    26: 227, 27: 93, 28: 88, 29: 69, 30: 60, 31: 34, 32: 30, 33: 73, 34: 54,
    35: 45, 36: 83, 37: 182, 38: 88, 39: 75, 40: 85, 41: 54, 42: 53, 43: 89,
    44: 59, 45: 37, 46: 35, 47: 38, 48: 29, 49: 18, 50: 45, 51: 60, 52: 49,
    53: 62, 54: 55, 55: 78, 56: 96, 57: 29, 58: 22, 59: 24, 60: 13, 61: 14,
    62: 11, 63: 11, 64: 18, 65: 12, 66: 12, 67: 30, 68: 52, 69: 52, 70: 44,
    71: 28, 72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40, 79: 46,
    80: 42, 81: 29, 82: 19, 83: 36, 84: 25, 85: 22, 86: 17, 87: 19, 88: 26,
    89: 30, 90: 20, 91: 15, 92: 21, 93: 11, 94: 8, 95: 8, 96: 19, 97: 5,
    98: 8, 99: 8, 100: 11, 101: 11, 102: 8, 103: 3, 104: 9, 105: 5, 106: 4,
    107: 7, 108: 3, 109: 6, 110: 3, 111: 5, 112: 4, 113: 5, 114: 6,
}

# سطر ملاحظة = سطر يبدأ بـ * ثم تاريخ YYYY-MM-DD
NOTE_LINE_RE = re.compile(r"^\s*\*\s*(\d{4}-\d{2}-\d{2})\b(.*)$")
# روابط ماركداون [نص](مسار)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# مرجع سورة:آية داخل نصّ الرابط — مثل «البقرة:255» أو «البقرة»
REF_RE = re.compile(r"^\s*(.+?)\s*(?::\s*(\d+))?\s*$")
# وسم سطري مثل #توحيد أو #آية-الكرسي (نوقف عند الفراغ/الفواصل/نهاية التوكيد)
TAG_RE = re.compile(r"#([^\s#·)\]*،,]+)")


def name_slug(name: str) -> str:
    """يطابق منطق note.py: استبدال الفراغات بشرطات."""
    return name.strip().replace(" ", "-")


# اسم السورة (بعد توحيد الشرطات) -> رقمها، للتحقق من تطابق المرجع
SLUG_TO_NUMBER = {name_slug(name): n for n, name in BY_NUMBER.items()}


def _norm_tag(s: str) -> str:
    """توحيد الهجاء الشائع: ة/ه، ى/ي، ئ/ؤ، والهمزات، لمطابقة المتغيّرات."""
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ٱ", "ا"),
                 ("ة", "ه"), ("ى", "ي"), ("ئ", "ي"), ("ؤ", "و")):
        s = s.replace(a, b)
    return s


# الصيغة الموحّدة -> الوسم المعتمد، لكشف متغيّرات الهجاء
NORM_APPROVED = {_norm_tag(t): t for t in APPROVED}


def check_link(note_file: Path, text: str, target: str,
               errors: list, warnings: list, lineno: int) -> None:
    rel = note_file.relative_to(PROJECT).as_posix()

    # روابط خارجية (http/https/بريد) لا نفحصها
    if re.match(r"^[a-zA-Z]+:", target):
        return

    # تجريد المرساة (#...) قبل فحص وجود الملف
    path_part = target.split("#", 1)[0]
    if not path_part:
        return  # رابط لمرساة في الصفحة نفسها

    resolved = (note_file.parent / path_part).resolve()
    if not resolved.exists():
        errors.append(f"{rel}:{lineno}  رابط مكسور → {target}")
        return

    # إن كان الهدف صفحة سورة (quran/NNN-اسم.md) تحقّق من تطابق المرجع
    fname = resolved.name
    fm = re.match(r"^(\d{3})-(.+)\.md$", fname)
    if not fm or resolved.parent.name != "quran":
        return
    sid = int(fm.group(1))

    m = REF_RE.match(text)
    if not m:
        return
    ref_name = m.group(1).strip()
    ref_ayah = m.group(2)

    # نصّ الرابط قد يكون اسم سورة فقط أو «سورة:آية» — نتحقق إن كان اسم سورة معروفًا
    ref_slug = name_slug(ref_name)
    if ref_slug in SLUG_TO_NUMBER and SLUG_TO_NUMBER[ref_slug] != sid:
        errors.append(
            f"{rel}:{lineno}  تعارُض مرجع: نصّ «{ref_name}» "
            f"لكنه يشير إلى ملف سورة {sid:03d} ({BY_NUMBER.get(sid, '?')})"
        )
        return

    if ref_ayah is not None:
        ayah = int(ref_ayah)
        count = AYAH_COUNTS.get(sid)
        if count and not (1 <= ayah <= count):
            warnings.append(
                f"{rel}:{lineno}  رقم آية خارج النطاق: {BY_NUMBER.get(sid, sid)} "
                f"لها {count} آية، والمرجع يذكر {ayah}"
            )


def scan_file(note_file: Path, errors: list, warnings: list) -> int:
    text = note_file.read_text(encoding="utf-8")
    rel = note_file.relative_to(PROJECT).as_posix()
    in_comment = False
    in_fence = False
    n = 0
    for lineno, line in enumerate(text.split("\n"), 1):
        # تخطّي كتل الكود المسيَّجة (``` أو ~~~) — قوالب الأمثلة توضع داخلها
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # تخطّي مناطق تعليقات HTML (قوالب الأمثلة توضع داخلها أيضًا)
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue

        m = NOTE_LINE_RE.match(line)
        if not m:
            continue
        n += 1
        date_str, rest = m.group(1), m.group(2)

        # 1) صحّة التاريخ
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            errors.append(f"{rel}:{lineno}  تاريخ غير صالح → {date_str}")

        # 2) وسم القالب المنسي
        if "#وسم" in rest:
            warnings.append(f"{rel}:{lineno}  وسم القالب «#وسم» لم يُستبدل")

        # 2b) وسوم تشبه معتمدًا (متغيّر هجاء أو خطأ مرجَّح) — الجديدة تُقبل بصمت
        for tag in TAG_RE.findall(rest):
            if tag in APPROVED or tag.startswith("وسم"):
                continue
            nt = _norm_tag(tag)
            if nt in NORM_APPROVED:        # نفس الكلمة بهجاء مختلف
                warnings.append(
                    f"{rel}:{lineno}  وسم بهجاء غير موحّد «#{tag}» — استخدم «#{NORM_APPROVED[nt]}»"
                )
                continue
            near = difflib.get_close_matches(nt, list(NORM_APPROVED), n=1, cutoff=0.8)
            if near:
                warnings.append(
                    f"{rel}:{lineno}  وسم غير معتمد «#{tag}» — هل تقصد «#{NORM_APPROVED[near[0]]}»؟"
                )

        # 3) الروابط
        for link_text, target in LINK_RE.findall(rest):
            check_link(note_file, link_text, target, errors, warnings, lineno)
    return n


def main() -> None:
    strict = "--strict" in sys.argv
    errors: list[str] = []
    warnings: list[str] = []
    total = 0

    for f in sorted(SURAHS_DIR.rglob("*.md")):
        total += scan_file(f, errors, warnings)

    print(f"✓ فحصتُ {total} سطر ملاحظة في {SURAHS_DIR.name}/.")

    if warnings:
        print(f"⚠ {len(warnings)} تحذير:")
        for w in warnings:
            print(f"  • {w}")

    if errors:
        print(f"✗ {len(errors)} خطأ:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)

    if strict and warnings:
        print("✗ وضع --strict: التحذيرات تُعامل كأخطاء.")
        sys.exit(1)

    print("✓ كل أسطر الملاحظات سليمة.")


if __name__ == "__main__":
    main()
