'use client';
import { useRef, useState } from 'react';
import { UploadCloud, Download, Trash2, Database, ChevronRight } from 'lucide-react';
import { api, endpoint, type Dataset } from '@/lib/api';
import { Panel, Empty, ErrorBox, Busy, stamp } from './ui';
export default function DatasetManager({ datasets, refresh }: { datasets: Dataset[]; refresh: () => Promise<void> }) {
  const [selected, setSelected] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState<Dataset | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const dataset = datasets.find(d => d.id === selected) || datasets[0];
  async function upload(file?: File) {
    if (!file) return;
    setError(''); setBusy(true);
    try {
      if (file.size > 10 * 1024 * 1024) throw new Error('Maximum upload size is 10 MiB.');
      const body = new FormData(); body.append('file', file);
      const d = await api<Dataset>('/datasets', { method: 'POST', body });
      setSelected(d.id); await refresh();
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); if (input.current) input.current.value = ''; }
  }
  async function remove() {
    if (!deleting) return; setBusy(true);
    try { await api(`/datasets/${deleting.id}`, { method: 'DELETE' }); setDeleting(null); await refresh(); }
    catch (e) { setError((e as Error).message); setDeleting(null); } finally { setBusy(false); }
  }
  return <div className="stack"><Panel><button className="upload-zone" onClick={() => input.current?.click()} disabled={busy} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); void upload(e.dataTransfer.files[0]); }}><span className="upload-symbol"><UploadCloud size={26} /></span><div><h3>{busy ? <Busy>Reading and validating dataset…</Busy> : 'Bring your data. Build something.'}</h3><p>Drop a CSV or XLSX here, or <span>browse files</span></p><small>UTF-8 CSV · Single-sheet XLSX · Up to 10 MiB / 10,000 rows / 100 columns</small></div></button><input ref={input} type="file" accept=".csv,.xlsx" hidden aria-label="Upload dataset" onChange={e => void upload(e.target.files?.[0])} /></Panel>
    {error && <ErrorBox message={error} />}
    <div className="dataset-layout"><Panel title="Dataset library" aside={<span className="count">{datasets.length}</span>}>{datasets.length ? <div className="dataset-list">{datasets.map(d => <button className={`dataset-item ${d.id === dataset?.id ? 'selected' : ''}`} onClick={() => setSelected(d.id)} key={d.id}><div className="icon-tile green"><Database size={18} /></div><div><strong>{d.name}</strong><small>{d.rows.toLocaleString()} rows · {d.columns.length} columns</small></div><ChevronRight size={15} /></button>)}</div> : <Empty title="Your data starts here">Try samples/customer_churn.csv for your first classification experiment.</Empty>}</Panel>
    {dataset ? <Panel title={dataset.name} aside={<div className="actions"><a className="icon-button" aria-label="Download original" href={endpoint(`/datasets/${dataset.id}/download`)}><Download size={17} /></a><button className="icon-button danger" aria-label="Delete dataset" onClick={() => setDeleting(dataset)}><Trash2 size={17} /></button></div>}><p className="panel-subtitle">Uploaded {stamp(dataset.created_at)} · Previewing {dataset.preview.length} of {dataset.rows} rows</p><div className="table-scroll preview-table"><table><thead><tr>{dataset.columns.map(c => <th key={c.name}>{c.name}<small>{c.dtype} · {c.missing} missing</small></th>)}</tr></thead><tbody>{dataset.preview.map((r,i) => <tr key={i}>{dataset.columns.map(c => <td key={c.name}>{r[c.name] == null ? <span className="null-value">null</span> : String(r[c.name])}</td>)}</tr>)}</tbody></table></div><p className="help padded">Select the target column in your training workspace. No columns are silently discarded.</p></Panel> : <Panel><Empty title="Select a dataset">A schema and row preview will appear here.</Empty></Panel>}</div>
    {deleting && <dialog ref={node => { if (node && !node.open) node.showModal(); }} className="confirm-dialog" aria-labelledby="delete-title" onCancel={() => setDeleting(null)} onKeyDown={e => { if (e.key === 'Escape') setDeleting(null); }}><h2 id="delete-title">Delete {deleting.name}?</h2><p>This removes the original uploaded file. Datasets referenced by experiments are protected.</p><div className="actions"><button autoFocus onClick={() => setDeleting(null)}>Cancel</button><button className="danger-button" disabled={busy} onClick={() => void remove()}>Delete dataset</button></div></dialog>}
  </div>;
}
