# DocBench — a pure-Python PDF / Office / Image toolkit

A self-hosted,toolkit built entirely in Python (Flask backend,
no external frameworks). Every tool runs in-memory, no uploaded file is ever
written to permanent storage, which makes it safe to run in a stateless
serverless environment.

o
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
https://doc-bench-the-file-tool-kit.vercel.app/
