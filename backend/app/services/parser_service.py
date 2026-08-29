"""File-type detection and parser dispatch (Phase 3: upload pipeline).

Single responsibility: given a file name + bytes, decide which concrete
parser (csv_parser or excel_parser) must run and return its standardised
row dictionaries. Also owns the shared parser exceptions + column contract
so every parser produces an identical shape.
"""
from pathlib import Path

# Canonical, normalised column names every parser must return.
REQUIRED_COLUMNS = {
    "invoice_number",
    "vendor_name",
    "invoice_date",
    "product_name",
    "quantity",
    "unit_price",
    "gst_percent",
}

# Friendly header variants -> canonical column name.
HEADER_ALIASES = {
    "gst": "gst_percent",
    "gst_rate": "gst_percent",
    "gst_percentage": "gst_percent",
    "sales_tax": "gst_percent",
}

ALLOWED_EXTENSIONS = {
    ".csv": "csv",
    ".xlsx": "excel",
}


class UnsupportedFileTypeError(ValueError):
    """Raised when the upload is not a .csv or .xlsx file."""


class EmptyFileError(ValueError):
    """Raised when the file has no headers or no data rows."""


class MissingColumnsError(ValueError):
    """Raised when required columns are absent from the file."""


class FileParseError(ValueError):
    """Raised when the file bytes cannot be parsed (e.g. corrupted Excel)."""


def normalize_header(header) -> str:
    """Lowercase a header and collapse runs of non-word chars into '_'."""
    cleaned = "".join("_" if not c.isalnum() else c for c in str(header).strip().lower())
    return "_".join(cleaned.split("_")).strip("_")


def resolve_header(header) -> str:
    """Map a raw header to its canonical column name."""
    return HEADER_ALIASES.get(normalize_header(header), normalize_header(header))


def detect_parser(file_name) -> str:
    """Return the parser key ('csv' | 'excel') or raise UnsupportedFileTypeError."""
    ext = Path(file_name or "").suffix.lower()
    kind = ALLOWED_EXTENSIONS.get(ext)
    if kind is None:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext or '<no extension>'}' for '{file_name}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )
    return kind


def parse_file(file_name, content: bytes) -> list:
    """Dispatch to the correct parser.

    Lazy imports avoid a circular import between this module (which owns the
    exceptions) and the concrete parsers (which raise them).
    """
    kind = detect_parser(file_name)
    if kind == "csv":
        from .csv_parser import parse_csv

        return parse_csv(content)
    from .excel_parser import parse_excel

    return parse_excel(content)