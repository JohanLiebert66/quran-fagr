# -*- coding: utf-8 -*-
"""
build_whatsnew.py — يُنشئ صفحة "الجديد" تعرض آخر التحديثات بترتيب زمني تنازلي.

يجمع:
- صفحات السور المُولَّدة (حسب حقل `generated:` في frontmatter)
- إدخالات تدبر الآيات (`## ... ` + سطر `*YYYY-MM-DD ...*`)
- إدخالات مشاركات حلقة الفجر (نفس الصيغة)

ويعرض آخر 25 تحديثًا.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT = Path(__file__).resolve().parent.parent
SURAHS = PROJECT / "surahs"
QURAN = SURAHS / "quran"
NOTE_DIRS = [SURAHS / "fajr", SURAHS / "verses"]
OUT = SURAHS / "whats-new.md"
LIMIT = 25

DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
HEAD_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
GEN_RE = re.compile(r"^generated:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)


def collect() -> list[dict]:
    items = []

    # 1) صفحات السور — حقل generated في frontmatter
    if QURAN.exists():
        for f in sorted(QURAN.glob("[0-9]*.md")):
            text = f.read_text(encoding="utf-8")
            gm = GEN_RE.search(text)
            hm = H1_RE.search(text)
            if not gm:
                continue
            y, m, d = map(int, gm.group(1).split("-"))
            items.append({
                "date": date(y, m, d),
                "title": hm.group(1).strip() if hm else f.stem,
                "rel": f.relative_to(SURAHS).as_posix(),
                "label": "تدبر سورة",
            })

    # 2) ملاحظات الفجر والآيات — كل H2 + ميتاداتا تاريخها
    for d_dir in NOTE_DIRS:
        if not d_dir.exists():
            continue
        for page in sorted(d_dir.rglob("*.md")):
            if page.name == "index.md":
                continue
            text = page.read_text(encoding="utf-8")
            heads = list(HEAD_RE.finditer(text))
            for i, h in enumerate(heads):
                seg_end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
                segment = text[h.end():seg_end]
                lines = segment.lstrip().split("\n", 5)
                for line in lines[:3]:
                    if line.strip().startswith("*") and line.strip().endswith("*"):
                        dm = DATE_RE.search(line)
                        if dm:
                            y, mo, da = int(dm.group(1)), int(dm.group(2)), int(dm.group(3))
                            label = "تدبر آية" if d_dir.name == "verses" else "مشاركات الفجر"
                            items.append({
                                "date": date(y, mo, da),
                                "title": h.group(1).strip(),
                                "rel": page.relative_to(SURAHS).as_posix(),
                                "label": label,
                            })
                            break
    return items


def main() -> None:
    items = collect()
    items.sort(key=lambda x: x["date"], reverse=True)
    items = items[:LIMIT]

    lines = [
        "# الجديد",
        "",
        f"آخر {LIMIT} تحديث على الموقع، مرتَّبة من الأحدث إلى الأقدم.",
        "",
    ]
    if not items:
        lines.append("*لا توجد تحديثات بعد.*")
    else:
        for it in items:
            lines.append(f"- **{it['date'].isoformat()}** · *{it['label']}* — [{it['title']}]({it['rel']})")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✓ {OUT.name} — {len(items)} عنصر")


if __name__ == "__main__":
    main()
