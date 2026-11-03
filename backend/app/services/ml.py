"""Bounded CPU training. All supervised preprocessing is fitted after splitting."""
import hashlib
import json
import time
import warnings
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support, confusion_matrix,
    roc_auc_score, mean_absolute_error, mean_squared_error, r2_score, silhouette_score)
from threadpoolctl import threadpool_limits

ALGORITHMS = {
    'classification': ['logistic_regression', 'random_forest_classifier', 'decision_tree_classifier', 'gaussian_nb'],
    'regression': ['linear_regression', 'random_forest_regressor', 'decision_tree_regressor', 'ridge'],
    'clustering': ['kmeans'], 'nlp': ['tfidf_logistic', 'tfidf_naive_bayes'],
    'neural_classification': ['mlp_classifier'], 'neural_regression': ['mlp_regressor'],
}

def build_estimator(cfg):
    seed = cfg.seed
    return {
        'logistic_regression': lambda: LogisticRegression(max_iter=500, random_state=seed),
        'random_forest_classifier': lambda: RandomForestClassifier(n_estimators=60, max_depth=12, n_jobs=1, random_state=seed),
        'decision_tree_classifier': lambda: DecisionTreeClassifier(max_depth=12, random_state=seed),
        'gaussian_nb': GaussianNB,
        'linear_regression': LinearRegression,
        'random_forest_regressor': lambda: RandomForestRegressor(n_estimators=60, max_depth=12, n_jobs=1, random_state=seed),
        'decision_tree_regressor': lambda: DecisionTreeRegressor(max_depth=12, random_state=seed),
        'ridge': Ridge,
        'tfidf_logistic': lambda: LogisticRegression(max_iter=500, random_state=seed),
        'tfidf_naive_bayes': MultinomialNB,
        'mlp_classifier': lambda: MLPClassifier(hidden_layer_sizes=tuple(cfg.hidden_layers), max_iter=cfg.iterations, random_state=seed, early_stopping=False),
        'mlp_regressor': lambda: MLPRegressor(hidden_layer_sizes=tuple(cfg.hidden_layers), max_iter=cfg.iterations, random_state=seed, early_stopping=False),
        'kmeans': lambda: KMeans(n_clusters=cfg.clusters, n_init=10, random_state=seed),
    }[cfg.algorithm]()

def preprocess(X, settings):
    numeric = list(X.select_dtypes(include='number').columns)
    categorical = [c for c in X if c not in numeric]
    width = len(numeric) + sum(max(1, X[c].nunique(dropna=False)) for c in categorical)
    if width > settings.max_encoded_features:
        raise ValueError(f'Categorical expansion exceeds {settings.max_encoded_features} features. Remove identifier/free-text columns explicitly before upload or use AutoNLP.')
    if len(X) * width > 5_000_000: raise ValueError('Encoded matrix exceeds 5 million cells; reduce dataset size or cardinality.')
    return ColumnTransformer([
        ('numeric', Pipeline([('impute', SimpleImputer(strategy='median', keep_empty_features=True)), ('scale', StandardScaler())]), numeric),
        ('categorical', Pipeline([('impute', SimpleImputer(strategy='constant', fill_value='__missing__', keep_empty_features=True)),
                                  ('encode', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), categorical),
    ], remainder='drop'), numeric

def clean_features(X):
    X = X.copy()
    for col in X:
        if not pd.api.types.is_numeric_dtype(X[col]):
            X[col] = X[col].map(lambda v: str(v) if pd.notna(v) else np.nan).astype(object)
    return X

def classification_metrics(y, pred, pipe, X):
    labels = list(pipe.classes_)
    result = {'accuracy': float(accuracy_score(y, pred)), 'confusion_matrix': confusion_matrix(y, pred, labels=labels).tolist(),
              'labels': [str(v) for v in labels], 'test_class_distribution': {str(k): int(v) for k,v in pd.Series(y).value_counts().items()}}
    for average in ['macro', 'weighted']:
        p, r, f, _ = precision_recall_fscore_support(y, pred, average=average, zero_division=0)
        result.update({f'precision_{average}': float(p), f'recall_{average}': float(r), f'f1_{average}': float(f)})
    if len(labels) == 2:
        p,r,f,_ = precision_recall_fscore_support(y, pred, average='binary', pos_label=labels[1], zero_division=0)
        result.update(precision_positive=float(p), recall_positive=float(r), f1_positive=float(f), positive_class=str(labels[1]))
    result['roc_auc'] = None
    try:
        proba = pipe.predict_proba(X)
        if len(np.unique(y)) != len(labels): raise ValueError('Evaluation split does not contain every training class.')
        result['roc_auc'] = float(roc_auc_score(y, proba[:,1])) if len(labels) == 2 else float(roc_auc_score(y, proba, labels=labels, multi_class='ovr', average='macro'))
        result['roc_auc_definition'] = 'positive class' if len(labels) == 2 else 'macro one-vs-rest'
    except (ValueError, AttributeError) as exc: result['roc_auc_reason'] = str(exc)
    return result

def regression_metrics(y, pred):
    mse = float(mean_squared_error(y, pred))
    result = {'mae': float(mean_absolute_error(y, pred)), 'mse': mse, 'rmse': float(np.sqrt(mse)), 'r2': None}
    if len(y) < 2 or np.ptp(np.asarray(y)) == 0:
        result['r2_reason'] = 'R² requires at least two evaluation samples and a nonconstant evaluation target.'
    else: result['r2'] = float(r2_score(y, pred, force_finite=False))
    for key, value in list(result.items()):
        if isinstance(value, float) and not np.isfinite(value):
            result[key] = None
            result[f'{key}_reason'] = 'Numerical overflow or undefined evaluation. Rescale the target or inspect the dataset.'
    return result

def finite_json(value):
    if isinstance(value, dict): return {str(k): finite_json(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [finite_json(v) for v in value]
    if isinstance(value, np.generic): return finite_json(value.item())
    if isinstance(value, float) and not np.isfinite(value): return None
    return value

def train(df, cfg, settings):
    if cfg.algorithm not in ALGORITHMS[cfg.task]: raise ValueError('Algorithm is incompatible with this task.')
    if any(h < 2 or h > 128 for h in cfg.hidden_layers): raise ValueError('Hidden layers must contain 2–128 units each.')
    notes = []
    details = {'warnings': notes}
    estimator = build_estimator(cfg)
    if cfg.task == 'clustering':
        if cfg.target: raise ValueError('Clustering does not accept a target. Explicitly remove any label columns before upload.')
        X = clean_features(df)
        if len(X) <= cfg.clusters: raise ValueError('Cluster count must be less than the sample count.')
        prep, numeric = preprocess(X, settings)
        pipe = Pipeline([('preprocess', prep), ('model', estimator)])
        with threadpool_limits(limits=1):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                labels = pipe.fit_predict(X)
                notes.extend(str(w.message) for w in caught)
            transformed = pipe[:-1].transform(X)
            if np.all(np.ptp(transformed, axis=0) == 0): raise ValueError('Clustering requires at least one nonconstant feature.')
            nlabels = len(np.unique(labels))
            metrics = {'silhouette': None, 'inertia': float(pipe[-1].inertia_), 'cluster_distribution': {str(k):int(v) for k,v in pd.Series(labels).value_counts().sort_index().items()}}
            if 1 < nlabels < len(X):
                try: metrics['silhouette'] = float(silhouette_score(transformed, labels, sample_size=min(1000, len(X)), random_state=cfg.seed))
                except ValueError as exc: metrics['silhouette_reason'] = str(exc)
            else: metrics['silhouette_reason'] = 'Silhouette requires between 2 and n−1 distinct clusters.'
        details.update(assignments=labels.tolist(), cluster_summaries={str(k): {c: float(X.loc[labels == k,c].mean()) if X.loc[labels == k,c].notna().any() else None for c in numeric} for k in np.unique(labels)}, evaluation='Clustering fitted on all rows; silhouette is not supervised test accuracy.')
    else:
        if not cfg.target or cfg.target not in df: raise ValueError('Select a valid target column.')
        target = df[cfg.target]
        if target.isna().any() or target.astype(str).str.strip().eq('').any(): raise ValueError('Target contains missing or empty labels. Clean labels before training.')
        classification = cfg.task in ('classification', 'nlp', 'neural_classification')
        if classification:
            y = target.astype(str)
            if y.nunique() < 2 or y.nunique() > 50: raise ValueError('Classification requires 2–50 distinct classes.')
            if y.value_counts().min() < 2: raise ValueError('Each class needs at least two labeled samples.')
        else:
            try: y = pd.to_numeric(target, errors='raise')
            except (TypeError, ValueError): raise ValueError('Regression requires a numeric target.')
            if not np.isfinite(y).all() or y.nunique() < 2: raise ValueError('Regression target must be finite and nonconstant.')
        if len(df) < 12: raise ValueError('Supervised training requires at least 12 labeled rows.')
        if cfg.task == 'nlp':
            if not cfg.text_column or cfg.text_column not in df or cfg.text_column == cfg.target: raise ValueError('Select a text feature distinct from the label.')
            X = df[cfg.text_column].fillna('').astype(str)
            if X.str.strip().eq('').any(): notes.append('Missing or empty text is represented as an empty string.')
            numeric = []
        else:
            X = clean_features(df.drop(columns=[cfg.target]))
            if not len(X.columns): raise ValueError('At least one feature column is required.')
        stratify = None
        if classification:
            ntest = int(np.ceil(len(df) * cfg.test_size))
            if ntest >= y.nunique() and len(df)-ntest >= y.nunique(): stratify = y
            else: notes.append('Split too small to stratify; class coverage may be incomplete.')
        train_idx, test_idx = train_test_split(np.arange(len(df)), test_size=cfg.test_size, random_state=cfg.seed, stratify=stratify)
        Xtrain, Xtest, ytrain, ytest = X.iloc[train_idx], X.iloc[test_idx], y.iloc[train_idx], y.iloc[test_idx]
        if classification and ytrain.nunique() != y.nunique(): raise ValueError('Training split lacks a class. Increase sample size or adjust split.')
        if len(test_idx) < 30: notes.append('Small evaluation sample (<30): metrics may vary substantially across splits.')
        if classification and y.value_counts().max()/y.value_counts().min() > 4: notes.append('Class imbalance detected. Inspect macro F1 and per-class confusion counts.')
        if cfg.task == 'nlp': pipe = Pipeline([('tfidf', TfidfVectorizer(max_features=3000, strip_accents='unicode')), ('model', estimator)])
        else:
            prep, numeric = preprocess(Xtrain, settings)
            pipe = Pipeline([('preprocess', prep), ('model', estimator)])
        with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            pipe.fit(Xtrain, ytrain)
            pred = pipe.predict(Xtest)
            if not classification and not np.isfinite(pred).all(): raise ValueError('Model produced non-finite predictions.')
            metrics = classification_metrics(ytest, pred, pipe, Xtest) if classification else regression_metrics(ytest, pred)
            notes.extend(str(w.message) for w in caught)
        details.update(train_rows=len(train_idx), test_rows=len(test_idx), split_fingerprint=hashlib.sha256(test_idx.tobytes()).hexdigest(),
                       evaluation='Held-out test set. Preprocessing fitted on training rows only.',
                       class_distribution={str(k):int(v) for k,v in y.value_counts().items()} if classification else None)
    features = [cfg.text_column] if cfg.task == 'nlp' else list(X.columns)
    details['features'] = [{'name': c, 'numeric': c in numeric} for c in features]
    # JSON roundtrip rejects any unexpected unserializable values before persistence.
    return pipe, json.loads(json.dumps(finite_json(metrics), allow_nan=False)), finite_json(details)

def predict(pipe, experiment, records):
    features = experiment.details['features']
    expected = {f['name'] for f in features}
    for row in records:
        if set(row) != expected: raise ValueError(f'Prediction fields must exactly match: {", ".join(sorted(expected))}.')
        for feature in features:
            value = row[feature['name']]
            if feature['numeric']:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
                    raise ValueError(f'{feature["name"]} must be a finite number.')
            elif value is not None and (not isinstance(value, str) or len(value) > 16000):
                raise ValueError(f'{feature["name"]} must be text (at most 16000 characters) or null.')
    if experiment.task == 'nlp':
        name = features[0]['name']
        if any(not isinstance(r[name], str) or not r[name].strip() for r in records): raise ValueError('Prediction text must be nonempty.')
        X = [r[name] for r in records]
    else: X = clean_features(pd.DataFrame(records, columns=[f['name'] for f in features]))
    with threadpool_limits(limits=1):
        outputs = pipe.predict(X).tolist()
        if any(isinstance(v, float) and not np.isfinite(v) for v in outputs): raise ValueError('Model produced non-finite predictions.')
        result = {'predictions': finite_json(outputs)}
        if hasattr(pipe, 'predict_proba'):
            result.update(probabilities=finite_json(pipe.predict_proba(X).tolist()), classes=[str(v) for v in pipe.classes_])
        return result
