'use client';
import { useState } from 'react';
import { Download, Box, Send } from 'lucide-react';
import { post, endpoint, type Model, type Dataset, type Prediction } from '@/lib/api';
import { Panel, Empty, MetricCards, Badge, nice, ErrorBox, Busy, stamp } from './ui';
export default function Registry({ models, datasets, predictions, refresh }: { models: Model[]; datasets: Dataset[]; predictions: Prediction[]; refresh: () => Promise<void> }) {
  const [selected, setSelected] = useState('');
  const model = models.find(m => m.id === selected) || models[0];
  const [values, setValues] = useState<Record<string,string>>({});
  const [result, setResult] = useState<Record<string,unknown> | null>(null);
  const [error, setError] = useState(''); const [busy,setBusy] = useState(false);
  if (!models.length) return <Panel><Empty title="A home for your trained models">Train an experiment, inspect its metrics, then choose Register model to make it available for prediction and export.</Empty></Panel>;
  const example = datasets.find(d => d.id === model.dataset_id)?.preview[0];
  const value = (key: string) => values[key] ?? String(example?.[key] ?? '');
  async function infer(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError(''); setResult(null);
    try {
      const row = Object.fromEntries(model.features.map(f => [f.name, f.numeric ? Number(value(f.name)) : value(f.name)]));
      const response = await post<Record<string,unknown>>(`/models/${model.id}/predict`, { records: [row] });
      setResult(response); await refresh();
    } catch(e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <div className="stack"><div className="model-grid">{models.map(m => <button key={m.id} className={`model-card ${m.id===model.id ? 'selected' : ''}`} onClick={() => { setSelected(m.id); setValues({}); setResult(null); setError(''); }}><div className="model-card-top"><span className="icon-tile violet"><Box size={21} /></span><Badge value="registered" /></div><h3>{m.name}</h3><p>{nice(m.algorithm)}</p><small>{nice(m.task)} · {m.id.slice(0,8)}</small></button>)}</div><div className="training-layout"><Panel title="Run a prediction" aside={<span className="step-label">FITTED PIPELINE</span>}><div className="padded"><p className="muted">{model.name} · Fields are prefilled from the dataset’s first row. Edit them for a new prediction.</p><form className="form-stack" onSubmit={infer}>{model.features.map(f => <label key={f.name}>{f.name}<span className="field-type" aria-hidden="true">{f.numeric ? 'number' : 'text'}</span>{model.task==='nlp' ? <textarea aria-label={f.name} value={value(f.name)} required maxLength={16000} onChange={e => setValues({...values,[f.name]:e.target.value})} /> : <input aria-label={f.name} required type={f.numeric ? 'number' : 'text'} step="any" value={value(f.name)} maxLength={16000} onChange={e => setValues({...values,[f.name]:e.target.value})} />}</label>)}{error && <ErrorBox message={error} />}<button className="primary" disabled={busy}>{busy ? <Busy>Predicting…</Busy> : <><Send size={16} />Run inference</>}</button></form>{result && <div className="prediction-result" role="status"><span>MODEL OUTPUT</span><strong>{((result.predictions as (string|number)[]) || []).map(v => typeof v==='number' ? v.toFixed(3) : v).join(', ')}</strong><details><summary>Prediction details</summary><pre>{JSON.stringify(result,null,2)}</pre></details></div>}</div></Panel><Panel title="Model metadata" aside={<a className="button" href={endpoint(`/models/${model.id}/export`)}><Download size={16} />Export</a>}><div className="padded"><p className="help">Registered {stamp(model.created_at)}. Metrics below are from the saved experiment evaluation.</p><MetricCards metrics={model.metrics} /><div className="notice warning">Serialized artifacts are trusted executable code. Load only files you trust.</div></div></Panel></div><Panel title="Prediction history">{predictions.length ? <div className="table-scroll"><table><thead><tr><th>Model</th><th>Prediction</th><th>Recorded</th></tr></thead><tbody>{predictions.map(p => <tr key={p.id}><td>{models.find(m => m.id===p.model_id)?.name || p.model_id.slice(0,8)}</td><td className="mono">{JSON.stringify(p.outputs.predictions)}</td><td>{stamp(p.created_at)}</td></tr>)}</tbody></table></div> : <Empty title="No predictions yet" />}</Panel></div>;
}
