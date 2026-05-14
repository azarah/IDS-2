"""Convert Markdown to PDF (tables, fenced code blocks). Requires: pip install markdown pymdown-extensions xhtml2pdf."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Markdown → PDF via HTML (xhtml2pdf).")
    ap.add_argument("markdown", type=Path, help="Input .md file")
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output .pdf path (default: same name as .md)",
    )
    args = ap.parse_args()
    md_path: Path = args.markdown.resolve()
    if not md_path.is_file():
        print(f"Not found: {md_path}", file=sys.stderr)
        return 1

    pdf_path = args.output.resolve() if args.output else md_path.with_suffix(".pdf")

    try:
        import markdown
        from xhtml2pdf import pisa
    except ImportError:
        print(
            "Missing packages. Install with:\n"
            "  python -m pip install markdown pymdown-extensions xhtml2pdf",
            file=sys.stderr,
        )
        return 1

    text = md_path.read_text(encoding="utf-8")

    extensions = [
        "markdown.extensions.tables",
        "markdown.extensions.nl2br",
        "pymdownx.superfences",
    ]
    extension_configs = {
        "pymdownx.superfences": {"custom_fences": []},
    }

    html_body = markdown.markdown(
        text,
        extensions=extensions,
        extension_configs=extension_configs,
    )

    css = """
@page { size: Letter; margin: 0.75in; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.35; color: #222; }
h1 { font-size: 18pt; margin-top: 0.5em; }
h2 { font-size: 14pt; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin-top: 1em; }
h3 { font-size: 11pt; margin-top: 0.85em; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 7.5pt; page-break-inside: avoid; }
th, td { border: 1px solid #666; padding: 4px 5px; vertical-align: top; }
th { background: #eee; font-weight: bold; }
pre, code { font-family: Consolas, "Courier New", monospace; }
pre {
  background: #f4f4f4;
  padding: 8px;
  font-size: 7pt;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0.6em 0;
}
code { font-size: 8.5pt; }
hr { border: none; border-top: 1px solid #ccc; margin: 1.25em 0; }
blockquote { margin: 0.5em 0; padding-left: 12px; border-left: 3px solid #ccc; color: #444; font-size: 9.5pt; }
"""

    wrapper = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>'
        f"<title>{md_path.name}</title><style>{css}</style></head><body>"
        f"{html_body}</body></html>"
    )

    with open(pdf_path, "wb") as pdf_file:
        result = pisa.CreatePDF(
            src=wrapper.encode("utf-8"),
            dest=pdf_file,
            encoding="utf-8",
        )

    if result.err:
        print("PDF conversion reported errors; file may still be usable.", file=sys.stderr)

    print(f"Wrote: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
