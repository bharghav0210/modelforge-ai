from contextlib import asynccontextmanager
from threading import Lock
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .config import Settings, settings
from .db import setup_database, Experiment, now
from .routers import datasets, training, records, genai
from .services.ml import ALGORITHMS

def create_app(config: Settings = settings):
    @asynccontextmanager
    async def lifespan(app):
        engine, app.state.sessions = setup_database(config.data_dir)
        app.state.settings = config
        app.state.uploads = config.data_dir / 'uploads'
        app.state.artifacts = config.data_dir / 'artifacts'
        app.state.uploads.mkdir(exist_ok=True)
        app.state.artifacts.mkdir(exist_ok=True)
        app.state.training_lock = Lock()
        with app.state.sessions() as db:
            for exp in db.scalars(select(Experiment).where(Experiment.status == 'running')):
                exp.status, exp.error, exp.finished_at = 'failed', 'Training interrupted by application restart.', now()
            db.commit()
        yield
        engine.dispose()
    app = FastAPI(title='ModelForge AI', version='1.0.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3003','http://127.0.0.1:3003'], allow_methods=['GET','POST','DELETE','OPTIONS'], allow_headers=['Content-Type'])
    @app.exception_handler(HTTPException)
    async def http_error(request, exc): return JSONResponse(status_code=exc.status_code, content={'error': {'message': str(exc.detail)}})
    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc): return JSONResponse(status_code=422, content={'error': {'message': '; '.join(f'{".".join(str(i) for i in e["loc"])}: {e["msg"]}' for e in exc.errors())}})
    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        import logging
        logging.getLogger('modelforge').exception('Unhandled API error')
        return JSONResponse(status_code=500, content={'error': {'message': 'Unexpected server error. See local server log.'}})
    @app.get('/')
    def root(): return {'application': 'ModelForge AI', 'version': '1.0.0'}
    @app.get('/api/v1/health')
    def health(): return {'status': 'healthy', 'service': 'modelforge-api', 'version': '1.0.0'}
    @app.get('/api/v1/settings')
    def limits(): return {'scope': 'Trusted local single-user CPU workstation', 'max_upload_mib': 10, 'max_rows': config.max_rows, 'max_columns': config.max_columns, 'max_encoded_features': config.max_encoded_features, 'algorithms': ALGORITHMS, 'ollama_url': config.ollama_url, 'training_concurrency': 1, 'artifact_warning': 'Serialized models are trusted executable code. Never load artifacts from untrusted sources.'}
    for router in (datasets.router, training.router, records.router, genai.router): app.include_router(router, prefix='/api/v1')
    return app

app = create_app()
