"""Excel reading helpers."""
import io

import pandas as pd


def read_excel(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(file_bytes))


def read_excel_path(path: str) -> pd.DataFrame:
    return pd.read_excel(path)