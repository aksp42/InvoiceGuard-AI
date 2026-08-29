"""CSV parser (Phase 3: upload pipeline).

Reads CSV bytes, validates the required columns and returns standardised
row dictionaries (transport keys from parser_service, string values).
"""
import csv
import io

from backend.app.services.parser_service import (
    EmptyFileError,
    FileParseError,
    MissingColumnsError,
    REQUIRED_COLUMNS,
    resolve_header,
)


def _decode(content: bytes) -> str:
    """Decode with UTF-8 (with BOM tolerance) falling back to Windows-1252."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise FileParseError("Could not decode CSV file (expected UTF-8 or Windows-1252).")


def _row_dict(raw, raw_headers, headers):
    row = {}
    for raw_header, header in zip(raw_headers, headers):
        value = raw.get(raw_header)
        row[header] = "" if value is None else str(value).strip()
    return row


def parse_csv(content: bytes) -> list:
    if not content or not content.strip():
        raise EmptyFileError("The uploaded file is empty.")

    reader = csv.DictReader(io.StringIO(_decode(content)))
    raw_headers = reader.fieldnames or []
    headers = [resolve_header(header) for header in raw_headers]

    missing = REQUIRED_COLUMNS - set(headers)
    if missing:
        raise MissingColumnsError(
            f"Missing required columns: {', '.join(sorted(missing))}. "
            f"Found: {[h for h in headers if h]}."
        )

    rows = []
    for raw in reader:
        row = _row_dict(raw, raw_headers, headers)
        if any(row.values()):
            rows.append(row)

    if not rows:
        raise EmptyFileError("The CSV file contains no data rows.")
    return rows