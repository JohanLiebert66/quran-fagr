# Resources — Quran Fagr

## Gemini API (Google AI Studio)
- **URL**: https://aistudio.google.com/apikey
- **Type**: API
- **Cost**: #cost/freemium (free tier = ~20 requests/day on 2.5-flash → 114 surahs over ~6 days; or switch model / enable billing)
- **Format**: #format/api #format/python
- **Projects**: #project/quran-fagr
- **Status**: #status/in-use
- **Notes**: Free key from AI Studio. Model `gemini-2.5-flash` for the run; `gemini-2.5-pro`
  for deeper analysis (smaller free quota). Rate limit ~15 req/min on free tier → 5s pause
  between calls. This is the engine for `contemplate.py`.

## google-genai (Python SDK)
- **URL**: https://pypi.org/project/google-genai/
- **Type**: library
- **Cost**: #cost/free
- **Format**: #format/python
- **Projects**: #project/quran-fagr
- **Status**: #status/in-use
- **Notes**: Official unified SDK. `from google import genai; client = genai.Client(api_key=...)`
  then `client.models.generate_content(model=..., contents=...)`. `pip install google-genai`.

## Pandoc
- **URL**: https://pandoc.org
- **Type**: tool
- **Cost**: #cost/free
- **Format**: CLI
- **Projects**: #project/quran-fagr
- **Status**: #status/discovered
- **Notes**: Converts the combined Markdown to `.docx` for upload to Google Drive.
  `pandoc surahs/_combined.md -o quran-fagr.docx`. H1-per-surah becomes the doc outline.

## MkDocs Material
- **URL**: https://squidfunk.github.io/mkdocs-material/
- **Type**: tool / library
- **Cost**: #cost/free
- **Format**: #format/python #format/webapp
- **Projects**: #project/quran-fagr
- **Status**: #status/discovered
- **Notes**: Optional display surface — turns the per-surah Markdown into a searchable
  static site. Needs RTL CSS for Arabic. Python-based, fits the toolchain.

## Obsidian
- **Cost**: #cost/free | **Status**: #status/in-use
- **Notes**: Primary display surface. Point a vault at `surahs/`. RTL renders well; outline
  + Dataview can auto-build index views. No extra tooling needed.
