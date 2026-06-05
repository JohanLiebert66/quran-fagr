# Quran Fagr — تدبر القرآن آليًا

Automate a daily Quran-contemplation workflow: ask the same تدبّر question for each
surah via the **free Gemini API**, save each answer as its own Markdown file
(number + name), then aggregate the بلاغة/نحو notes and (optionally) export the
whole thing to a Google Doc.

## Status & features (updated 2026-06)

Surah generation is automated (see the daily task below). The site has since gone
through a two-phase redesign — all on the existing **MkDocs/Python** stack:

- **Note validation** — `validate_notes.py` checks each note's date, internal links,
  and surah refs; runs on every pull request (`validate.yml`) **and** before each
  deploy, so a broken note blocks publishing. It also warns on likely tag typos.
- **Note-type chips** — every note shows a نوع chip (تأمل / لغة / بلاغة / فقه / تجويد /
  سؤال) derived from its location, via the MkDocs hook `scripts/hooks/note_types.py`.
- **Ayah timeline** — verse pages render as a khatmah-aware vertical timeline
  (ختمة badges + cycle separators).
- **Tag system** — curated vocabulary page (`معجم الوسوم`), a "notes by tag" index
  (`الملاحظات حسب الوسم`) with **clickable** tag chips.
- **Reading mode** — a floating 📖 button toggles a focused, larger-text view.
- **Cross-khatmah comparison** — `مقارنة التدبر` stacks an ayah's reflections across
  cycles to compare how understanding evolved.
- **Authoring** — an Obsidian **Templater** kit in `obsidian-templates/` (offline ayah
  lookup) writes the exact note format for you. See *Adding a note* below.

## Pipeline

```
prompt.md ──► contemplate.py ──► surahs/NNN-name.md   (one file per surah)
                                      │
                                      ├─► aggregate.py ─► surahs/_تجميع-بلاغة.md
                                      │                    surahs/_تجميع-نحو.md
                                      └─► combine.py   ─► surahs/_combined.md ─(pandoc)─► quran-fagr.docx ─► Google Drive
```

## Folder layout

```
quran-fagr/
├── README.md            ← this file
├── context.md           ← analysis of the old doc, organization plan, decisions
├── ideas.md             ← dated idea log (append-only)
├── resources.md         ← tools/APIs used by this project
├── environment.yml      ← conda environment (primary setup)
├── mkdocs.yml           ← MkDocs Material site config (RTL/Arabic, awesome-pages, tags)
├── daily-update.ps1     ← runs daily via Task Scheduler: generate batch → aggregate → deploy
├── .env                 ← your GEMINI_API_KEY (gitignored — paste your key here)
├── .gitignore
├── fagr.docx            ← the original Google Doc export (reference only; gitignored)
├── fajr-notes.xlsx      ← OPTIONAL Excel input for notes (Markdown editing is recommended)
├── logs/                ← daily-task logs (gitignored)
├── scripts/
│   ├── surahs.py          ← the 114 surahs (number + name) — shared reference data
│   ├── prompt.md          ← the تدبّر question + the fixed output structure (edit freely)
│   ├── contemplate.py     ← Gemini → one Markdown file per surah (→ surahs/quran/)
│   ├── aggregate.py       ← collect بلاغة/نحو across surahs (→ surahs/quran/_تجميع-*.md)
│   ├── validate_notes.py  ← validate note metadata (CI gate); warns on tag typos
│   ├── tag_vocabulary.py  ← approved tags + tag_anchor() (source of truth)
│   ├── khatmas_registry.py← date → khatmah lookup (shared by hook + builders)
│   ├── build_surah_index.py / build_khatmas.py / build_whatsnew.py
│   ├── build_tags_doc.py  ← → معجم-الوسوم.md   build_tags_index.py ← → الملاحظات-حسب-الوسم.md
│   ├── build_ayah_compare.py ← → مقارنة-التدبر.md (cross-khatmah)
│   ├── note.py            ← prints a ready metadata line for a note
│   ├── hooks/note_types.py← MkDocs hook: type/khatmah chips, timeline, tag links
│   ├── build_notes.py     ← OPTIONAL: fajr-notes.xlsx → category pages (overwrites them)
│   ├── combine.py / requirements.txt
├── obsidian-templates/    ← Templater note templates + offline ayah JSON (NOT published)
└── surahs/                ← MkDocs docs_dir
    ├── index.md           ← home page
    ├── tags.md            ← الوسوم — the tag index (Material plugin)
    ├── معجم-الوسوم.md / الملاحظات-حسب-الوسم.md / مقارنة-التدبر.md  ← generated
    ├── notes-by-surah.md / whats-new.md  ← generated
    ├── stylesheets/extra.css   javascripts/reading-mode.js
    ├── quran/             ← "تدبر السور": 001-*.md … + _تجميع-*.md (generated)
    ├── fajr/              ← "مشاركات حلقة الفجر": one .md per category (edit these)
    ├── verses/            ← per-ayah notes: NNN-name.md (timeline pages)
    └── khatmas/           ← per-khatmah pages (registry in khatmas/index.md)
```

### Site navigation (left sidebar)

```
الرئيسية
تدبر السور                     ← main section (generated)
  ├─ 001 — سورة الفاتحة          ← subsection per surah
  ├─ … (114 surahs)
  ├─ تجميع: ملاحظات بلاغية
  └─ تجميع: ملاحظات نحوية ولغوية
مشاركات حلقة الفجر              ← main section (your manual notes)
  ├─ فوائد لغوية                 ← subsection per category
  ├─ فوائد بلاغية
  ├─ تجويد
  ├─ أسئلة وأجوبة
  └─ فوائد فقهية   (add more anytime — new categories appear automatically)
```

## Setup (one time, conda)

1. Get a **free** API key: https://aistudio.google.com/apikey
2. Paste it into `.env` (already created):
   ```
   GEMINI_API_KEY=your-key-here
   ```
3. Create and activate the conda environment (installs python, pandoc, the Gemini SDK,
   python-dotenv, and MkDocs Material):
   ```powershell
   conda env create -f environment.yml
   conda activate quran-fagr
   ```

## Run

```powershell
conda activate quran-fagr
cd scripts

python contemplate.py            # all surahs not done yet (auto-resume)
python contemplate.py 18         # just surah 18 (الكهف)
python contemplate.py 1 10       # surahs 1–10
python contemplate.py --force 2  # regenerate surah 2 even if it exists

python aggregate.py              # build the بلاغة + نحو master files
python combine.py                # build _combined.md for the Docs export
```

The script loads your key from `.env`, then **resumes**: already-saved surahs are skipped
unless `--force`.

> ⚠️ **Free-tier limit:** `gemini-2.5-flash` allows only **~20 requests/day**. So the full
> Quran takes **~6 days** — just run the same command once a day and it picks up from the
> first missing surah. When the daily quota is hit, the script **stops immediately** (it
> detects the daily-quota 429, so no pointless retries) and tells you to resume later.
> To finish faster: switch `MODEL` in `contemplate.py` to a model with a larger free
> allowance (e.g. `gemini-2.5-flash-lite` — check current limits), or enable billing.

## Adding a note — three ways

Every note is one block: a heading (`## آية N` for verse notes, or `## عنوان` for
fajr notes), an optional ayah quote, a **metadata line**, then your text:

```markdown
## آية 255:
> "ٱللَّهُ لَآ إِلَٰهَ إِلَّا هُوَ ٱلْحَىُّ ٱلْقَيُّومُ"

*2026-06-05 · #توحيد · [البقرة:255](../quran/002-البقرة.md)*
نص التأمّل…
```

The metadata line is what powers the type chip, ختمة badge, timeline, and tag links,
so keep its shape: `*التاريخ · #وسوم · [السورة:الآية](../quran/NNN-name.md)*`.
Multi-word tags: join with a hyphen (e.g. `#حجج-باطلة`). Paste new blocks at the **top**
(newest first).

**1. Obsidian + Templater — easiest (desktop).** Open the target file in
`surahs/verses/` or `surahs/fajr/`, run *Templater: Insert template* → `verse-note`,
and answer surah № / ayah № / tags. The block — including the ayah text from an offline
copy — is written for you. One-time setup and usage in
[obsidian-templates/README.md](obsidian-templates/README.md).

**2. GitHub web editor — any device.** On https://github.com/JohanLiebert66/quran-fagr →
open the file (or **Add file → Create new file** named `NNN-name.md` under
`surahs/verses/`) → **✏️ Edit** → paste a block in the format above → **Commit**. It's
validated and auto-deploys in ~2 min. (No Templater on the web, so type the metadata
line yourself using the shape above.)

**3. Plain Markdown — local.** Edit the file in any editor, then publish (see *Edit any
page & publish* below). `validate_notes.py` lets you check before pushing:
`python scripts/validate_notes.py`.

## Fajr notes — write in Markdown (recommended)

Each category under **مشاركات حلقة الفجر** is a plain Markdown file in `surahs/fajr/`.
**Capture notes by editing these files directly** (ideally in Obsidian — fast, works on
mobile). This is recommended over Excel for on-the-fly note-taking.

- **Add a note:** open the category file (e.g. `surahs/fajr/فوائد-لغوية.md`) and paste a
  block at the top:
  ```markdown
  ## عنوان الفائدة
  *2026-05-29 · #توحيد #رحمة · متعلّقة بـ [البقرة](../quran/002-البقرة.md)*

  نص الملاحظة…
  ```
- **New category** = create a new file, e.g. `surahs/fajr/سيرة.md` with a `# سيرة` heading.
  It appears in the sidebar automatically (alphabetical).

### Linking & tagging (so you can search and relate later)
- **Topic tag** — write `#توحيد` `#رحمة` anywhere in the note. Find it later via the
  site's **search box** 🔍 (it indexes the full text, including these inline tags).
- **Link to a surah/verse** — a normal Markdown link to that surah's page:
  `[البقرة ٢٥٥](../quran/002-البقرة.md)`. It's **clickable** on the site and searchable.
  General notes just carry `#tags`; surah-specific notes add the link too.
- **Tag index page** — add `tags:` in a page's frontmatter (see `فوائد-لغوية.md`) and that
  page is listed on the **الوسوم** page for browsing by topic.

### Optional: bulk-enter notes via Excel
If you'd rather type notes in a spreadsheet, `scripts/build_notes.py` reads `fajr-notes.xlsx`
(columns القسم / التاريخ / العنوان / المحتوى / المرجع) and generates the category pages.
⚠️ It **overwrites** the pages it manages — so for any given category, pick *either*
hand-edited Markdown *or* Excel, not both. (`python build_notes.py --init` creates the
template; `python build_notes.py` regenerates.) The daily auto-task does **not** run it,
so your hand-edited notes are safe.

## Display — MkDocs site (chosen)

A searchable, RTL Arabic website built from the per-surah Markdown:

```powershell
conda activate quran-fagr
mkdocs serve     # live preview at http://127.0.0.1:8000
mkdocs build     # static site into ./site/ (gitignored)
```

`mkdocs.yml` uses `docs_dir: surahs`, so the generated `NNN-name.md` files (plus the
`_تجميع-بلاغة.md` / `_تجميع-نحو.md` aggregates) become the site pages, ordered by surah
number. `surahs/index.md` is the home page. Run `aggregate.py` before building so the
بلاغة/نحو index pages are up to date.

### Other display options (still available)
- **Obsidian** — point a vault at `surahs/`; RTL + outline work out of the box.
- **Google Doc** — `combine.py` → `pandoc _combined.md -o quran-fagr.docx` → upload
  to Drive. The H1-per-surah outline acts like tabs for navigation.

## Edit any page & publish — the everyday workflow

Every page on the site is a Markdown file under `surahs/`:

| To change… | Edit this file |
|------------|----------------|
| A surah's analysis | `surahs/quran/NNN-name.md` |
| A Fajr-notes category | `surahs/fajr/<category>.md` |
| A per-verse note | `surahs/verses/NNN-name.md` (one H2 per verse) |
| A khatma | the table in `surahs/khatmas/index.md` |
| The home page | `surahs/index.md` |

### Edit from any device — GitHub web editor (auto-deploys)

Open https://github.com/JohanLiebert66/quran-fagr on phone or browser →
navigate to the file → **✏️ Edit** → write Markdown → **Commit**.

A **GitHub Actions workflow** ([.github/workflows/deploy.yml](.github/workflows/deploy.yml))
auto-triggers on every push to `main`:
- **Validates notes** (`validate_notes.py`) — a broken date/link/ref fails the build.
- Refreshes derived pages: `aggregate.py`, `build_surah_index.py`, `build_khatmas.py`,
  `build_whatsnew.py`, `build_tags_doc.py`, `build_tags_index.py`, `build_ayah_compare.py`.
- Builds and deploys to `gh-pages`.

A second workflow ([.github/workflows/validate.yml](.github/workflows/validate.yml)) runs
the note validator on every **pull request**, so problems show up before merging.

So edits from the web editor become live on
[the site](https://johanliebert66.github.io/quran-fagr/) within ~2 minutes, **no
local action required**. Status of any run: the repo's **Actions** tab.

### Edit locally — the 3-step flow

```powershell
conda activate quran-fagr
# 1. edit the .md file(s) …
python -m mkdocs serve          # 2. (optional) preview at http://127.0.0.1:8000 — live-reloads
python -m mkdocs gh-deploy --remote-name origin   # 3. publish → live in ~1 min
```

- There's no live sync: changes appear online only after `gh-deploy` (local) or after
  pushing to `main` (GitHub web editor). `mkdocs serve` is a *local* preview that reloads
  instantly as you type.
- Hand-edits to surah pages are **safe** — `contemplate.py` skips files that already exist;
  only `contemplate.py --force <n>` regenerates (and overwrites) a surah.

## Automated daily surah generation

A Windows Scheduled Task **`quran-fagr-daily`** runs [daily-update.ps1](daily-update.ps1)
every day at **11:00** (just after the free-tier quota resets ~10:00 Cairo). Each run:
resumes from the first missing surah → generates ~20 → refreshes the aggregates →
`gh-deploy`s the site. It **never overwrites** existing surahs.

- **Catch-up:** if the PC is off at 11:00, it runs as soon as you next log in
  (`StartWhenAvailable`).
- **Logs:** `logs/daily-YYYY-MM-DD.log` (gitignored).
- **Run it now manually:** `powershell -File daily-update.ps1`
- **Change the time:**
  `Set-ScheduledTask quran-fagr-daily -Trigger (New-ScheduledTaskTrigger -Daily -At 7:00pm)`
- **Disable / remove** (e.g. once all 114 are done):
  `Disable-ScheduledTask quran-fagr-daily`  or  `Unregister-ScheduledTask quran-fagr-daily -Confirm:$false`

## Share the site with friends

`mkdocs build` produces a plain static `site/` folder (just HTML/CSS/JS) — host it
anywhere. Options, easiest first:

1. **Instant, no deploy — local network.** While at the same Wi-Fi (e.g. the Fajr circle):
   ```powershell
   mkdocs serve -a 0.0.0.0:8000
   ```
   Friends open `http://<your-PC-IP>:8000` (find your IP with `ipconfig`). Off when you close it.

2. **Instant public link — Cloudflare Tunnel.** A temporary public URL to your local server,
   no account/host needed:
   ```powershell
   mkdocs serve            # in one terminal
   cloudflared tunnel --url http://localhost:8000   # in another → gives a public *.trycloudflare.com link
   ```
   Great for quick sharing; link lives only while it runs.

3. **Permanent free hosting — GitHub Pages (recommended).** One command publishes the built
   site to a free public URL `https://<username>.github.io/<repo>/`:
   ```powershell
   # one-time: git init, create a GitHub repo, push
   mkdocs gh-deploy        # builds + pushes to the gh-pages branch
   ```
   Re-run `mkdocs gh-deploy` anytime to update. (Free GitHub Pages is **public**.)

   Alternatives in the same vein: **Cloudflare Pages** / **Netlify** (connect the repo, auto-build
   on push, free, custom domain optional).

> Privacy note: options 2 & 3 put the site on the public internet. The content is study
> notes, so that's usually fine — but if you want it private, keep to option 1, or use
> Cloudflare Access / a password-protected host. Your API key is in `.env` (gitignored),
> so it never ships with the site.

See `context.md` for the reasoning behind every choice.
