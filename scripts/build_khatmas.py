# -*- coding: utf-8 -*-
"""
build_khatmas.py — يُنشئ صفحة لكل ختمة في `surahs/khatmas/` تجمع الملاحظات
(من تدبر الآيات ومشاركات حلقة الفجر) مقسمة هيكلياً:
اليوم (الجلسة) -> السورة (بترتيب المصحف) -> الآيات تصاعدياً.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from khatmas_registry import parse_registry, in_range
from surahs import BY_NUMBER

PROJECT = Path(__file__).resolve().parent.parent
SURAHS = PROJECT / "surahs"
KHATMAS = SURAHS / "khatmas"
REGISTRY = KHATMAS / "index.md"

NOTE_DIRS = [SURAHS / "fajr", SURAHS / "verses"]
QURAN = SURAHS / "quran"

DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
HEAD_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
SURAH_LINK_RE = re.compile(r"\[([^:\]]+)(?::(\d+))?\]\((?:\.\./)?quran/(\d{3})-[^)]+\.md\)")
AYAH_TITLE_RE = re.compile(r"آية\s*(\d+)")


def slug(name: str) -> str:
    return name.strip().replace("/", "-").replace(" ", "-")


def collect_notes() -> list[dict]:
    """يُعيد قائمة بالملاحظات متضمنة التاريخ، السورة، ورقم الآية."""
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
            text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
            text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
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
                surah_num = 999
                surah_name = "مشاركات عامة"
                ayah_num = 0

                raw_head = h.group(1).strip()
                id_m = re.search(r"\{:\s*#([^\s}]+)\s*\}", raw_head)
                anchor = id_m.group(1) if id_m else ""
                clean_title = re.sub(r"\{:\s*#([^\s}]+)\s*\}", "", raw_head).strip()

                for j, line in enumerate(lines[:5]):
                    mm = DATE_RE.search(line)
                    if mm and line.strip().startswith("*") and line.strip().endswith("*"):
                        dt = date(int(mm.group(1)), int(mm.group(2)), int(mm.group(3)))

                        # استخراج السورة والآية من سطر الميتاداتا
                        sm = SURAH_LINK_RE.search(line)
                        if sm:
                            surah_num = int(sm.group(3))
                            surah_name = BY_NUMBER.get(surah_num, sm.group(1).strip())
                            ayah_num = int(sm.group(2)) if sm.group(2) else 0

                        # snippet = أول سطر نصّي بعد الـ metadata، يتجاهل blockquote
                        for k in range(j + 1, min(len(lines), j + 5)):
                            cand = lines[k].strip()
                            if cand and not cand.startswith(">") and not cand.startswith("#"):
                                snippet = cand[:140]
                                break
                        break

                if not dt:
                    continue

                # إذا لم تُستنتج السورة من الرابط، وكان الملف في verses
                if surah_num == 999 and page.parent.name == "verses":
                    fn = page.stem
                    if fn[:3].isdigit():
                        surah_num = int(fn[:3])
                        surah_name = BY_NUMBER.get(surah_num, fn[4:])
                    am = AYAH_TITLE_RE.search(clean_title)
                    if am:
                        ayah_num = int(am.group(1))

                if not anchor and ayah_num and page.parent.name == "verses":
                    anchor = str(ayah_num)

                rel = page.relative_to(SURAHS).as_posix()
                label = page.relative_to(SURAHS).parts[0]   # "fajr" أو "verses"
                label_ar = {"fajr": "مشاركات الفجر", "verses": "تدبر آية"}.get(label, label)
                out.append({
                    "date": dt,
                    "rel": rel,
                    "anchor": anchor,
                    "label": label_ar,
                    "title": clean_title,
                    "snippet": snippet,
                    "surah_num": surah_num,
                    "surah_name": surah_name,
                    "ayah_num": ayah_num,
                })
    return out


def write_khatma_page(k: dict, notes: list[dict]) -> Path:
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
    ]
    if not notes:
        lines.append("## الملاحظات")
        lines.append("")
        lines.append("*لا توجد ملاحظات في هذه المدّة بعد.*")
    else:
        # ترتيب الأيام زمنياً (تصاعدياً مع سير الختمة من الفاتحة إلى الناس)
        unique_dates = sorted(set(n["date"] for n in notes))
        for d in unique_dates:
            day_notes = [n for n in notes if n["date"] == d]
            lines.append(f"## 🗓 جلسة: {d.isoformat()}")
            lines.append("")

            # تجميع ملاحظات اليوم حسب السورة بترتيب المصحف
            surahs_in_day = sorted(
                list(set((n["surah_num"], n["surah_name"]) for n in day_notes)),
                key=lambda x: x[0]
            )

            for s_num, s_name in surahs_in_day:
                if s_num < 900:
                    lines.append(f"### سورة {s_name} ({s_num:03d})")
                else:
                    lines.append(f"### {s_name}")
                lines.append("")

                # ترتيب الآيات تصاعدياً داخل السورة
                s_notes = sorted(
                    [n for n in day_notes if n["surah_num"] == s_num],
                    key=lambda x: (x["ayah_num"], x["title"])
                )

                for n in s_notes:
                    anchor_part = f"#{n['anchor']}" if n.get("anchor") else ""
                    link = f"../{n['rel']}{anchor_part}"
                    lines.append(f"- **[{n['title']}]({link})** — *{n['label']}*")
                    if n["snippet"]:
                        lines.append(f"    - {n['snippet']}")
                lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    KHATMAS.mkdir(parents=True, exist_ok=True)
    khatmas = parse_registry(REGISTRY)
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
