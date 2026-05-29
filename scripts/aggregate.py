# -*- coding: utf-8 -*-
"""
aggregate.py — تجميع الملاحظات البلاغية والنحوية من كل ملفات السور في ملفّين مرجعيين.

يقرأ كل surahs/NNN-*.md، يستخرج قسمَي "ملاحظات بلاغية" و"ملاحظات نحوية ولغوية"
(الموجودَين بصيغة عناوين H2 ثابتة كما يفرضها prompt.md)، ثم يكتب:
    surahs/_تجميع-بلاغة.md
    surahs/_تجميع-نحو.md

التشغيل:
    python aggregate.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "surahs" / "quran"

# المفتاح يُستعمل في اسم الملف، والقيمة هي نص العنوان H2 المطلوب استخراجه.
SECTIONS = {
    "بلاغة": "ملاحظات بلاغية",
    "نحو": "ملاحظات نحوية ولغوية",
}


def extract_section(text: str, heading: str) -> str:
    """يُعيد محتوى قسم H2 معيّن حتى العنوان H2 التالي."""
    out: list[str] = []
    capturing = False
    for line in text.splitlines():
        if line.startswith("## "):
            capturing = line[3:].strip() == heading
            continue
        if capturing:
            out.append(line)
    return "\n".join(out).strip()


def surah_title(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.*)$", text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def main() -> None:
    files = sorted(p for p in OUTPUT_DIR.glob("*.md") if not p.name.startswith("_"))
    if not files:
        print("لا توجد ملفات سور بعد. شغّل contemplate.py أولًا.")
        return

    for key, heading in SECTIONS.items():
        blocks: list[str] = []
        for f in files:
            text = f.read_text(encoding="utf-8")
            section = extract_section(text, heading)
            if section:
                blocks.append(f"## {surah_title(text, f.stem)}\n\n{section}\n")
        out = OUTPUT_DIR / f"_تجميع-{key}.md"
        header = f"# تجميع: {heading}\n\n_مُولّد آليًا من كل ملفات السور — لا تُحرّره يدويًا._\n\n"
        out.write_text(header + "\n".join(blocks), encoding="utf-8")
        print(f"✓ {out.name} — {len(blocks)} سورة")


if __name__ == "__main__":
    main()
