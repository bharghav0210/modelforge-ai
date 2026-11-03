import os
from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.environ.get('MODELFORGE_DATA_DIR', Path(__file__).resolve().parents[1] / 'data'))
    max_upload_bytes: int = 10 * 1024 * 1024
    max_rows: int = 10000
    max_columns: int = 100
    max_encoded_features: int = 2000
    ollama_url: str = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')

settings = Settings()
