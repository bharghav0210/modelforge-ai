from pathlib import Path
from uuid import uuid4
import time
import joblib
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from ..db import Experiment, now, session
from ..schemas import TrainRequest
from ..services.datasets import controlled, parse_dataset
from ..services.ml import train
from .datasets import get_dataset

router = APIRouter(tags=['training'])

def experiment_view(e):
    return {key: getattr(e, key) for key in ('id', 'dataset_id', 'task', 'algorithm', 'config', 'metrics', 'status', 'started_at', 'finished_at', 'duration', 'error', 'details')} | {'has_artifact': bool(e.artifact)}

@router.post('/automl/train')
def train_model(cfg: TrainRequest, request: Request, db: Session = Depends(session)):
    dataset = get_dataset(db, cfg.dataset_id)
    if not request.app.state.training_lock.acquire(blocking=False): raise HTTPException(409, 'Another training request is running. Please wait.')
    started = time.perf_counter()
    exp = Experiment(dataset_id=dataset.id, task=cfg.task, algorithm=cfg.algorithm, config=cfg.model_dump())
    artifact_path = None
    try:
        db.add(exp)
        db.commit()
        original = controlled(request.app.state.uploads, dataset.storage_name)
        frame = parse_dataset(original.read_bytes(), original.suffix, request.app.state.settings)
        pipeline, metrics, details = train(frame, cfg, request.app.state.settings)
        artifact_name = f'{uuid4()}.joblib'
        artifact_path = controlled(request.app.state.artifacts, artifact_name)
        # Only this code writes artifacts. No API accepts serialized model uploads.
        joblib.dump(pipeline, artifact_path)
        exp.metrics, exp.details, exp.artifact, exp.status = metrics, details, artifact_name, 'succeeded'
    except Exception as exc:
        if artifact_path: artifact_path.unlink(missing_ok=True)
        exp.status, exp.error = 'failed', str(exc)[:2000]
    finally:
        exp.duration = time.perf_counter() - started
        exp.finished_at = now()
        try: db.commit()
        finally: request.app.state.training_lock.release()
    return experiment_view(exp)

@router.post('/autonlp/train')
def train_nlp(cfg: TrainRequest, request: Request, db: Session = Depends(session)):
    if cfg.task != 'nlp': raise HTTPException(422, 'AutoNLP requires the nlp task.')
    return train_model(cfg, request, db)

@router.post('/neural/train')
def train_neural(cfg: TrainRequest, request: Request, db: Session = Depends(session)):
    if not cfg.task.startswith('neural_'): raise HTTPException(422, 'Neural Lab requires a neural task.')
    return train_model(cfg, request, db)
