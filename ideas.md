# Ideas log — Quran Fagr

---

## 2026-05-28 — original idea
Daily تدبّر workflow currently done by hand: ask Gemini (web UI) a fixed question about a
surah, copy the answer into a per-surah tab in a Google Doc (`fagr.docx`) on Drive. Want
to automate: ask → wait for full answer → save to the right surah → repeat for the next
surah. Concern: not "wasting tokens" on the API.

## 2026-05-28 — clarification: avoid API, use browser/keyboard automation
First instinct was to skip the API entirely and automate the browser/keyboard: preset the
questions (maybe as Excel columns), drive gemini.google.com, copy the response, parse it
into the right place in the `.docx`.

## 2026-05-28 — evolved: the API is free, so use it
Key reframe — the Gemini API has a free tier; 114 surahs = 114 requests, well inside the
free daily quota, so it costs $0. Browser automation is the same $0 but far more fragile
(UI changes, bot detection, account risk, unreliable "answer finished" detection, and the
hardest part — injecting into the correct Google Docs tab). Decided: **free API key**.

## 2026-05-28 — evolved: Markdown-per-surah instead of Docs tabs
Save each answer as `NNN-name.md` (e.g. `002-البقرة.md`) instead of writing back into Doc
tabs. Opens in Obsidian (primary app), sorts in surah order, easy to aggregate, local.
Keep Google Docs as an *export* target (combine → pandoc → docx → Drive) for sharing —
the "both" path. Fixed the old doc's inconsistent naming (`"البقرة 2"`, `"3 ال عمران"`…).

## 2026-05-28 — evolved: enforce a fixed structure for aggregation
`prompt.md` forces every surah to use the same H2 headings, including dedicated
`ملاحظات بلاغية` and `ملاحظات نحوية ولغوية` sections + ayah-based H3 subheaders. This makes
`aggregate.py` able to pull all بلاغة/نحو notes across surahs into two master reference
files — the "تجميع التقسيمات البلاغية واللغوية" goal.

## 2026-05-28 — open: questions as Excel
Could later move the single question into `questions.xlsx` (one row per preset question)
so several questions can be asked per surah without touching code. Not needed for v1.

## 2026-05-29 — evolved: two-section site + Excel-driven daily notes
Reorganized the MkDocs sidebar into two main sections (awesome-pages plugin + folders):
**تدبر السور** (auto-generated, `surahs/quran/`) and **مشاركات حلقة الفجر** (manual,
`surahs/fajr/`). The manual notes are authored in `fajr-notes.xlsx` (columns: القسم/
التاريخ/العنوان/المحتوى/المرجع) and `build_notes.py` turns each القسم value into a
subsection page — dynamic categories, self-maintaining nav. This realizes the "تدبرات
حلقة الفجر اليومية" idea: a shared, browsable record of what the circle discusses.

## 2026-05-29 — evolved: publish the site to share with friends
Site is a static folder. Plan: GitHub Pages via `mkdocs gh-deploy` for a permanent free
public URL; `mkdocs serve -a 0.0.0.0` for same-Wi-Fi sharing during the circle; Cloudflare
Tunnel for an instant temporary public link. Public-internet tradeoff acknowledged.
DONE: published at https://johanliebert66.github.io/quran-fagr/ (repo JohanLiebert66/quran-fagr).

## 2026-05-29 — automated daily generation (quota-aware)
Windows Scheduled Task `quran-fagr-daily` runs `daily-update.ps1` at 11:00 (after the
~10:00 Cairo free-tier reset), `StartWhenAvailable` so it catches up if the PC was off.
Each run: contemplate.py (resume, ~20 surahs, stop on quota) → aggregate.py → mkdocs
gh-deploy. Never overwrites existing surahs. Disable once all 114 are done.

## 2026-05-29 — decided: Fajr notes in Markdown, not Excel
For quick on-the-fly capture + relate-later, editing Markdown (in Obsidian, the user's
main app) beats Excel: lower friction, mobile-friendly, native #tags and links. So
`surahs/fajr/*.md` are hand-edited; `build_notes.py`/Excel kept only as an optional bulk
importer (and excluded from the daily task so it can't clobber hand edits).

## 2026-05-29 — tagging/linking convention
- Topic: inline `#توحيد` etc. → found via full-text search.
- Surah/verse: Markdown link `[البقرة](../quran/002-البقرة.md)` → clickable + searchable.
- Page-level `tags:` frontmatter → listed on the الوسوم index (Material tags plugin, 9.7
  in-page marker `<!-- material/tags -->`, not the deprecated `tags_file`).

## 2026-06-09 — second tadabbur tab + per-surah verses skeletons
Added a parallel surah-analysis tab **«تدبر السور ٢»** (`surahs/quran2/`) — same
per-surah-page idea as `quran/` but a different model/source/structure; registered in
`surahs/.pages` right after `quran`, with `.pages` (title) + placeholder `index.md` so
the build doesn't break before the 114 files are dropped in. The 114 `NNN-اسم.md`
files are copied in manually (no badge, like the `quran/` tab).
Also scaffolded a **skeleton per surah in `surahs/verses/`** (all 114; existing
002/006/043 preserved) — each file = H1 `NNN — اسم` + an HTML-comment template ready
to fill, classifying notes by tag: `#تدبر` (تأمل) vs `#سؤال` (سؤال). The Obsidian
Templater `verse-note.md` now prompts note type (تدبّر/سؤال) and prepends the tag.
Generator: `scripts/scaffold_new_tab.py` (idempotent, never overwrites). Build passes
`mkdocs build --strict`.
