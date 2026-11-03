import joblib
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..db import Dataset, Experiment, RegisteredModel, PredictionRecord, session
from ..schemas import RegisterRequest, PredictRequest, CompareRequest
from ..services.datasets import controlled
from ..services.ml import predict
from .training import experiment_view

router = APIRouter(tags=['records'])

def get_experiment(db, eid):
    exp = db.get(Experiment, eid)
    if not exp: raise HTTPException(404, 'Experiment not found.')
    return exp

def model_view(db, model):
    exp = get_experiment(db, model.experiment_id)
    return {'id': model.id, 'name': model.name, 'created_at': model.created_at, 'experiment_id': exp.id,
            'dataset_id': exp.dataset_id, 'task': exp.task, 'algorithm': exp.algorithm, 'metrics': exp.metrics, 'features': exp.details.get('features', [])}

@router.get('/experiments')
def experiments(task: str | None = None, status: str | None = None, db: Session = Depends(session)):
    q = select(Experiment).order_by(Experiment.started_at.desc())
    if task: q = q.where(Experiment.task == task)
    if status: q = q.where(Experiment.status == status)
    return [experiment_view(e) for e in db.scalars(q)]

@router.post('/experiments/compare')
def compare(cfg: CompareRequest, db: Session = Depends(session)):
    rows = [get_experiment(db, eid) for eid in cfg.experiment_ids]
    if len(set(cfg.experiment_ids)) != len(rows): raise HTTPException(422, 'Select distinct experiments.')
    if len({(e.dataset_id, e.task) for e in rows}) != 1: raise HTTPException(422, 'Comparison requires the same dataset and task.')
    if any(e.status != 'succeeded' for e in rows): raise HTTPException(422, 'Compare successful experiments only.')
    allowed = {'accuracy','precision_macro','precision_weighted','recall_macro','recall_weighted','f1_macro','f1_weighted','roc_auc','mae','mse','rmse','r2','silhouette','inertia'}
    if cfg.metric not in allowed or any(not isinstance(e.metrics.get(cfg.metric), (float,int)) for e in rows):
        raise HTTPException(422, 'Choose a numeric metric available for every selected experiment.')
    compatible = len({(e.config['seed'], e.config['test_size'], e.config.get('target'), e.config.get('text_column'), e.details.get('split_fingerprint')) for e in rows}) == 1
    ordered = sorted(rows, key=lambda e:e.metrics[cfg.metric], reverse=cfg.metric not in {'mae','mse','rmse','inertia'})
    return {'runs': [experiment_view(e) for e in ordered], 'metric': cfg.metric, 'best_experiment_id': ordered[0].id if compatible else None,
            'warning': None if compatible else 'Evaluation setups differ. Scores are not directly equivalent; best-model selection is disabled.'}

@router.get('/experiments/{experiment_id}')
def experiment(experiment_id: str, db: Session = Depends(session)):
    return experiment_view(get_experiment(db, experiment_id))

@router.get('/models')
def models(db: Session = Depends(session)):
    return [model_view(db,m) for m in db.scalars(select(RegisteredModel).order_by(RegisteredModel.created_at.desc()))]

@router.post('/models', status_code=201)
def register(cfg: RegisterRequest, db: Session = Depends(session)):
    exp = get_experiment(db, cfg.experiment_id)
    if exp.status != 'succeeded' or not exp.artifact: raise HTTPException(422, 'Only successful trained experiments can be registered.')
    model = db.scalar(select(RegisteredModel).where(RegisteredModel.experiment_id == exp.id))
    if not model:
        model = RegisteredModel(experiment_id=exp.id, name=cfg.name.strip() or exp.algorithm)
        db.add(model)
        db.commit()
    return model_view(db, model)

def registered(db, mid):
    model = db.get(RegisteredModel, mid)
    if not model: raise HTTPException(404, 'Registered model not found.')
    return model

@router.get('/models/{model_id}')
def model_detail(model_id: str, db: Session = Depends(session)):
    return model_view(db, registered(db, model_id))

@router.get('/models/{model_id}/export')
def export(model_id: str, request: Request, db: Session = Depends(session)):
    model = registered(db, model_id)
    exp = get_experiment(db, model.experiment_id)
    return FileResponse(controlled(request.app.state.artifacts, exp.artifact), filename=f'modelforge-{model.id}.joblib', media_type='application/octet-stream')

@router.post('/models/{model_id}/predict')
def inference(model_id: str, cfg: PredictRequest, request: Request, db: Session = Depends(session)):
    model = registered(db, model_id)
    exp = get_experiment(db, model.experiment_id)
    path = controlled(request.app.state.artifacts, exp.artifact)
    if not path.is_file(): raise HTTPException(409, 'Registered artifact is missing from local storage.')
    try: result = predict(joblib.load(path), exp, cfg.records)
    except ValueError as exc: raise HTTPException(422, str(exc))
    record = PredictionRecord(model_id=model.id, inputs=cfg.model_dump(), outputs=result)
    db.add(record)
    db.commit()
    return {'id': record.id, **result}

@router.get('/predictions')
def predictions(db: Session = Depends(session)):
    return [{'id': p.id, 'model_id': p.model_id, 'created_at': p.created_at, 'inputs': p.inputs, 'outputs': p.outputs} for p in db.scalars(select(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(100))]

@router.get('/dashboard')
def dashboard(db: Session = Depends(session)):
    count = lambda entity: db.scalar(select(func.count()).select_from(entity))
    return {'datasets': count(Dataset), 'experiments': count(Experiment), 'models': count(RegisteredModel), 'predictions': count(PredictionRecord),
            'succeeded': db.scalar(select(func.count()).select_from(Experiment).where(Experiment.status=='succeeded')),
            'failed': db.scalar(select(func.count()).select_from(Experiment).where(Experiment.status=='failed')),
            'recent_runs': [experiment_view(e) for e in db.scalars(select(Experiment).order_by(Experiment.started_at.desc()).limit(6))],
            'recent_predictions': predictions(db)[:5]}
