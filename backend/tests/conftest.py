import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import create_app
from app.config import Settings

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path, ollama_url='http://127.0.0.1:1'))) as c: yield c

@pytest.fixture
def sample():
    return Path(__file__).resolve().parents[2] / 'samples'

def upload(client, sample, name='customer_churn.csv'):
    response = client.post('/api/v1/datasets', files={'file': (name, (sample/name).read_bytes())})
    assert response.status_code == 201, response.text
    return response.json()

def run(client, did, task='classification', algorithm='logistic_regression', target='churn', **kw):
    return client.post('/api/v1/automl/train', json={'dataset_id':did,'task':task,'algorithm':algorithm,'target':target,**kw}).json()
