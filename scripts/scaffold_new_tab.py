# -*- coding: utf-8 -*-
"""
scaffold_new_tab.py — أداة لمرّة واحدة:

  1) تُنشئ تبويب «تدبر السور ٢» (surahs/quran2/) كحاوية لملفات تدبّر بمصدر/نموذج مختلف.
  2) تُنشئ هيكلًا (skeleton) لكل سورة في surahs/verses/ — ملف لكل سورة فيه قالب
     إدخال جاهز يصنّف الملاحظات بالوسوم: #تدبر للتأمّل، #سؤال للأسئلة.

لا تكتب فوق أي ملف موجود في verses/ (تحفظ الملاحظات السابقة). أعد تشغيلها بأمان.
أسماء السور وأرقامها تُؤخذ من أسماء ملفات surahs/quran/ (المصدر المرجعي 001-اسم.md).
"""
from __future__ import annotations

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "surahs"
QURAN = DOCS / "quran"
VERSES = DOCS / "verses"
QURAN2 = DOCS / "quran2"

SURAH_RE = re.compile(r"^(\d{3})-(.+)\.md$")


def surah_list() -> list[tuple[str, str]]:
    """[(NNN, slug-name), ...] مرتّبة، من ملفات تبويب «تدبر السور»."""
    out = []
    for f in sorted(QURAN.glob("*.md")):
        m = SURAH_RE.match(f.name)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def make_new_tab() -> None:
    QURAN2.mkdir(exist_ok=True)
    (QURAN2 / ".pages").write_text(
        "title: تدبر السور ٢\norder: asc\n", encoding="utf-8"
    )
    index = (
        "# تدبر السور ٢\n\n"
        "نسخةٌ موازية لتبويب **«تدبر السور»**، بمصدرٍ/نموذجٍ مختلف وتركيبٍ مختلف "
        "في عرض التدبّر لكل سورة.\n\n"
        "تُضاف كل سورة كملف `NNN-اسم-السورة.md` (مثل `002-البقرة.md`) داخل هذا "
        "المجلد، فتظهر تلقائيًا في الشريط الجانبي مرتَّبةً برقمها.\n"
    )
    (QURAN2 / "index.md").write_text(index, encoding="utf-8")
    print(f"[tab] {QURAN2} (.pages + index.md)")


def skeleton(nnn: str, slug: str) -> str:
    name = slug.replace("-", " ")
    link = f"../quran/{nnn}-{slug}.md"
    num = str(int(nnn))
    return (
        f"# {nnn} — {name}\n\n"
        "<!--\n"
        "قالب إدخال — انسخ المقطع المناسب أسفل العنوان واملأه، ثم احذف هذا التعليق "
        "إن شئت.\n"
        "التصنيف بالوسم:  #تدبر  للتأمّل  ·  #سؤال  للسؤال.\n\n"
        "## آية N: \"مطلع الآية\"\n"
        f"*YYYY-MM-DD · #تدبر · [{name}:N]({link})*\n"
        "> \"نص الآية كاملًا\"\n\n"
        "اكتب تدبّرك هنا…\n\n"
        "## آية N: \"مطلع الآية\"\n"
        f"*YYYY-MM-DD · #سؤال · [{name}:N]({link})*\n"
        "> \"نص الآية كاملًا\"\n\n"
        "اكتب سؤالك هنا…\n"
        "-->\n"
    )


def make_skeletons() -> None:
    created = skipped = 0
    for nnn, slug in surah_list():
        target = VERSES / f"{nnn}-{slug}.md"
        if target.exists():
            skipped += 1
            continue
        target.write_text(skeleton(nnn, slug), encoding="utf-8")
        created += 1
    print(f"[verses] created {created} skeleton(s), skipped {skipped} existing")


if __name__ == "__main__":
    make_new_tab()
    make_skeletons()
    print("done.")
