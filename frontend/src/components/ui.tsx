'use client';
import type { ReactNode } from 'react';
import { AlertCircle, Loader2 } from 'lucide-react';
import type { Experiment, Metrics } from '@/lib/api';
export const nice = (text: string) => text.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
export const stamp = (text: string) => new Date(text).toLocaleString();
export const score = (value: unknown) => typeof value === 'number' ? (Number.isInteger(value) ? value.toString() : value.toFixed(4)) : value == null ? 'Unavailable' : String(value);
export function Panel({ children, title, aside, className = '' }: { children: ReactNode; title?: string; aside?: ReactNode; className?: string }) { return <section className={`panel ${className}`}>{title && <div className="panel-heading"><h2>{title}</h2>{aside}</div>}{children}</section>; }
export function Empty({ title, children }: { title: string; children?: ReactNode }) { return <div className="empty"><div className="empty-mark">◇</div><h3>{title}</h3><p>{children || 'Your work will appear here as you build.'}</p></div>; }
export function ErrorBox({ message }: { message: string }) { return <div className="notice error" role="alert"><AlertCircle size={17} /><span>{message}</span></div>; }
export function Busy({ children = 'Working…' }: { children?: ReactNode }) { return <span className="busy" role="status"><Loader2 className="spin" size={16} />{children}</span>; }
export function Badge({ value }: { value: string }) { return <span className={`badge ${value}`}>{value}</span>; }
export function MetricCards({ metrics }: { metrics: Metrics }) { return <div className="metric-grid">{Object.entries(metrics).filter(([,v]) => typeof v === 'number' || v === null).map(([k,v]) => <div className="metric" key={k}><span>{nice(k)}</span><strong>{score(v)}</strong>{v === null && typeof metrics[`${k}_reason`] === 'string' && <small>{String(metrics[`${k}_reason`])}</small>}</div>)}</div>; }
export function RunTable({ runs, onSelect, datasets = {} }: { runs: Experiment[]; onSelect: (e: Experiment) => void; datasets?: Record<string, string> }) { return runs.length ? <div className="table-scroll"><table><thead><tr><th>Experiment / algorithm</th><th>Dataset</th><th>Task</th><th>Status</th><th>Duration</th><th>Started</th></tr></thead><tbody>{runs.map(e => <tr key={e.id}><td><button className="text-button" onClick={() => onSelect(e)}>{nice(e.algorithm)}</button><small className="mono">{e.id.slice(0,8)}</small></td><td>{datasets[e.dataset_id] || e.dataset_id.slice(0,8)}</td><td>{nice(e.task)}</td><td><Badge value={e.status} /></td><td>{e.duration == null ? '—' : `${e.duration.toFixed(2)}s`}</td><td className="muted">{stamp(e.started_at)}</td></tr>)}</tbody></table></div> : <Empty title="No experiments yet">Upload a dataset and train your first model.</Empty>; }
