export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8003';
export const endpoint = (path: string) => `${API_BASE}/api/v1${path}`;
export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(endpoint(path), { ...options, cache: 'no-store', headers: { ...(options?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options?.headers } });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error?.message || `Request failed (${response.status})`);
  return body as T;
}
export const post = <T>(path: string, data: unknown) => api<T>(path, { method: 'POST', body: JSON.stringify(data) });
export type Column = { name: string; dtype: string; numeric: boolean; missing: number };
export type Dataset = { id: string; name: string; rows: number; columns: Column[]; preview: Record<string, string | number | null>[]; created_at: string };
export type Metrics = Record<string, number | string | null | number[][] | string[] | Record<string, number>>;
export type Experiment = { id: string; dataset_id: string; task: string; algorithm: string; config: Record<string, string | number | number[] | null>; metrics: Metrics; status: string; started_at: string; finished_at: string | null; duration: number | null; error: string | null; has_artifact: boolean; details: { warnings?: string[]; features?: { name: string; numeric: boolean }[]; train_rows?: number; test_rows?: number; evaluation?: string; cluster_summaries?: Record<string, Record<string, number | null>>; assignments?: number[]; split_fingerprint?: string; class_distribution?: Record<string,number> | null } };
export type Model = { id: string; name: string; experiment_id: string; dataset_id: string; task: string; algorithm: string; metrics: Metrics; features: { name: string; numeric: boolean }[]; created_at: string };
export type Prediction = { id: string; model_id: string; created_at: string; inputs: Record<string, unknown>; outputs: { predictions: (string | number)[] } };
export type Dashboard = { datasets: number; experiments: number; models: number; predictions: number; succeeded: number; failed: number; recent_runs: Experiment[]; recent_predictions: Prediction[] };
export type Provider = { available: boolean; models: string[]; message: string };
export type Settings = { scope: string; max_upload_mib: number; max_rows: number; max_columns: number; max_encoded_features: number; ollama_url: string; training_concurrency: number; artifact_warning: string; algorithms: Record<string, string[]> };
