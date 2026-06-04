# -*- coding: utf-8 -*-
"""
build_tags_doc.py — يولّد صفحة «معجم الوسوم» من tag_vocabulary.py،
ليبقى المعجم المعروض متزامنًا مع القائمة التي يفحصها validate_notes.

التشغيل:
    python build_tags_doc.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tag_vocabulary import VOCABULARY

PROJECT = ROOT.parent
OUT = PROJECT / "surahs" / "معجم-الوسوم.md"


def main() -> None:
    lines = [
        "# معجم الوسوم",
        "",
        "الوسوم المعتمدة مُصنَّفة أدناه. أضِف وسومًا جديدة بحُرّية — لا يمنعها الفحص؛",
        "إنما يُنبّه فقط على وسمٍ يشبه معتمدًا (تصحيح إملائي مرجَّح).",
        "",
        "> للبحث عن ملاحظات وسمٍ بعينه استخدم صندوق البحث 🔍 أو صفحة [الوسوم](tags.md).",
        "",
    ]
    for group, tags in VOCABULARY.items():
        lines.append(f"## {group}")
        lines.append("")
        lines.append("| الوسم | الوصف |")
        lines.append("|---|---|")
        for tag, desc in tags.items():
            lines.append(f"| `#{tag}` | {desc} |")
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    total = sum(len(t) for t in VOCABULARY.values())
    print(f"✓ كُتب {OUT.relative_to(PROJECT).as_posix()} — {total} وسمًا في {len(VOCABULARY)} فئات.")


if __name__ == "__main__":
    main()
