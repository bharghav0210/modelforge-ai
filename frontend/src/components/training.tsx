'use client';
import { useState } from 'react';
import { Play, ArrowRight, Cpu, Layers3, FlaskConical } from 'lucide-react';
import { post, type Dataset, type Experiment, type Settings } from '@/lib/api';
import { Panel, Empty, ErrorBox, Busy, nice } from './ui';
const defaults: Record<string, string> = { classification: 'logistic_regression', regression: 'linear_regression', clustering: 'kmeans', nlp: 'tfidf_logistic', neural_classification: 'mlp_classifier', neural_regression: 'mlp_regressor' };
export default function Training({ mode, datasets, settings, onComplete }: { mode: string; datasets: Dataset[]; settings: Settings; onComplete: (e: Experiment) => void }) {
  const initial = mode === 'autonlp' ? 'nlp' : mode === 'neural' ? 'neural_classification' : 'classification';
  const [task, setTask] = useState(initial);
  const [datasetId, setDatasetId] = useState(datasets[0]?.id || '');
  const [target, setTarget] = useState('');
  const [text, setText] = useState('');
  const [algorithm, setAlgorithm] = useState(defaults[initial]);
  const [seed, setSeed] = useState(42);
  const [split, setSplit] = useState(0.25);
  const [clusters, setClusters] = useState(3);
  const [layers, setLayers] = useState('32,16');
  const [iterations, setIterations] = useState(150);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const dataset = datasets.find(d => d.id === datasetId);
  const selectedTarget = target || (task === 'nlp' ? dataset?.columns.at(-1)?.name : dataset?.columns.at(-1)?.name) || '';
  const selectedText = text || dataset?.columns[0]?.name || '';
  if (!datasets.length) return <Panel><Empty title="Start with your data">Open Datasets to upload a CSV or XLSX. Sample files are included in the repository.</Empty></Panel>;
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const hidden = layers.split(',').map(s => Number(s.trim()));
      if (mode === 'neural' && (hidden.length > 3 || hidden.some(v => !Number.isInteger(v) || v < 2 || v > 128))) throw new Error('Enter 1–3 comma-separated layers, each with 2–128 units.');
      const result = await post<Experiment>(mode === 'autonlp' ? '/autonlp/train' : mode === 'neural' ? '/neural/train' : '/automl/train', { dataset_id: datasetId, task, algorithm, target: task === 'clustering' ? null : selectedTarget, text_column: task === 'nlp' ? selectedText : null, seed, test_size: split, clusters, hidden_layers: mode === 'neural' ? hidden : [32,16], iterations });
      onComplete(result);
      if (result.status === 'failed') setError(result.error || 'Training failed. See experiment history.');
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <div className="training-layout"><Panel title="Configure experiment" aside={<span className="step-label">01 / SETUP</span>}><form onSubmit={submit} className="form-stack">
    <label>Dataset<select value={datasetId} onChange={e => { setDatasetId(e.target.value); setTarget(''); setText(''); }} disabled={busy}>{datasets.map(d => <option key={d.id} value={d.id}>{d.name} · {d.rows} rows</option>)}</select></label>
    {mode !== 'autonlp' && <label>Learning task<select value={task} disabled={busy} onChange={e => { setTask(e.target.value); setAlgorithm(defaults[e.target.value]); }}>{(mode === 'neural' ? ['neural_classification','neural_regression'] : ['classification','regression','clustering']).map(t => <option key={t} value={t}>{nice(t)}</option>)}</select></label>}
    {task !== 'clustering' && <label>Target column<select value={selectedTarget} disabled={busy} onChange={e => setTarget(e.target.value)}>{dataset?.columns.map(c => <option value={c.name} key={c.name}>{c.name}</option>)}</select></label>}
    {task === 'nlp' && <label>Text column<select value={selectedText} disabled={busy} onChange={e => setText(e.target.value)}>{dataset?.columns.map(c => <option value={c.name} key={c.name}>{c.name}</option>)}</select></label>}
    <label>Algorithm<select value={algorithm} disabled={busy} onChange={e => setAlgorithm(e.target.value)}>{settings.algorithms[task]?.map(a => <option key={a} value={a}>{nice(a)}</option>)}</select></label>
    <div className="form-row"><label>Random seed<input type="number" min="0" max="2147483647" value={seed} required onChange={e => setSeed(Number(e.target.value))} /></label>{task !== 'clustering' ? <label>Test split<select value={split} onChange={e => setSplit(Number(e.target.value))}><option value={0.2}>20% test / 80% train</option><option value={0.25}>25% test / 75% train</option><option value={0.3}>30% test / 70% train</option><option value={0.4}>40% test / 60% train</option></select></label> : <label>Cluster count<input type="number" min="2" max="12" value={clusters} onChange={e => setClusters(Number(e.target.value))} required /></label>}</div>
    {mode === 'neural' && <div className="form-row"><label>Hidden layers<input value={layers} onChange={e => setLayers(e.target.value)} required placeholder="32,16" /></label><label>Maximum iterations<input type="number" min="20" max="500" value={iterations} onChange={e => setIterations(Number(e.target.value))} required /></label></div>}
    {error && <ErrorBox message={error} />}
    <button className="primary full" disabled={busy} type="submit">{busy ? <Busy>Training model — waiting for evaluation</Busy> : <><Play size={16} />Train model<ArrowRight size={16} /></>}</button>
    <p className="help">Training runs synchronously on your CPU. Keep this page open until the request finishes.</p>
  </form></Panel><div className="stack"><Panel title="Built for honest evaluation"><div className="explain-item"><div className="icon-tile violet"><FlaskConical size={21} /></div><div><h3>{task === 'clustering' ? 'Unsupervised discovery' : 'Unseen data, real metrics'}</h3><p>{task === 'clustering' ? 'K-Means fits all rows. Silhouette measures cluster separation, not prediction accuracy. Upload only the features you want to cluster.' : 'The target stays out of features. A held-out test split measures how the model generalizes.'}</p></div></div><div className="explain-item"><div className="icon-tile blue"><Layers3 size={21} /></div><div><h3>A single fitted pipeline</h3><p>{task === 'nlp' ? 'TF-IDF vocabulary is fitted on training text only. The saved pipeline transforms new text consistently.' : 'Imputation, categorical encoding, scaling and the estimator are saved together for reliable inference.'}</p></div></div><div className="explain-item"><div className="icon-tile green"><Cpu size={21} /></div><div><h3>{mode === 'neural' ? 'CPU-friendly neural-network baseline' : 'Workstation-sized experiments'}</h3><p>{mode === 'neural' ? 'Scikit-learn MLP with bounded layers and iterations. Inspect convergence warnings after training.' : 'Bounded settings, reproducible seeds, and one training request at a time.'}</p></div></div></Panel>{dataset && <Panel title="Dataset snapshot"><div className="snapshot"><div><strong>{dataset.rows.toLocaleString()}</strong><span>Rows</span></div><div><strong>{dataset.columns.length}</strong><span>Columns</span></div><div><strong>{dataset.columns.reduce((n,c) => n+c.missing,0)}</strong><span>Missing values</span></div></div><div className="chips">{dataset.columns.map(c => <span key={c.name} className="chip">{c.name}<small>{c.numeric ? '#' : 'Aa'}</small></span>)}</div></Panel>}</div></div>;
}
