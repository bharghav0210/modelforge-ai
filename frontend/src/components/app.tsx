'use client';
import { useCallback, useEffect, useState, type ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Box, LayoutDashboard, Database, Network, Sparkles, BrainCircuit, MessageSquare, FlaskConical, Settings as SettingsIcon, ArrowUpRight, ChevronRight, Menu, RefreshCw, X, ShieldCheck, FolderOpen } from 'lucide-react';
import { api, API_BASE, type Dataset, type Experiment, type Model, type Prediction, type Dashboard, type Provider, type Settings } from '@/lib/api';
import { Panel, ErrorBox, Busy } from './ui';
import Overview from './overview';
import DatasetManager from './dataset-manager';
import Training from './training';
import ExperimentDetail from './experiment-detail';
import Experiments from './experiments';
import Registry from './registry';
import GenAI from './genai';
const nav = [
  {href:'/',label:'Overview',icon:LayoutDashboard,description:'Your ideas. Your models. Your workspace.'},
  {href:'/datasets',label:'Datasets',icon:Database,description:'A clear view of the data behind your next model.'},
  {href:'/automl',label:'AutoML',icon:Network,description:'Train, evaluate, and discover what your data can do.'},
  {href:'/autonlp',label:'AutoNLP',icon:Sparkles,description:'Build focused text classifiers with real evaluation.'},
  {href:'/neural',label:'Neural Network Lab',icon:BrainCircuit,description:'A CPU-friendly neural-network baseline, built for experimentation.'},
  {href:'/genai',label:'GenAI Lab',icon:MessageSquare,description:'A playground for your own local language models.'},
  {href:'/experiments',label:'Experiments',icon:FlaskConical,description:'Every configuration. Every result. One place.'},
  {href:'/models',label:'Model Registry',icon:Box,description:'Keep your best models close. Put them to work.'},
  {href:'/settings',label:'Settings',icon:SettingsIcon,description:'Understand your local environment and resource limits.'},
];
export default function App({ children }: { children: ReactNode }) {
  const pathname = usePathname(); const current = nav.find(n=>n.href===pathname) || nav[0];
  const [datasets,setDatasets]=useState<Dataset[]>([]); const [runs,setRuns]=useState<Experiment[]>([]); const [models,setModels]=useState<Model[]>([]); const [predictions,setPredictions]=useState<Prediction[]>([]); const [dashboard,setDashboard]=useState<Dashboard | null>(null); const [settings,setSettings]=useState<Settings | null>(null); const [provider,setProvider]=useState<Provider | null>(null);
  const [error,setError]=useState(''); const [loading,setLoading]=useState(true); const [refreshing,setRefreshing]=useState(false); const [menu,setMenu]=useState(false); const [detail,setDetail]=useState<Experiment | null>(null);
  const refresh = useCallback(() => Promise.all([api<Dataset[]>('/datasets'),api<Experiment[]>('/experiments'),api<Model[]>('/models'),api<Prediction[]>('/predictions'),api<Dashboard>('/dashboard'),api<Settings>('/settings')]).then(([d,e,m,p,s,c]) => {
    setDatasets(d);setRuns(e);setModels(m);setPredictions(p);setDashboard(s);setSettings(c);setError('');
  }).catch((e: Error) => setError(e.message)).finally(() => {setLoading(false);setRefreshing(false);}),[setDatasets,setRuns,setModels,setPredictions,setDashboard,setSettings,setError,setLoading,setRefreshing]);
  useEffect(()=>{void refresh(); api<Provider>('/genai/status').then(setProvider).catch(()=>setProvider({available:false,models:[],message:'API unavailable. Start the backend on port 8003.'}));},[refresh]);
  async function completed(e: Experiment) { setDetail(e);await refresh(); }
  return <div className="app-shell"><aside className={`sidebar ${menu ? 'show' : ''}`}><Link href="/" className="brand" onClick={()=>{setMenu(false);setDetail(null);}}><span className="brand-symbol"><Box size={25} strokeWidth={1.6} /></span><span>ModelForge<span className="brand-ai">AI</span><small>THE EXPERIMENT WORKSPACE</small></span></Link><button className="mobile-close icon-button" aria-label="Close navigation" onClick={()=>setMenu(false)}><X size={20} /></button><div className="workspace-switch"><span className="workspace-avatar">M</span><div><strong>Personal workspace</strong><small>Local environment</small></div><ChevronRight size={14} /></div><nav aria-label="Main navigation"><p className="nav-section">WORKSPACE</p>{nav.slice(0,2).map(n=><Link key={n.href} href={n.href} className={pathname===n.href?'active':''} onClick={()=>{setMenu(false);setDetail(null);}}><n.icon size={18} />{n.label}</Link>)}<p className="nav-section">BUILD & EXPERIMENT</p>{nav.slice(2,6).map(n=><Link key={n.href} href={n.href} className={pathname===n.href?'active':''} onClick={()=>{setMenu(false);setDetail(null);}}><n.icon size={18} />{n.label}{n.href==='/genai' && <span className="nav-local">LOCAL</span>}</Link>)}<p className="nav-section">MANAGE</p>{nav.slice(6).map(n=><Link key={n.href} href={n.href} className={pathname===n.href?'active':''} onClick={()=>{setMenu(false);setDetail(null);}}><n.icon size={18} />{n.label}</Link>)}</nav><div className="sidebar-bottom"><div className="local-note"><ShieldCheck size={18} /><div><strong>Your machine. Your models.</strong><p>A local, single-user workspace.</p></div></div><div className="profile"><span className="user-avatar">ML</span><div><strong>Model builder</strong><small>Local portfolio · v1.0</small></div><span className="dot green-dot" /></div></div></aside>{menu && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={()=>setMenu(false)} />}
    <div className="main-shell"><header className="topbar"><div className="breadcrumb"><button className="mobile-menu icon-button" aria-label="Open navigation" onClick={()=>setMenu(true)}><Menu size={20} /></button><span>Workspace</span><ChevronRight size={13} /><strong>{current.label}</strong></div><div className="topbar-right"><span className={`connection ${error ? 'disconnected' : ''}`}><span className="dot" />{error ? 'API disconnected' : loading ? 'Connecting' : 'Local API connected'}</span><a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer" className="docs-link">API docs<ArrowUpRight size={14} /></a><span className="user-avatar small">ML</span></div></header><main><div className="page-heading"><div><p className="eyebrow">MODELFORGE / {current.label.toUpperCase()}</p><h1>{current.label === 'Overview' ? 'Workspace overview' : current.label}</h1><p>{current.description}</p></div><button className="button refresh-button" disabled={refreshing || loading} onClick={()=>{setRefreshing(true);void refresh();}}><RefreshCw size={15} className={refreshing?'spin':''} />Refresh</button></div>
      {children}
      {error && <ErrorBox message={`${error}. Ensure the ModelForge backend is running at ${API_BASE}.`} />}
      {loading ? <Panel><div className="empty"><Busy>Connecting to your workspace…</Busy></div></Panel> : settings && dashboard && <>
        {detail && <ExperimentDetail key={detail.id} experiment={detail} models={models} refresh={refresh} close={()=>setDetail(null)} />}
        {!detail && <>
          {pathname==='/' && <Overview stats={dashboard} datasets={datasets} runs={runs} onSelect={setDetail} />}
          {pathname==='/datasets' && <DatasetManager datasets={datasets} refresh={refresh} />}
          {['/automl','/autonlp','/neural'].includes(pathname) && <Training key={pathname} mode={pathname.slice(1)} datasets={datasets} settings={settings} onComplete={e=>void completed(e)} />}
          {pathname==='/experiments' && <Experiments runs={runs} datasets={datasets} onSelect={setDetail} />}
          {pathname==='/models' && <Registry models={models} datasets={datasets} predictions={predictions} refresh={refresh} />}
          {pathname==='/genai' && <GenAI provider={provider} setProvider={setProvider} />}
          {pathname==='/settings' && <div className="stack"><Panel title="Local environment" aside={<ShieldCheck size={18} />}><div className="settings-grid">{Object.entries({Scope:settings.scope,'API endpoint':API_BASE,'Frontend port':3003,'Backend port':8003,'Upload limit':`${settings.max_upload_mib} MiB`,'Maximum rows':settings.max_rows,'Maximum columns':settings.max_columns,'Encoded feature limit':settings.max_encoded_features,'Concurrent training jobs':settings.training_concurrency,'Ollama provider':settings.ollama_url}).map(([k,v])=><div key={k}><span>{k}</span><strong>{v}</strong></div>)}</div></Panel><Panel title="Storage & trust"><div className="padded"><div className="explain-item"><span className="icon-tile violet"><FolderOpen size={21} /></span><div><h3>Durable, project-local storage</h3><p>SQLite metadata, original datasets and fitted pipelines live in backend/data by default. Restarting the app preserves them. Configure MODELFORGE_DATA_DIR before startup to use another controlled directory.</p></div></div><div className="notice warning">{settings.artifact_warning}</div><p className="help">Trusted local single-user MVP. No authentication, public hosting, multi-tenant isolation, GPU training or hyperparameter optimization. Keep services bound to loopback.</p></div></Panel></div>}
        </>}
      </>}
    <footer><span><Box size={13} />ModelForge AI</span><span>Built to experiment. Designed to understand.</span><span>LOCAL WORKSPACE <span className="dot" /></span></footer></main></div></div>;
}
