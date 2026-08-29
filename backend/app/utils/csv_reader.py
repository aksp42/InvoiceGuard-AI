"""CSV reading helpers."""
import io

import pandas as pd


def read_csv(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(file_bytes))


def read_csv_path(path: str) -> pd.DataFrame:
    return pd.read_csv(path)