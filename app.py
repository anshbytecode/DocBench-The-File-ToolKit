
import io
import os
import traceback
from flask import Flask, render_template, request, send_file, jsonify, abort

from utils import pdf_tools, image_tools, office_tools

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  
TOOLS = {
    "merge-pdf": {
        "name": "Merge PDF", "category": "Organize",
        "desc": "Combine multiple PDFs into one, in the order you choose.",
        "accept": ".pdf", "multiple": True, "fields": [],
    },
    "split-pdf": {
        "name": "Split PDF", "category": "Organize",
        "desc": "Extract page ranges into separate PDF files (zipped).",
        "accept": ".pdf", "multiple": False,
        "fields": [{"name": "ranges", "label": "Page ranges (e.g. 1-3,5,7-9)", "type": "text"}],
    },
    "organize-pdf": {
        "name": "Organize PDF", "category": "Organize",
        "desc": "Reorder or delete pages by specifying the new page order.",
        "accept": ".pdf", "multiple": False,
        "fields": [{"name": "order", "label": "New page order (e.g. 3,1,2)", "type": "text"}],
    },
    "compress-pdf": {
        "name": "Compress PDF", "category": "Optimize",
        "desc": "Shrink file size by re-encoding embedded images.",
        "accept": ".pdf", "multiple": False,
        "fields": [{"name": "level", "label": "Compression level", "type": "select",
                     "options": ["low", "recommended", "extreme"]}],
    },
    "repair-pdf": {
        "name": "Repair PDF", "category": "Optimize",
        "desc": "Attempt to fix a corrupted or malformed PDF.",
        "accept": ".pdf", "multiple": False, "fields": [],
    },
    "pdf-to-word": {
        "name": "PDF to Word", "category": "Convert",
        "desc": "Convert PDF pages into an editable .docx file.",
        "accept": ".pdf", "multiple": False, "fields": [],
    },
    "pdf-to-powerpoint": {
        "name": "PDF to PowerPoint", "category": "Convert",
        "desc": "Turn each PDF page into a slide (image-based).",
        "accept": ".pdf", "multiple": False, "fields": [],
    },
    "pdf-to-excel": {
        "name": "PDF to Excel", "category": "Convert",
        "desc": "Extract tables from a PDF into an .xlsx workbook.",
        "accept": ".pdf", "multiple": False, "fields": [],
    },
    "word-to-pdf": {
        "name": "Word to PDF", "category": "Convert",
        "desc": "Convert a .docx document into PDF.",
        "accept": ".docx", "multiple": False, "fields": [],
    },
    "powerpoint-to-pdf": {
        "name": "PowerPoint to PDF", "category": "Convert",
        "desc": "Convert a .pptx presentation into PDF.",
        "accept": ".pptx", "multiple": False, "fields": [],
    },
    "excel-to-pdf": {
        "name": "Excel to PDF", "category": "Convert",
        "desc": "Convert an .xlsx spreadsheet into PDF.",
        "accept": ".xlsx", "multiple": False, "fields": [],
    },
    "html-to-pdf": {
        "name": "HTML to PDF", "category": "Convert",
        "desc": "Paste HTML markup and convert it into a PDF.",
        "accept": None, "multiple": False,
        "fields": [{"name": "html", "label": "HTML content", "type": "textarea"}],
    },
    "pdf-to-jpg": {
        "name": "PDF to JPG", "category": "Convert",
        "desc": "Render every PDF page as a JPG image (zipped).",
        "accept": ".pdf", "multiple": False,
        "fields": [{"name": "dpi", "label": "DPI (image quality)", "type": "number", "default": 150}],
    },
    "jpg-to-pdf": {
        "name": "JPG to PDF", "category": "Convert",
        "desc": "Combine one or more images into a single PDF.",
        "accept": "image/*", "multiple": True, "fields": [],
    },
    "compress-image": {
        "name": "Image Compressor", "category": "Optimize",
        "desc": "Reduce image file size by adjusting quality and width.",
        "accept": "image/*", "multiple": False,
        "fields": [
            {"name": "quality", "label": "Quality (1-95)", "type": "number", "default": 60},
            {"name": "max_width", "label": "Max width in px (optional)", "type": "number", "default": ""},
        ],
    },
    "watermark-pdf": {
        "name": "Watermark", "category": "Edit",
        "desc": "Stamp text over every page of a PDF.",
        "accept": ".pdf", "multiple": False,
        "fields": [
            {"name": "text", "label": "Watermark text", "type": "text", "default": "CONFIDENTIAL"},
            {"name": "opacity", "label": "Opacity (0-1)", "type": "number", "default": 0.3},
        ],
    },
    "rotate-pdf": {
        "name": "Rotate PDF", "category": "Edit",
        "desc": "Rotate all or specific pages by 90/180/270 degrees.",
        "accept": ".pdf", "multiple": False,
        "fields": [
            {"name": "angle", "label": "Angle", "type": "select", "options": ["90", "180", "270"]},
            {"name": "pages", "label": "Pages to rotate (blank = all, e.g. 1,3,5)", "type": "text"},
        ],
    },
    "page-numbers": {
        "name": "Page numbers", "category": "Edit",
        "desc": "Add page numbers to a PDF.",
        "accept": ".pdf", "multiple": False,
        "fields": [
            {"name": "position", "label": "Position", "type": "select",
             "options": ["bottom-center", "bottom-right", "bottom-left", "top-center"]},
            {"name": "start_at", "label": "Start at", "type": "number", "default": 1},
        ],
    },
    "crop-pdf": {
        "name": "Crop PDF", "category": "Edit",
        "desc": "Trim margins from every page (in points).",
        "accept": ".pdf", "multiple": False,
        "fields": [
            {"name": "left", "label": "Left", "type": "number", "default": 0},
            {"name": "right", "label": "Right", "type": "number", "default": 0},
            {"name": "top", "label": "Top", "type": "number", "default": 0},
            {"name": "bottom", "label": "Bottom", "type": "number", "default": 0},
        ],
    },
    "redact-pdf": {
        "name": "Redact PDF", "category": "Security",
        "desc": "Permanently black out and remove text matches.",
        "accept": ".pdf", "multiple": False,
        "fields": [{"name": "terms", "label": "Words/phrases to redact (comma-separated)", "type": "text"}],
    },
    "protect-pdf": {
        "name": "Protect PDF", "category": "Security",
        "desc": "Add a password to encrypt a PDF.",
        "accept": ".pdf", "multiple": False,
        "fields": [{"name": "password", "label": "Password", "type": "password"}],
    },
    "unlock-pdf": {
        "name": "Unlock PDF", "category": "Security",
        "desc": "Remove password protection from a PDF you have access to.",
        "accept": ".pdf", "multiple": False,
        "fields": [{"name": "password", "label": "Current password", "type": "password"}],
    },
    "compare-pdf": {
        "name": "Compare PDF", "category": "Intelligence",
        "desc": "Highlight text differences between two PDFs.",
        "accept": ".pdf", "multiple": True, "fields": [], "result": "html",
    },
}

CATEGORIES = ["Organize", "Optimize", "Convert", "Edit", "Security", "Intelligence"]


@app.route("/")
def index():
    grouped = {c: [] for c in CATEGORIES}
    for tool_id, cfg in TOOLS.items():
        grouped[cfg["category"]].append({"id": tool_id, **cfg})
    return render_template("index.html", grouped=grouped, categories=CATEGORIES)


@app.route("/tool/<tool_id>")
def tool_page(tool_id):
    cfg = TOOLS.get(tool_id)
    if not cfg:
        abort(404)
    return render_template("tool.html", tool_id=tool_id, cfg=cfg)


def _read_upload(key):
    f = request.files.get(key)
    if not f or f.filename == "":
        return None
    return io.BytesIO(f.read())


@app.route("/process/<tool_id>", methods=["POST"])
def process(tool_id):
    cfg = TOOLS.get(tool_id)
    if not cfg:
        abort(404)

    try:
        form = request.form
        files = request.files.getlist("file") if cfg["multiple"] else None
        single = _read_upload("file") if not cfg["multiple"] else None

        # ---------------- ORGANIZE ----------------
        if tool_id == "merge-pdf":
            streams = [io.BytesIO(f.read()) for f in files]
            result = pdf_tools.merge_pdfs(streams)
            return send_file(result, download_name="merged.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "split-pdf":
            result = pdf_tools.split_pdf(single, form.get("ranges") or None)
            return send_file(result, download_name="split_result.zip", as_attachment=True, mimetype="application/zip")

        if tool_id == "organize-pdf":
            result = pdf_tools.organize_pdf(single, form.get("order", ""))
            return send_file(result, download_name="organized.pdf", as_attachment=True, mimetype="application/pdf")

        # ---------------- OPTIMIZE ----------------
        if tool_id == "compress-pdf":
            result = pdf_tools.compress_pdf(single, form.get("level", "recommended"))
            return send_file(result, download_name="compressed.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "repair-pdf":
            result = pdf_tools.repair_pdf(single)
            return send_file(result, download_name="repaired.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "compress-image":
            quality = int(form.get("quality") or 60)
            max_width = form.get("max_width")
            max_width = int(max_width) if max_width else None
            result, mimetype, ext = image_tools.compress_image(single, quality, max_width)
            return send_file(result, download_name=f"compressed.{ext}", as_attachment=True, mimetype=mimetype)

        # ---------------- CONVERT ----------------
        if tool_id == "pdf-to-word":
            result = pdf_tools.pdf_to_word(single)
            return send_file(result, download_name="converted.docx", as_attachment=True,
                              mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        if tool_id == "pdf-to-powerpoint":
            result = pdf_tools.pdf_to_ppt(single)
            return send_file(result, download_name="converted.pptx", as_attachment=True,
                              mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation")

        if tool_id == "pdf-to-excel":
            result = pdf_tools.pdf_to_excel(single)
            return send_file(result, download_name="converted.xlsx", as_attachment=True,
                              mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if tool_id == "word-to-pdf":
            result = office_tools.word_to_pdf(single)
            return send_file(result, download_name="converted.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "powerpoint-to-pdf":
            result = office_tools.ppt_to_pdf(single)
            return send_file(result, download_name="converted.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "excel-to-pdf":
            result = office_tools.excel_to_pdf(single)
            return send_file(result, download_name="converted.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "html-to-pdf":
            result = office_tools.html_to_pdf(form.get("html", ""))
            return send_file(result, download_name="converted.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "pdf-to-jpg":
            dpi = int(form.get("dpi") or 150)
            result = pdf_tools.pdf_to_jpg(single, dpi)
            return send_file(result, download_name="pages.zip", as_attachment=True, mimetype="application/zip")

        if tool_id == "jpg-to-pdf":
            streams = [io.BytesIO(f.read()) for f in files]
            result = image_tools.images_to_pdf(streams)
            return send_file(result, download_name="images.pdf", as_attachment=True, mimetype="application/pdf")

        # ---------------- EDIT ----------------
        if tool_id == "watermark-pdf":
            opacity = float(form.get("opacity") or 0.3)
            result = pdf_tools.watermark_pdf(single, form.get("text", "CONFIDENTIAL"), opacity)
            return send_file(result, download_name="watermarked.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "rotate-pdf":
            angle = int(form.get("angle") or 90)
            result = pdf_tools.rotate_pdf(single, angle, form.get("pages") or None)
            return send_file(result, download_name="rotated.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "page-numbers":
            start_at = int(form.get("start_at") or 1)
            result = pdf_tools.add_page_numbers(single, form.get("position", "bottom-center"), start_at)
            return send_file(result, download_name="numbered.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "crop-pdf":
            result = pdf_tools.crop_pdf(
                single,
                left=float(form.get("left") or 0), right=float(form.get("right") or 0),
                top=float(form.get("top") or 0), bottom=float(form.get("bottom") or 0),
            )
            return send_file(result, download_name="cropped.pdf", as_attachment=True, mimetype="application/pdf")

        # ---------------- SECURITY ----------------
        if tool_id == "redact-pdf":
            terms = [t.strip() for t in form.get("terms", "").split(",") if t.strip()]
            result = pdf_tools.redact_pdf(single, terms)
            return send_file(result, download_name="redacted.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "protect-pdf":
            result = pdf_tools.protect_pdf(single, form.get("password", ""))
            return send_file(result, download_name="protected.pdf", as_attachment=True, mimetype="application/pdf")

        if tool_id == "unlock-pdf":
            result = pdf_tools.unlock_pdf(single, form.get("password", ""))
            return send_file(result, download_name="unlocked.pdf", as_attachment=True, mimetype="application/pdf")

        # ---------------- INTELLIGENCE ----------------
        if tool_id == "compare-pdf":
            streams = [io.BytesIO(f.read()) for f in files]
            if len(streams) != 2:
                return jsonify({"error": "Please upload exactly two PDF files to compare."}), 400
            html_diff = pdf_tools.compare_pdfs(streams[0], streams[1])
            return html_diff

        return jsonify({"error": "Unknown tool"}), 400

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large for this deployment's request size limit."}), 413


if __name__ == "__main__":
    app.run(debug=True, port=5000)
