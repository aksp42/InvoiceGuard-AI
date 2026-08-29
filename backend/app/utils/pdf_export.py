"""
PDF export (report service).

Generates a simple text-based PDF for the validation report using only the
standard library. A production deployment can swap this for ReportLab / WeasyPrint.
"""
from typing import Iterable


def _escape(text: str) -> str:
    text = str(text)
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.replace("\r", "").replace("\xa0", " ")


def to_pdf_bytes(rows: Iterable[tuple]) -> bytes:
    """
    Minimal PDF writer. `rows` is an iterable of tuples; the first row is
    treated as the header.
    """
    rows = list(rows)
    col_count = len(rows[0]) if rows else 0
    col_w = max(20, 660 // max(col_count, 1))
    line_h = 18
    y = 800

    content = "BT /F1 10 Tf\n"
    for row in rows:
        cell = " | ".join(_escape(c)[: col_w] for c in row)
        content += f"1 0 0 1 40 {y} Tm ({cell}) Tj T*\n"
        y -= line_h
    content += "ET"

    objects = [
        b"<< /Type /Catalog /Pages 3 0 R >>",
        b"<< /Type /Pages /Kids [4 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R /Resources << /Font << /F1 6 0 R >> >> >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
        (b"<< /Length " + str(len(content.encode("latin-1", "replace"))).encode() + b" >>\nstream\n"
         + content.encode("latin-1", "replace") + b"\nendstream"),
    ]

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    return bytes(out)