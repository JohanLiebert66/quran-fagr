# -*- coding: utf-8 -*-
"""
build_khatmas.py — يُنشئ صفحة لكل ختمة في `surahs/khatmas/` تجمع الملاحظات
(من تدبر الآيات ومشاركات حلقة الفجر) التي أُضيفت خلال مدتها.

يقرأ سجل الختمات من جدول Markdown داخل `surahs/khatmas/index.md` بالأعمدة:
    | الرقم | الاسم | البدء | الانتهاء |

ثم يفحص كل ملاحظة (`## عنوان` متبوع بسطر `*YYYY-MM-DD · ...*`) ويُلحقها بالختمة
المناسبة. تُحذف صفحات الختمات القديمة التي لم تعد في السجل.

التشغيل:
    python build_khatmas.py
"""
from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT = Path(__file__).resolve().parent.parent
SURAHS = PROJECT / "surahs"
KHATMAS = SURAHS / "khatmas"
REGISTRY = KHATMAS / "index.md"

NOTE_DIRS = [SURAHS / "fajr", SURAHS / "verses"]
QURAN = SURAHS / "quran"
GEN_RE_FM = re.compile(r"^generated:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

# صف بيانات داخل جدول Markdown: |a|b|c|d|  (ليس صف الفواصل ---)
ROW_RE = re.compile(r"^\s*\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|\s*$", re.MULTILINE)
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
HEAD_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
META_RE = re.compile(r"^\s*\*([^\n*]+)\*\s*$", re.MULTILINE)


def parse_registry() -> list[dict]:
    if not REGISTRY.exists():
        return []
    text = REGISTRY.read_text(encoding="utf-8")
    out = []
    for m in ROW_RE.finditer(text):
        a, b, c, d = (x.strip() for x in m.groups())
        # تجاهَل صف الرؤوس
        if a.isdigit() is False:
            continue
        start_m = DATE_RE.search(c)
        end_m = DATE_RE.search(d)
        if not start_m:
            continue
        start = date(int(start_m.group(1)), int(start_m.group(2)), int(start_m.group(3)))
        end = None
        if end_m:
            end = date(int(end_m.group(1)), int(end_m.group(2)), int(end_m.group(3)))
        out.append({
            "number": int(a),
            "name": b,
            "start": start,
            "end": end,
        })
    return sorted(out, key=lambda k: k["number"])


def slug(name: str) -> str:
    return name.strip().replace("/", "-").replace(" ", "-")


def collect_notes() -> list[dict]:
    """يُعيد قائمة من (date, source_rel, source_label, title, snippet)
    — من ملاحظاتك اليدوية فقط، دون السور المولَّدة آليًا."""
    out = []

    for d in NOTE_DIRS:
        if not d.exists():
            continue
        for page in sorted(d.rglob("*.md")):
            if page.name == "index.md":
                continue
            try:
                text = page.read_text(encoding="utf-8")
            except Exception:
                continue
            # remove frontmatter
            if text.startswith("---"):
                end = text.find("\n---", 3)
                if end != -1:
                    text = text[end + 4:]
            heads = list(HEAD_RE.finditer(text))
            for i, h in enumerate(heads):
                section_start = h.end()
                section_end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
                section = text[section_start:section_end]
                # ابحث عن سطر metadata في أول 5 أسطر
                lines = section.lstrip().split("\n", 5)
                dt = None
                snippet = ""
                for j, line in enumerate(lines[:5]):
                    mm = DATE_RE.search(line)
                    if mm and line.strip().startswith("*") and line.strip().endswith("*"):
                        dt = date(int(mm.group(1)), int(mm.group(2)), int(mm.group(3)))
                        # snippet = أول سطر نصّي بعد الـ metadata، يتجاهل blockquote
                        for k in range(j + 1, min(len(lines), j + 5)):
                            cand = lines[k].strip()
                            if cand and not cand.startswith(">") and not cand.startswith("#"):
                                snippet = cand[:140]
                                break
                        break
                if not dt:
                    continue
                rel = page.relative_to(SURAHS).as_posix()
                label = page.relative_to(SURAHS).parts[0]   # "fajr" أو "verses"
                label_ar = {"fajr": "مشاركات الفجر", "verses": "تدبر آية"}.get(label, label)
                out.append({
                    "date": dt,
                    "rel": rel,
                    "label": label_ar,
                    "title": h.group(1).strip(),
                    "snippet": snippet,
                })
    return out


def in_range(note_date: date, k: dict) -> bool:
    if note_date < k["start"]:
        return False
    if k["end"] is None:
        return note_date <= date.today()
    return note_date <= k["end"]


def write_khatma_page(k: dict, notes: list[dict]) -> Path:
    notes = sorted(notes, key=lambda n: n["date"])
    fname = f"{k['number']:03d}-{slug(k['name'])}.md"
    path = KHATMAS / fname
    end_str = k["end"].isoformat() if k["end"] else "— (جارية)"
    duration = ((k["end"] or date.today()) - k["start"]).days + 1
    lines = [
        f"# {k['number']:03d} — {k['name']}",
        "",
        f"- **البدء:** {k['start'].isoformat()}",
        f"- **الانتهاء:** {end_str}",
        f"- **المدة:** {duration} يومًا",
        f"- **عدد الملاحظات:** {len(notes)}",
        "",
        "## الملاحظات",
        "",
    ]
    if not notes:
        lines.append("*لا توجد ملاحظات في هذه المدّة بعد.*")
    else:
        for n in notes:
            link = f"../{n['rel']}"
            lines.append(f"### {n['date'].isoformat()} — [{n['title']}]({link})")
            lines.append(f"*{n['label']}*")
            if n["snippet"]:
                lines.append("")
                lines.append(n["snippet"])
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    KHATMAS.mkdir(parents=True, exist_ok=True)
    khatmas = parse_registry()
    if not khatmas:
        print("لا يوجد سجل ختمات بعد — أضف صفًّا للجدول في khatmas/index.md")
        return
    all_notes = collect_notes()
    kept = {"index.md"}
    for k in khatmas:
        matched = [n for n in all_notes if in_range(n["date"], k)]
        path = write_khatma_page(k, matched)
        kept.add(path.name)
        print(f"✓ {path.name} — {len(matched)} ملاحظة")
    # نظّف صفحات الختمات القديمة
    for old in KHATMAS.glob("*.md"):
        if old.name not in kept:
            old.unlink()
            print(f"− حُذفت ختمة قديمة: {old.name}")


if __name__ == "__main__":
    main()
