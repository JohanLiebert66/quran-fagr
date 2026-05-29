# Context — Quran Fagr

## Goal

A daily, repeatable workflow: for each surah, ask one fixed تدبّر question to an LLM,
save the answer in a per-surah location named by **number + name**, then be able to
(a) collect all rhetorical (بلاغة) and grammatical (نحو) notes across surahs, and
(b) display everything nicely.

## What the original `fagr.docx` looked like (analysis)

Exported from Google Docs → one flat `.docx` (653 paragraphs, 107 headings). Google
Docs "tabs" collapse into a single document on export. The top level mixed two axes:

- **Category tabs:** كتاباتي / أسئلة / لغة / لفتات / سيرة / سور / تجويد
- **Per-surah tabs:** البقرة، آل عمران، النساء، المائدة، الأنعام، الكهف، القلم، نوح، الإنسان

Problems found:

1. **Inconsistent surah naming** — `"البقرة 2"`, `"3 ال عمران"`, `"الأنعام 6"`, and some
   with no number (`"القلم"`, `"نوح"`). No sortable convention.
2. **Duplication** — الأنعام and the "ترتيب الأنبياء" analysis each appear twice; several
   empty headings (e.g. paragraphs 43, 64, 65, 72).
3. **Heading-level drift** — the same logical level is `H1` in one surah and `H2` in
   another, so no uniform template could be parsed or rendered.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| LLM access | **Free Gemini API key** | $0. Robust, returns clean Markdown, runs unattended, avoids browser-automation fragility/account-risk. ⚠️ Free tier = **~20 req/day** on 2.5-flash (observed 2026-05-29), so 114 surahs span ~6 days of resumable runs — not one session. |
| Model | `gemini-2.5-flash` | On the free tier; fast and good enough. Switch to `gemini-2.5-pro` for deeper analysis (smaller free quota). |
| Output | **One Markdown file per surah** (`NNN-name.md`) | Opens in Obsidian (primary app), trivial to aggregate, version-able, local/offline. |
| Naming | `NNN-name`, zero-padded | `002-البقرة.md`, `003-آل-عمران.md` … sorts in surah order automatically. Fixes the inconsistency in the old doc. |
| Structure | Fixed H2 skeleton enforced by `prompt.md` | Every surah identical → aggregation by section is reliable, display is uniform. |
| Docs sync | Markdown → `combine.py` → pandoc → docx → Drive | "Both" path: clean automation in Markdown, shareable Google Doc when wanted. |
| Questions source | `prompt.md` (editable) | Edit the question without touching code. Can later move to `questions.xlsx` if you want several preset questions. |

## The fixed per-surah structure (enforced in `prompt.md`)

```
## المقصد الرئيسي
## الموضوع الرئيسي
## المواضيع الفرعية وعلاقتها
## الترابط مع ما قبلها
## الترابط مع ما بعدها
## السرد القصصي المترابط (مجموعة السور)
## التقسيم حسب الآيات      ← ### الآيات 1–7: ... (subheaders by ayah)
## ملاحظات بلاغية          ← collected by aggregate.py
## ملاحظات نحوية ولغوية    ← collected by aggregate.py
## لطائف ولفتات
```

Two output axes, both satisfied:
- **Vertical** (per surah): each `NNN-name.md`.
- **Horizontal** (across surahs): `aggregate.py` pulls the بلاغة and نحو sections into
  `_تجميع-بلاغة.md` and `_تجميع-نحو.md`. This is the "تجميع التقسيمات البلاغية واللغوية" the
  original workflow wanted — trivial in Markdown, painful in Google Docs.

## Why not browser automation (the first instinct)

It's the same $0 as the free API but: Gemini's web UI changes break selectors; Google
detects bots (CAPTCHAs / account flags); "wait until the answer finished" is hard to
detect in a streaming UI; copying rich HTML cleanly is unreliable; and injecting each
answer into the *correct Google Docs tab* is the single most fragile step. The free API
removes all of that. (The one case for browser automation: you pay for Gemini Advanced
and specifically want that model instead of the free-tier API model.)

## Display options considered

1. **Obsidian** — primary app; RTL renders well; folding + outline + Dataview can build
   index views automatically. Zero extra tooling.
2. **MkDocs Material** — Markdown → searchable static site (free, Python). Best for a
   polished browsable presentation; needs `dir="rtl"` CSS for Arabic.
3. **Quartz** — Obsidian → website, but JS-based (against the Python-first preference).
4. **PDF via Pandoc** — single book-like artifact.
5. **Google Docs** — kept for sharing via Drive (the "sync" half of the chosen path).

## Site structure — two main sections (2026-05-29)

The MkDocs left sidebar is organized into two top-level sections via the
**awesome-pages** plugin + folder structure (no hand-maintained `nav:`):

- **تدبر السور** (`surahs/quran/`) — all auto-generated surah analyses + the two
  `_تجميع-*` cross-surah pages. Files auto-included, ordered by `NNN` prefix.
- **مشاركات حلقة الفجر** (`surahs/fajr/`) — manually-curated daily notes, one page per
  category (subsection): فوائد لغوية، فوائد بلاغية، تجويد، أسئلة وأجوبة، فوائد فقهية، …

`docs_dir` stays `surahs/`; `surahs/.pages` sets top-level order; each section folder has
a `.pages` with its Arabic `title`. New surahs or new note-categories appear automatically.

### Manual notes pipeline (Excel-driven)
Source of truth = **`fajr-notes.xlsx`** (project root), columns: القسم / التاريخ / العنوان /
المحتوى / المرجع. `build_notes.py` groups rows by القسم and writes one page per category
into `surahs/fajr/`, regenerating `surahs/fajr/.pages` for nav order. Categories are
**dynamic** — a new value in القسم makes a new subsection; removing all rows of a category
deletes its page. Chosen because the user prefers editing a list/sheet over Markdown for
daily entries, and it keeps the section self-maintaining.

### Sharing decision
Site is a static `site/` folder. Recommended: **GitHub Pages via `mkdocs gh-deploy`** (free,
permanent, public URL). Quick options: `mkdocs serve -a 0.0.0.0:8000` (same Wi-Fi) or a
Cloudflare Tunnel (instant public link). Public-internet caveat noted; `.env` is gitignored
so the API key never ships. Full how-to in `README.md`.

## Open / next

- First real run: `python contemplate.py 1 5` to sanity-check quality, then tune
  `prompt.md` before running all 114.
- Decide final display surface (Obsidian vs MkDocs) after seeing a few generated files.
- Optional: migrate the question into `questions.xlsx` if multiple preset questions are
  wanted per surah.
