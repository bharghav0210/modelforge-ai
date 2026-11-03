import io
import json
import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.config import Settings
from app.main import create_app
from app.db import Experiment
from app.schemas import TrainRequest
from app.services.ml import train, finite_json, regression_metrics
from app.services.datasets import controlled
from conftest import upload, run


def test_health_and_empty_dashboard(client):
    assert client.get('/api/v1/health').json()['status']=='healthy'
    assert client.get('/api/v1/dashboard').json()['experiments']==0
    assert client.get('/api/v1/settings').json()['training_concurrency']==1


def test_upload_metadata_download_delete(client, sample):
    d=upload(client,sample)
    assert d['rows']==240 and len(d['columns'])==5
    assert client.get(f'/api/v1/datasets/{d["id"]}/download').content==(sample/'customer_churn.csv').read_bytes()
    assert client.delete(f'/api/v1/datasets/{d["id"]}').status_code==200
    assert client.get(f'/api/v1/datasets/{d["id"]}').status_code==404


@pytest.mark.parametrize('raw', [b'',b'a,b\n1,2,3\n',b'a,a\n1,2\n',b'a,b\n1\n',b'a,b\n"unclosed,2',b'\xff\xfe',b'a,b\n1,\x00\n',b'a,b\n',b'a,\n1,2\n',b'a,b\ninf,1\n'])
def test_malformed_csv(client,raw):
    r=client.post('/api/v1/datasets',files={'file':('bad.csv',raw)})
    assert r.status_code==422,r.text


def test_xlsx(client):
    stream=io.BytesIO()
    pd.DataFrame({'a':[1,2], 'b':['x','y']}).to_excel(stream,index=False)
    assert client.post('/api/v1/datasets',files={'file':('book.xlsx',stream.getvalue())}).status_code==201


def test_size_limit(client):
    assert client.post('/api/v1/datasets',files={'file':('large.csv',b'x'*(10*1024*1024+1))}).status_code==422


@pytest.mark.parametrize('task,algorithm,file,target,extra',[
    ('classification','logistic_regression','customer_churn.csv','churn',{}),
    ('classification','random_forest_classifier','customer_churn.csv','churn',{}),
    ('classification','decision_tree_classifier','customer_churn.csv','churn',{}),
    ('classification','gaussian_nb','customer_churn.csv','churn',{}),
    ('regression','linear_regression','house_prices.csv','price',{}),
    ('regression','random_forest_regressor','house_prices.csv','price',{}),
    ('regression','decision_tree_regressor','house_prices.csv','price',{}),
    ('regression','ridge','house_prices.csv','price',{}),
    ('clustering','kmeans','customer_segments.csv',None,{}),
    ('nlp','tfidf_logistic','product_reviews.csv','sentiment',{'text_column':'review'}),
    ('nlp','tfidf_naive_bayes','product_reviews.csv','sentiment',{'text_column':'review'}),
    ('neural_classification','mlp_classifier','customer_churn.csv','churn',{'iterations':40}),
    ('neural_regression','mlp_regressor','house_prices.csv','price',{'iterations':40}),
])
def test_train_register_predict_export(client,sample,task,algorithm,file,target,extra):
    d=upload(client,sample,file)
    e=run(client,d['id'],task,algorithm,target,**extra)
    assert e['status']=='succeeded',e
    assert e['has_artifact']
    m=client.post('/api/v1/models',json={'experiment_id':e['id'],'name':'Test model'}).json()
    assert client.get('/api/v1/models').json()[0]['id']==m['id']
    frame=pd.read_csv(sample/file)
    fields=e['details']['features']
    row={f['name']:frame.iloc[0][f['name']].item() if isinstance(frame.iloc[0][f['name']],np.generic) else frame.iloc[0][f['name']] for f in fields}
    if task in ['classification','regression','neural_classification','neural_regression']:
        for f in fields:
            if not f['numeric']: row[f['name']]='previously unseen category'
    response=client.post(f'/api/v1/models/{m["id"]}/predict',json={'records':[row]})
    assert response.status_code==200,response.text
    assert len(response.json()['predictions'])==1
    exported=client.get(f'/api/v1/models/{m["id"]}/export')
    assert exported.status_code==200 and len(exported.content)>100
    loaded=joblib.load(io.BytesIO(exported.content))
    assert hasattr(loaded,'predict')
    assert client.get('/api/v1/predictions').json()[0]['model_id']==m['id']
    assert client.delete(f'/api/v1/datasets/{d["id"]}').status_code==409
    assert client.get('/api/v1/dashboard').json()['succeeded']==1
    assert 'NaN' not in json.dumps(e,allow_nan=False)


def test_train_test_isolation_and_reproducibility(tmp_path,sample):
    from sklearn.model_selection import train_test_split
    df=pd.read_csv(sample/'customer_churn.csv')
    cfg=TrainRequest(dataset_id='example',task='classification',algorithm='logistic_regression',target='churn')
    a,b=train_test_split(np.arange(len(df)),test_size=.25,random_state=42,stratify=df.churn)
    # Make held-out numeric and categorical values impossible to encounter in training.
    df.loc[b,'age']=1000000
    df.loc[b,'contract']='test-only-category'
    pipe,metrics,detail=train(df,cfg,Settings(data_dir=tmp_path))
    prep=pipe.named_steps['preprocess']
    numeric=prep.named_transformers_['numeric']
    assert numeric.named_steps['impute'].statistics_[0]==df.iloc[a].age.median()
    assert numeric.named_steps['scale'].mean_[0]==pytest.approx(df.iloc[a].age.mean())
    assert 'test-only-category' not in prep.named_transformers_['categorical'].named_steps['encode'].categories_[0]
    assert 'churn' not in prep.feature_names_in_
    assert not set(a)&set(b)
    _,metrics2,detail2=train(df,cfg,Settings(data_dir=tmp_path))
    assert metrics==metrics2 and detail['split_fingerprint']==detail2['split_fingerprint']


def test_nlp_vocabulary_isolation(tmp_path,sample):
    from sklearn.model_selection import train_test_split
    df=pd.read_csv(sample/'product_reviews.csv')
    _,test=train_test_split(np.arange(len(df)),test_size=.25,random_state=42,stratify=df.sentiment)
    df.loc[test,'review']='neverobservedtoken'
    pipe,_,_=train(df,TrainRequest(dataset_id='x',task='nlp',algorithm='tfidf_logistic',target='sentiment',text_column='review'),Settings(data_dir=tmp_path))
    assert 'neverobservedtoken' not in pipe.named_steps['tfidf'].vocabulary_


@pytest.mark.parametrize('task,algorithm,target', [('classification','logistic_regression','missing'),('regression','ridge','contract'),('classification','ridge','churn')])
def test_invalid_target_and_failed_history(client,sample,task,algorithm,target):
    d=upload(client,sample)
    e=run(client,d['id'],task,algorithm,target)
    assert e['status']=='failed' and e['error']
    assert client.get('/api/v1/experiments?status=failed').json()[0]['id']==e['id']
    assert client.post('/api/v1/models',json={'experiment_id':e['id'],'name':'no'}).status_code==422


@pytest.mark.parametrize('csv,task,algorithm,target',[
    ('x,y\n'+''.join(f'{i},same\n' for i in range(20)),'classification','logistic_regression','y'),
    ('x,y\n'+''.join(f'{i},1\n' for i in range(20)),'regression','ridge','y'),
    ('x,y\n'+''.join(f'{i},{"" if i==2 else i%2}\n' for i in range(20)),'classification','logistic_regression','y'),
    ('x\n'+'1\n'*20,'clustering','kmeans',None),
    ('x\n1\n2\n','clustering','kmeans',None),
])
def test_invalid_training_data(client,csv,task,algorithm,target):
    d=client.post('/api/v1/datasets',files={'file':('edge.csv',csv.encode())}).json()
    assert run(client,d['id'],task,algorithm,target)['status']=='failed'


def test_nonfinite_metrics():
    assert finite_json({'a':float('nan'),'b':float('inf')})=={'a':None,'b':None}
    assert regression_metrics([1,1],[2,2])['r2'] is None


def test_invalid_predictions_and_safe_artifacts(client,sample,tmp_path):
    d=upload(client,sample)
    e=run(client,d['id'])
    m=client.post('/api/v1/models',json={'experiment_id':e['id'],'name':'Churn'}).json()
    for row in [{}, {'age':'no'}, {'age':30,'tenure_months':12,'monthly_charge':'nan','contract':'annual'}, {'age':None,'tenure_months':12,'monthly_charge':70,'contract':'annual'}]:
        assert client.post(f'/api/v1/models/{m["id"]}/predict',json={'records':[row]}).status_code==422
    assert client.post('/api/v1/models/upload',files={'file':('evil.joblib',b'no')}).status_code==405
    assert client.get('/api/v1/models/unknown/export').status_code==404
    with pytest.raises(Exception): controlled(tmp_path,'../evil.joblib')
    # A tampered metadata reference cannot escape the controlled artifact directory.
    with client.app.state.sessions() as db:
        exp=db.get(Experiment,e['id']);exp.artifact='../evil.joblib';db.commit()
    assert client.get(f'/api/v1/models/{m["id"]}/export').status_code==400


def test_comparison(client,sample):
    d=upload(client,sample)
    a=run(client,d['id'])
    b=run(client,d['id'],algorithm='random_forest_classifier')
    q={'experiment_ids':[a['id'],b['id']],'metric':'f1_macro'}
    assert client.post('/api/v1/experiments/compare',json=q).json()['best_experiment_id']
    c=run(client,d['id'],seed=9)
    q['experiment_ids']=[a['id'],c['id']]
    r=client.post('/api/v1/experiments/compare',json=q).json()
    assert r['warning'] and r['best_experiment_id'] is None
    q['metric']='duration';assert client.post('/api/v1/experiments/compare',json=q).status_code==422


def test_persistence_across_restart(tmp_path,sample):
    config=Settings(data_dir=tmp_path,ollama_url='http://127.0.0.1:1')
    with TestClient(create_app(config)) as c:
        d=upload(c,sample);e=run(c,d['id']);m=c.post('/api/v1/models',json={'experiment_id':e['id'],'name':'Saved'}).json()
    with TestClient(create_app(config)) as c:
        assert c.get('/api/v1/dashboard').json()['experiments']==1
        row={'age':33,'tenure_months':12,'monthly_charge':75,'contract':'monthly'}
        assert c.post(f'/api/v1/models/{m["id"]}/predict',json={'records':[row]}).status_code==200


def test_ollama_offline(client):
    s=client.get('/api/v1/genai/status').json()
    assert not s['available'] and s['models']==[]
    assert client.post('/api/v1/genai/generate',json={'model':'none','prompt':'hello'}).status_code==503
    assert client.get('/api/v1/health').status_code==200


def test_multiclass(client):
    from sklearn.datasets import load_iris
    df=load_iris(as_frame=True).frame
    d=client.post('/api/v1/datasets',files={'file':('iris.csv',df.to_csv(index=False).encode())}).json()
    e=run(client,d['id'],target='target')
    assert e['status']=='succeeded',e
    assert len(e['metrics']['labels'])==3 and e['metrics']['roc_auc'] is not None
    assert 'precision_positive' not in e['metrics']


def test_missing_mixed_features_and_schema_limits(client):
    # Numeric imputation, an entirely empty column and mixed strings remain in the pipeline.
    text='number,mixed,empty,target\n'+''.join(f'{"" if i%4==0 else i},{"value" if i%3==0 else i},,{i%2}\n' for i in range(80))
    d=client.post('/api/v1/datasets',files={'file':('mixed.csv',text.encode())}).json()
    e=run(client,d['id'],target='target')
    assert e['status']=='succeeded',e
    assert [x['name'] for x in e['details']['features']]==['number','mixed','empty']
    assert client.post('/api/v1/automl/train',json={'dataset_id':d['id'],'task':'classification','algorithm':'logistic_regression','iterations':501}).status_code==422


def test_training_concurrency_limit(client,sample):
    d=upload(client,sample)
    client.app.state.training_lock.acquire()
    try:
        response=client.post('/api/v1/automl/train',json={'dataset_id':d['id'],'task':'classification','algorithm':'logistic_regression','target':'churn'})
        assert response.status_code==409
    finally: client.app.state.training_lock.release()


def test_regression_overflow_has_reason():
    with np.errstate(over='ignore',invalid='ignore'):
        result=regression_metrics([1e200,-1e200],[0,0])
    assert result['mse'] is None and 'mse_reason' in result
