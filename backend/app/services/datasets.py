import csv
import io
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from fastapi import HTTPException

def parse_dataset(raw: bytes, suffix: str, settings):
    if not raw or len(raw) > settings.max_upload_bytes:
        raise ValueError('File must contain data and be at most 10 MiB.')
    if suffix == '.csv':
        text = raw.decode('utf-8-sig', errors='strict')
        if '\x00' in text: raise ValueError('Null bytes are not valid CSV.')
        records = list(csv.reader(io.StringIO(text), strict=True))
        if len(records) < 2: raise ValueError('Include a header and at least one data row.')
        header = records[0]
        if any(len(row) != len(header) for row in records[1:]):
            raise ValueError('Malformed CSV: every row must match the header width.')
        if any(not x.strip() for x in header) or len(set(header)) != len(header):
            raise ValueError('Column names must be nonempty and unique.')
        df = pd.read_csv(io.BytesIO(raw), encoding='utf-8-sig', on_bad_lines='error')
    elif suffix == '.xlsx':
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if sum(i.file_size for i in z.infolist()) > 50 * 1024 * 1024:
                raise ValueError('Workbook expanded size exceeds 50 MiB.')
        from openpyxl import load_workbook
        book = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        try:
            if len(book.sheetnames) != 1: raise ValueError('Upload one worksheet per dataset.')
            sheet = book.active
            if sheet.max_row > settings.max_rows + 1 or sheet.max_column > settings.max_columns:
                raise ValueError('Dataset exceeds row or column limits.')
            rows = list(sheet.values)
            if len(rows) < 2: raise ValueError('Workbook contains no data rows.')
            header = rows[0]
            if any(not isinstance(x, str) or not x.strip() for x in header) or len(set(header)) != len(header):
                raise ValueError('Column names must be nonempty, unique strings.')
            df = pd.DataFrame(rows[1:], columns=header)
            for col in df.select_dtypes(include=['object', 'str']): df[col] = df[col].where(df[col].notna(), np.nan)
        finally: book.close()
    else: raise ValueError('Only UTF-8 CSV and single-sheet XLSX are supported.')
    if df.empty or len(df) > settings.max_rows or len(df.columns) > settings.max_columns:
        raise ValueError(f'Dataset requires 1–{settings.max_rows} rows and at most {settings.max_columns} columns.')
    for col in df.select_dtypes(include='number'):
        if np.isinf(df[col].to_numpy(dtype=float)).any(): raise ValueError(f'Column {col} contains infinity.')
    return df

def metadata(df):
    return {'rows': len(df), 'columns': [{'name': str(c), 'dtype': str(df[c].dtype),
            'numeric': bool(pd.api.types.is_numeric_dtype(df[c])), 'missing': int(df[c].isna().sum())} for c in df],
            'preview': df.head(20).astype(object).where(pd.notna(df.head(20)), None).to_dict(orient='records')}

def controlled(directory: Path, name: str):
    if Path(name).name != name: raise HTTPException(400, 'Invalid storage reference.')
    path = (directory / name).resolve()
    if path.parent != directory.resolve(): raise HTTPException(400, 'Invalid storage reference.')
    return path
