# -*- coding: utf-8 -*-
"""
auto_bold.py — تشديد المصطلحات المحورية في صفحات السور الموجودة (دون استدعاء Gemini).

يمشي على `surahs/quran/*.md` ويلفّ المصطلحات المعروفة بـ `**...**` لتسهيل المسح البصري،
دون لمس:
- الـ frontmatter
- الآيات داخل صناديق الاقتباس (`> "..."`)
- العناوين (الأسطر التي تبدأ بـ #)
- النصوص المُشدَّدة مسبقًا (**...**)
- نصوص الروابط [نص](رابط)

التشغيل:
    python auto_bold.py                # شدِّد كل ملفات السور
    python auto_bold.py --dry          # عرض ما سيتغيّر دون كتابة
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

QURAN = Path(__file__).resolve().parent.parent / "surahs" / "quran"

# قائمة المصطلحات (من الأطول إلى الأقصر لتجنّب التضارب مع المصطلحات المركّبة)
KEY_TERMS = [
    # تعابير مركّبة (يجب أن تأتي أولًا)
    "الصراط المستقيم", "الحي القيوم", "آية الكرسي", "المقصد الرئيسي",
    "الموضوع الرئيسي", "أم الكتاب",
    # أسماء الأنبياء
    "إبراهيم", "إسماعيل", "إسحاق", "يعقوب", "موسى", "هارون", "عيسى", "محمد",
    "نوح", "يوسف", "داود", "داوود", "سليمان", "يونس", "يحيى", "زكريا",
    "آدم", "إدريس", "لوط", "هود", "صالح", "شعيب", "إلياس", "اليسع", "أيوب",
    # أسماء الله الحسنى
    "الرحمن", "الرحيم", "الواحد", "الأحد", "السميع", "البصير", "العليم",
    "الحكيم", "اللطيف", "الخبير", "الرزاق", "الجبار", "المتكبر",
    "الغفور", "الغفار", "العزيز", "القدير", "الكريم", "الودود", "الحي",
    "القيوم", "الحق", "النور", "الفتاح",
    # مفاهيم محورية
    "التوحيد", "التقوى", "الإيمان", "الشرك", "الكفر", "النفاق", "الإسلام",
    "الإحسان", "الهداية", "الجنة", "النار", "الآخرة", "الدنيا", "البعث",
    "الحساب", "الرسالة", "النبوة", "الوحي", "القدر", "الكتاب", "الذكر",
    "الصلاة", "الزكاة", "الصوم", "الحج", "الجهاد", "الشهادة",
    # علوم وأقسام
    "تدبر", "تفسير", "بلاغة", "نحو", "صرف", "تجويد", "فقه", "عقيدة",
    "سيرة",
]
# رتّب من الأطول إلى الأقصر دائمًا
KEY_TERMS = sorted(set(KEY_TERMS), key=len, reverse=True)

# نمط حقول لا نلمسها داخل السطر: **...** أو [...](...)
PROTECTED_SPAN = re.compile(r"\*\*[^*\n]+\*\*|\[[^\]\n]+\]\([^\)\n]+\)")

# لحَدِّ الكلمة العربية: ليس قبلها/بعدها حرف عربي
AR = r"ء-ي"


def make_term_pat(term: str) -> re.Pattern:
    return re.compile(rf"(?<![{AR}])({re.escape(term)})(?![{AR}])")


PATTERNS = [(t, make_term_pat(t)) for t in KEY_TERMS]


def process_line(line: str) -> str:
    """شدِّد المصطلحات في السطر، مع حماية ما يقع داخل ** أو روابط Markdown."""
    parts: list[tuple[str, str]] = []
    pos = 0
    for m in PROTECTED_SPAN.finditer(line):
        if m.start() > pos:
            parts.append(("plain", line[pos:m.start()]))
        parts.append(("keep", m.group(0)))
        pos = m.end()
    if pos < len(line):
        parts.append(("plain", line[pos:]))

    out = []
    for kind, text in parts:
        if kind == "keep":
            out.append(text)
            continue
        for _term, pat in PATTERNS:
            text = pat.sub(r"**\1**", text)
        out.append(text)
    return "".join(out)


def process_file(path: Path) -> tuple[int, int]:
    """يُعيد (عدد الأسطر المُعدَّلة، إجمالي الأسطر النصية المعالَجة)."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    in_fm = False
    changed = 0
    touched = 0
    new_lines = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        # frontmatter بين ---
        if line.strip() == "---":
            in_fm = not in_fm
            new_lines.append(line)
            continue
        if in_fm or stripped.startswith(">") or stripped.startswith("#"):
            new_lines.append(line)
            continue
        touched += 1
        new = process_line(line)
        if new != line:
            changed += 1
        new_lines.append(new)
    new_text = "\n".join(new_lines)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return changed, touched


def main() -> None:
    dry = "--dry" in sys.argv
    files = sorted(QURAN.glob("[0-9]*.md"))
    total_changed = 0
    files_changed = 0
    for f in files:
        before = f.read_text(encoding="utf-8")
        changed, _ = process_file(f)
        if dry:
            f.write_text(before, encoding="utf-8")  # تراجع في وضع المعاينة
        if changed:
            files_changed += 1
            total_changed += changed
    label = "(معاينة)" if dry else ""
    print(f"✓ {label} {files_changed}/{len(files)} ملف تغيّر؛ {total_changed} سطر مُشدَّد.")


if __name__ == "__main__":
    main()
