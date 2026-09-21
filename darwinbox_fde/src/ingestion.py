import re
from pathlib import Path
import pandas as pd


def safe_name(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = re.sub(r"[^a-z0-9_]+", "_", stem).strip("_")
    return stem or "data"


def load_upload(upload):
    ext = Path(upload.name).suffix.lower()
    if ext == ".csv":
        return {safe_name(upload.name): pd.read_csv(upload)}
    if ext in {".xlsx", ".xls"}:
        book = pd.ExcelFile(upload)
        out = {}
        base = safe_name(upload.name)
        for sheet in book.sheet_names:
            out[f"{base}__{safe_name(sheet)}"] = pd.read_excel(book, sheet_name=sheet)
        return out
    raise ValueError(f"Unsupported file type: {ext}")
