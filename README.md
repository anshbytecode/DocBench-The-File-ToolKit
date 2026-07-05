# DocBench — a pure-Python PDF / Office / Image toolkit

A self-hosted,toolkit built entirely in Python (Flask backend,
no external frameworks). Every tool runs in-memory, no uploaded file is ever
written to permanent storage, which makes it safe to run in a stateless
serverless environment.

## Tools included (21)

| Category | Tools |
|---|---|
| Organize | Merge PDF, Split PDF, Organize (reorder/delete pages) |
| Optimize | Compress PDF, Repair PDF, Image Compressor |
| Convert | PDF↔Word, PDF↔PowerPoint, PDF↔Excel, HTML→PDF, PDF→JPG, JPG→PDF |
| Edit | Watermark, Rotate, Page numbers, Crop |
| Security | Redact, Protect (password), Unlock |
| Intelligence | Compare PDF (text diff) |

The included `vercel.json` + `api/index.py` route all traffic to the Flask
app (`@vercel/python` runtime auto-detects the WSGI `app` object). Flask
serves its own `/static` assets, so no separate static build step is needed.

**Before you deploy, know these Vercel constraints:**
- **Package size**: PyMuPDF alone is ~65 MB unzipped; with pikepdf, Pillow,
  reportlab, etc. the deployed function lands around 100–130 MB. Vercel's
  Hobby plan allows up to 250 MB unzipped per function, so this fits — but
  leaves less room if you add more dependencies later.
- **Execution timeout**: Hobby plan functions time out at 10s (60s on Pro).
  Compressing/converting large multi-page PDFs can exceed 10s — upgrade to
  Pro or reduce `MAX_CONTENT_LENGTH` in `app.py` if you hit this.
- **Request body size**: Vercel serverless functions cap request bodies
  around 4.5 MB on some plans. `app.py` sets its own 20 MB cap — align this
  with whatever your Vercel plan actually allows, or users seeing large
  uploads silently fail.
- **No persistent disk**: `/tmp` is writable but wiped between invocations.
  This project already avoids relying on it except as a short-lived scratch
  space for `pdf2docx` (which needs real file paths), and cleans up after itself.

### Netlify (not recommended for this project)

Netlify does not have first-class Python function support the way Vercel
does. A `netlify/functions/app.py` wrapper (using `serverless-wsgi`) and
`netlify.toml` are included for completeness, but expect to hit:
- Smaller function bundle limits than Vercel, which is tight against
  PyMuPDF's size.
- A default 10s function timeout (26s max even on paid plans).
- Less mature tooling around Python native dependencies (`pikepdf`,
  `PyMuPDF` both ship compiled C extensions).

If you specifically want Netlify, add `serverless-wsgi` to requirements and
test each tool individually — some of the larger conversions may need to be
disabled or moved elsewhere.

### If you need heavier/more accurate conversions later

The Word/Excel/PowerPoint ↔ PDF conversions here are **pure-Python
re-renders** — good for text, tables, and images, but not pixel-perfect for
complex layouts, because no serverless platform gives you a LibreOffice or
MS Office engine to shell out to. For production-grade fidelity (or to add
OCR via Tesseract, or true digital signing), the standard approach is to run
this same Flask app in a **Docker container on Render, Railway, Fly.io, or
a small VM**, with `libreoffice-writer`, `libreoffice-impress`, and
`tesseract-ocr` installed via apt — then swap in `subprocess` calls to
`soffice --headless --convert-to pdf` for those specific routes. Everything
else in this project stays the same.

## Project structure

```
app.py                  Flask app: tool registry + routes
utils/pdf_tools.py       PDF-native operations (merge, split, compress, etc.)
utils/office_tools.py    Word/Excel/PowerPoint/HTML -> PDF (pure-Python renders)
utils/image_tools.py     Image compression, image <-> PDF
templates/               Jinja2 templates (homepage + generic tool page)
static/                  CSS + vanilla JS (drag-drop upload, fetch, download)
api/index.py             Vercel entry point
netlify/functions/app.py Netlify entry point (alternative)
test_smoke.py            End-to-end test covering all 21 tools
```

## Security notes

- Files are processed entirely in memory (`BytesIO`) and discarded after
  the response is sent — nothing is written to a database or persistent disk.
- `protect-pdf` / `unlock-pdf` use PDF standard encryption via `pypdf`. This
  is suitable for casual access control, not for protecting highly sensitive
  documents against a determined attacker.
- `redact-pdf` uses PyMuPDF's `apply_redactions()`, which truly removes the
  underlying text/image content (not just a black box drawn on top).
