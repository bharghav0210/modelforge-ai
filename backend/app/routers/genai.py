import time
import httpx
from fastapi import APIRouter, Request, HTTPException
from ..schemas import GenerateRequest

router = APIRouter(prefix='/genai', tags=['genai'])

@router.get('/status')
def status(request: Request):
    try:
        with httpx.Client(timeout=3, trust_env=False) as client:
            response = client.get(request.app.state.settings.ollama_url + '/api/tags')
            response.raise_for_status()
            models = [m['name'] for m in response.json().get('models', [])]
        return {'available': True, 'models': models, 'message': 'Connected to local Ollama.' if models else 'Ollama is running with no installed models. Install a model manually.'}
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return {'available': False, 'models': [], 'message': f'Ollama unavailable. Start Ollama locally on port 11434. Other workspaces remain available. ({type(exc).__name__})'}

@router.post('/generate')
def generate(cfg: GenerateRequest, request: Request):
    started = time.perf_counter()
    try:
        with httpx.Client(timeout=120, trust_env=False) as client:
            response = client.post(request.app.state.settings.ollama_url + '/api/generate', json={**cfg.model_dump(exclude={'temperature'}), 'stream': False, 'options': {'temperature': cfg.temperature, 'num_predict': 1024, 'num_ctx': 4096}})
            response.raise_for_status()
            body = response.json()
            if not isinstance(body.get('response'), str): raise ValueError('Provider returned no text response.')
        return {'response': body['response'], 'model': cfg.model, 'duration': time.perf_counter()-started}
    except (httpx.HTTPError, ValueError) as exc: raise HTTPException(503, f'Local provider request failed: {exc}')
