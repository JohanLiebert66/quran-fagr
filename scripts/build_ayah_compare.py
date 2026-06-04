# -*- coding: utf-8 -*-
"""
build_ayah_compare.py — يولّد صفحة «مقارنة التدبر عبر الختمات».

يفحص صفحات الآيات (surahs/verses/NNN-سورة.md)، ويُجمِّع الملاحظات حسب (السورة،
الآية) من عنوان «## آية N». كل آيةٍ تأمّلتَها أكثر من مرّة تظهر في الصفحة، وتحتها
كل تأمّل مُعنوَنًا بختمته وتاريخه — لمقارنة تطوّر الفهم بين الختمات.

التشغيل:
    python build_ayah_compare.py
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
from surahs import BY_NUMBER
from khatmas_registry import parse_registry, khatma_for

PROJECT = ROOT.parent
SURAHS = PROJECT / "surahs"
VERSES = SURAHS / "verses"
REGISTRY = SURAHS / "khatmas" / "index.md"
OUT = SURAHS / "مقارنة-التدبر.md"

HEAD_RE = re.compile(r"^##\s+(.+?)\s*$")
META_RE = re.compile(r"^\s*\*\s*(\d{4}-\d{2}-\d{2})\b(.*)\*\s*$")
AYAH_RE = re.compile(r"آية\s*(\d+)")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
_AR = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def ar(n: int) -> str:
    return str(n).translate(_AR)


def strip_fm(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def collect() -> dict[tuple[int, int], list[dict]]:
    """(سورة، آية) -> [ {date, snippet, rel} ] مرتّبة."""
    out: dict[tuple[int, int], list[dict]] = {}
    if not VERSES.exists():
        return out
    for page in sorted(VERSES.glob("*.md")):
        if page.name == "index.md":
            continue
        sm = re.match(r"^(\d{3})-", page.name)
        if not sm:
            continue
        sid = int(sm.group(1))
        rel = page.relative_to(SURAHS).as_posix()
        lines = strip_fm(page.read_text(encoding="utf-8")).split("\n")
        in_fence = False
        cur_ayah: int | None = None
        i = 0
        while i < len(lines):
            line = lines[i]
            if FENCE_RE.match(line):
                in_fence = not in_fence
                i += 1
                continue
            if not in_fence:
                hm = HEAD_RE.match(line)
                if hm:
                    am = AYAH_RE.search(hm.group(1))
                    cur_ayah = int(am.group(1)) if am else None
                    i += 1
                    continue
                mm = META_RE.match(line)
                if mm and cur_ayah is not None:
                    dm = DATE_RE.search(mm.group(1))
                    dt = date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                    snippet = ""
                    for j in range(i + 1, min(len(lines), i + 6)):
                        cand = lines[j].strip()
                        if cand and not cand.startswith((">", "#")):
                            snippet = cand[:200]
                            break
                    out.setdefault((sid, cur_ayah), []).append(
                        {"date": dt, "snippet": snippet, "rel": rel}
                    )
            i += 1
    return out


def main() -> None:
    khatmas = parse_registry(REGISTRY)
    by_ayah = collect()
    # أبقِ الآيات المتكرّرة فقط
    repeated = {k: v for k, v in by_ayah.items() if len(v) >= 2}

    lines = [
        "# مقارنة التدبر عبر الختمات",
        "",
        "الآيات التي تأمّلتَها أكثر من مرّة، وتحت كلٍّ منها تأمّلاتها مرتّبةً زمنيًّا",
        "ومُعنوَنةً بختمتها — لتقارن تطوّر فهمك للآية بين الختمات.",
        "",
    ]
    if not repeated:
        lines += [
            "> لا توجد آيةٌ تكرّر تدبّرها بعد. عند تأمّلك آيةً سبق أن دوّنتَ فيها"
            " (بإضافة قسم `## آية N` جديد بتاريخٍ لاحق)، تظهر هنا مقارنةً بين الختمات.",
        ]
    else:
        for (sid, ayah) in sorted(repeated):
            notes = sorted(repeated[(sid, ayah)], key=lambda n: n["date"])
            name = BY_NUMBER.get(sid, str(sid))
            khset = {(khatma_for(n["date"], khatmas) or {}).get("number") for n in notes}
            multi = len([x for x in khset if x]) >= 2
            badge = "  ⟳ متعدّد الختمات" if multi else ""
            lines.append(f"## {name}:{ar(ayah)}{badge}")
            lines.append("")
            for n in notes:
                k = khatma_for(n["date"], khatmas)
                label = f"ختمة {ar(k['number'])} · {n['date'].isoformat()}" if k else n["date"].isoformat()
                snippet = n["snippet"] or "—"
                lines.append(f"- **{label}** — {snippet} [↗]({n['rel']})")
            lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ كُتب {OUT.relative_to(PROJECT).as_posix()} — {len(repeated)} آية متكرّرة.")


if __name__ == "__main__":
    main()
