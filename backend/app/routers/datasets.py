from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, UploadFile, Request, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..db import Dataset, Experiment, session
from ..services.datasets import parse_dataset, metadata, controlled

router = APIRouter(prefix='/datasets', tags=['datasets'])

def dataset_view(row):
    return {'id': row.id, 'name': row.name, 'created_at': row.created_at, **row.info}

def get_dataset(db, dataset_id):
    row = db.get(Dataset, dataset_id)
    if not row: raise HTTPException(404, 'Dataset not found.')
    return row

@router.get('')
def datasets(db: Session = Depends(session)):
    return [dataset_view(d) for d in db.scalars(select(Dataset).order_by(Dataset.created_at.desc()))]

@router.post('', status_code=201)
async def upload(request: Request, file: UploadFile = File(...), db: Session = Depends(session)):
    raw = await file.read(request.app.state.settings.max_upload_bytes + 1)
    name = Path(file.filename or 'dataset.csv').name[:180]
    suffix = Path(name).suffix.lower()
    try: df = parse_dataset(raw, suffix, request.app.state.settings)
    except Exception as exc: raise HTTPException(422, f'Invalid dataset: {exc}')
    storage = f'{uuid4()}{suffix}'
    path = controlled(request.app.state.uploads, storage)
    row = Dataset(name=name, storage_name=storage, info=metadata(df))
    try:
        path.write_bytes(raw)
        db.add(row)
        db.commit()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return dataset_view(row)

@router.get('/{dataset_id}')
def detail(dataset_id: str, db: Session = Depends(session)):
    return dataset_view(get_dataset(db, dataset_id))

@router.get('/{dataset_id}/download')
def download(dataset_id: str, request: Request, db: Session = Depends(session)):
    row = get_dataset(db, dataset_id)
    return FileResponse(controlled(request.app.state.uploads, row.storage_name), filename=row.name)

@router.delete('/{dataset_id}')
def delete(dataset_id: str, request: Request, db: Session = Depends(session)):
    row = get_dataset(db, dataset_id)
    if db.scalar(select(func.count()).select_from(Experiment).where(Experiment.dataset_id == row.id)):
        raise HTTPException(409, 'Dataset is referenced by experiment history and cannot be deleted.')
    path = controlled(request.app.state.uploads, row.storage_name)
    db.delete(row)
    db.commit()
    path.unlink(missing_ok=True)
    return {'deleted': dataset_id}
