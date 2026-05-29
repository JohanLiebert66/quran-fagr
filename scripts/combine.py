# -*- coding: utf-8 -*-
"""
combine.py — دمج كل ملفات السور في ملف Markdown واحد جاهز للتحويل إلى Google Docs.

يقرأ surahs/quran/NNN-*.md بالترتيب، يزيل الـ frontmatter، ويكتب _combined.md في جذر المشروع.
بعدها — إن كان pandoc مُثبّتًا — حوّله إلى docx وارفعه على Google Drive:
    pandoc _combined.md -o quran-fagr.docx

عناوين H1 لكل سورة تظهر في "مخطط المستند" (Document outline) داخل Google Docs،
فتعمل عمل التبويبات تمامًا للتنقّل بين السور.

التشغيل:
    python combine.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "surahs" / "quran"
FRONTMATTER = re.compile(r"^---\n.*?\n---\n", re.DOTALL)


def main() -> None:
    files = sorted(p for p in OUTPUT_DIR.glob("*.md") if not p.name.startswith("_"))
    if not files:
        print("لا توجد ملفات سور بعد. شغّل contemplate.py أولًا.")
        return

    parts = ["# تدبر القرآن — مشروع فجر\n"]
    for f in files:
        body = FRONTMATTER.sub("", f.read_text(encoding="utf-8")).strip()
        parts.append(body)
        parts.append("\n\n---\n")  # فاصل بين السور

    combined = PROJECT_DIR / "_combined.md"
    combined.write_text("\n".join(parts), encoding="utf-8")
    print(f"✓ {combined.name} — دُمجت {len(files)} سورة")
    print("للتحويل إلى Google Docs:  pandoc _combined.md -o quran-fagr.docx  ثم ارفعها على Drive")


if __name__ == "__main__":
    main()
