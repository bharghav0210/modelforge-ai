# ModelForge AI

An independent local workspace for dataset management, real CPU model training, honest evaluation, experiment history and saved-model inference. Built with Next.js App Router, TypeScript, Tailwind, Recharts, Lucide, FastAPI, SQLAlchemy/SQLite and scikit-learn.

**Local single-user portfolio MVP.** This is not a public, authenticated training service. All displayed metrics are computed from actual runs. GenAI requires your own optional Ollama installation; offline providers are reported explicitly.

## Launch

From this repository:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
./start.sh
```

Open **http://localhost:3003**. API documentation: **http://localhost:8003/docs**. The launcher binds only to 127.0.0.1, checks both ports before starting, and never kills an existing listener. Ctrl+C stops only processes launched by that invocation. If a port is occupied, identify the owner and reuse or stop it yourself. Other portfolio projects and their ports are not involved.

For a production frontend:

```bash
MODELFORGE_BUILD_DIR=.next-verification npm --prefix frontend run build
MODELFORGE_BUILD_DIR=.next-verification ./start.sh --production
```

The frontend build/dev scripts use Next.js Webpack because the execution environment blocks Turbopack's CSS-worker socket. Tailwind uses its standard PostCSS plugin. Existing dependencies are retained. External font downloads are not required. The production commands above use the ignored `.next-verification` directory, separate from a development server's `.next` files. Always build current source before starting production; do not serve an older retained build. Both commands keep frontend port 3003 and loopback binding.

Optional frontend configuration: create `frontend/.env.local` with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8003` (already the fallback). Backend configuration comes from process environment variables: `MODELFORGE_DATA_DIR` and `OLLAMA_BASE_URL`, shown in `.env.example`. Do not overwrite an existing environment file. SQLite metadata and original uploads / generated artifacts persist in `backend/data` by default. The frontend's public API URL is baked in at build time.

Separate terminals are also supported:

```bash
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8003
# In another terminal:
npm --prefix frontend run dev
```

## Workspaces

| Workspace | Function |
|---|---|
| Overview | Persisted counts, recent experiments/inference, task mix, quick actions |
| Datasets | CSV/XLSX upload, schema/missing counts, preview, original download, protected deletion |
| AutoML | Classification, regression and K-Means configuration, training and evaluation |
| AutoNLP | Training-only TF-IDF with logistic regression or MultinomialNB |
| Neural Network Lab | CPU-friendly MLP classification/regression with bounded layers and iterations |
| GenAI Lab | Ollama status, installed models, system instruction, temperature and actual generation |
| Experiments | Failure/success history, filters, detail, metric charts and compatible comparisons |
| Model Registry | Explicit registration, trusted artifact export, structured/text/cluster inference, prediction history |
| Settings | Environment, fixed resource limits and storage/trust information |

Classification: logistic regression, random forest, decision tree, Gaussian Naive Bayes. Regression: linear regression, random forest, decision tree, Ridge. All supervised tabular transformations are fitted after the train/test split and saved with the estimator. Unknown categories are handled by the fitted encoder. Training is synchronous with an actual request busy state, not simulated percentages.

Uploads: 10 MiB, 10,000 rows, 100 columns; UTF-8 CSV or one-sheet XLSX. Malformed row widths, duplicate headers, invalid encoding, infinity and empty data are rejected. Dense feature expansion is bounded to 2,000 features / 5 million cells. Target labels cannot be missing. See [ML methodology](docs/ML_METHODOLOGY.md) for split, metric and algorithm details.

Start with `samples/customer_churn.csv`: train classification on `churn`, inspect held-out metrics, register a model, then edit customer fields and predict. Other original, reproducible samples cover house-price regression, unlabeled customer segments and review sentiment. See [sample schemas](samples/README.md) and [demo journey](docs/DEMO.md).

## Optional local LLM

Run Ollama separately at http://127.0.0.1:11434 and manually install a model appropriate for your hardware. No models are downloaded by ModelForge. `OLLAMA_BASE_URL` can be set before backend startup. Open GenAI Lab and check the connection. Offline generation returns a clear error while the remaining modules continue working. Real generation is verified only when a request to an installed model succeeds.

## Verify

```bash
./verify.sh
# With a frontend already available at localhost:3003 and Chrome installed:
./verify.sh --browser
```

Backend tests always use temporary databases, uploads and artifacts. Browser tests also start the same real API with temporary storage on `127.0.0.2:8003`; Chromium forwards browser API requests to that second loopback address without mocking calculations or touching the live `127.0.0.1:8003` backend database. No additional TCP port is used. Browser page reload confirms persistence, and backend tests additionally restart the app and reload a registered artifact. The fixture forces an unavailable Ollama port to verify offline behavior. Set `CHROME_PATH` if Chrome is installed somewhere other than `/usr/bin/google-chrome`. Browser tests leave screenshots/evidence in docs and clean up their isolated backend. Do not run a production build concurrently with a dev server using the same `.next` directory; stop your owned frontend or use a separate build directory first.

See [verification](docs/VERIFICATION.md) for actual results, evidence and limitations, [architecture](docs/ARCHITECTURE.md) for components and endpoints, and [security](docs/SECURITY.md) for the trust model. **Never deserialize joblib/pickle models from untrusted sources.** Only server-generated, registered artifacts can be loaded through this application. No arbitrary model upload/import exists.
