# -*- coding: utf-8 -*-
"""
build_tags_index.py — يولّد صفحة «الملاحظات حسب الوسم»: قسمٌ لكل وسمٍ مستعمَل
يسرد الملاحظات التي تحمله، مع رابط لكل ملاحظة. مُعرِّف القسم من tag_anchor
ليطابقه رابط الشارة الذي يبنيه hook note_types.

التشغيل:
    python build_tags_index.py
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

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tag_vocabulary import tag_anchor

PROJECT = ROOT.parent
SURAHS = PROJECT / "surahs"
NOTE_DIRS = [SURAHS / "verses", SURAHS / "fajr"]
OUT = SURAHS / "الملاحظات-حسب-الوسم.md"

HEAD_RE = re.compile(r"^##\s+(.+?)\s*$")
META_RE = re.compile(r"^\s*\*\s*(\d{4}-\d{2}-\d{2})\b(.*)\*\s*$")
TAG_RE = re.compile(r"#([^\s#·)\]*،,]+)")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def collect() -> dict[str, list[dict]]:
    """وسم -> [ {date, title, rel} ] لكل ملاحظة تحمله."""
    by_tag: dict[str, list[dict]] = {}
    for d in NOTE_DIRS:
        if not d.exists():
            continue
        for page in sorted(d.glob("*.md")):
            if page.name == "index.md":
                continue
            text = strip_frontmatter(page.read_text(encoding="utf-8"))
            lines = text.split("\n")
            rel = page.relative_to(SURAHS).as_posix()
            in_fence = False
            cur_title = None
            for line in lines:
                if re.match(r"^\s*(```|~~~)", line):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                hm = HEAD_RE.match(line)
                if hm:
                    cur_title = hm.group(1).strip()
                    continue
                mm = META_RE.match(line)
                if not mm:
                    continue
                dm = DATE_RE.search(mm.group(1))
                dt = date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                tags = [t for t in TAG_RE.findall(mm.group(2)) if not t.startswith("وسم")]
                for tag in tags:
                    by_tag.setdefault(tag, []).append({
                        "date": dt,
                        "title": cur_title or rel,
                        "rel": rel,
                    })
    return by_tag


def main() -> None:
    by_tag = collect()
    lines = [
        "# الملاحظات حسب الوسم",
        "",
        "كل وسمٍ مستعمَل وتحته ملاحظاته. اضغط شارة الوسم في أي ملاحظة لتصل إلى قسمها هنا.",
        "",
    ]
    if not by_tag:
        lines.append("*لا توجد ملاحظات موسومة بعد.*")
    else:
        # ترتيب: الأكثر استعمالًا أولًا، ثم أبجديًّا
        for tag in sorted(by_tag, key=lambda t: (-len(by_tag[t]), t)):
            notes = sorted(by_tag[tag], key=lambda n: n["date"], reverse=True)
            lines.append(f"## #{tag} {{#{tag_anchor(tag)}}}")
            lines.append("")
            for nt in notes:
                lines.append(f"- [{nt['title']}]({nt['rel']}) · {nt['date'].isoformat()}")
            lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ كُتب {OUT.relative_to(PROJECT).as_posix()} — {len(by_tag)} وسمًا.")


if __name__ == "__main__":
    main()
