# Release verification — ModelForge AI

Verified 2 November 2026 (Asia/Kolkata) for a trusted-local, single-user source-code portfolio. This does not certify public hosted deployment.

## Executed release checks

| Check | Fresh result |
|---|---|
| Backend `backend/.venv/bin/python -m pytest backend/tests -q` with temporary storage and one BLAS/OpenMP thread | **46 passed, 0 failed, 0 skipped** |
| Frontend ESLint | Exit 0, no diagnostics |
| Strict TypeScript `tsc --noEmit --incremental false` | Exit 0, `strict: true` |
| Next.js 16.4.3 production build, Webpack | Passed from a clean source copy with no old build output |
| Separate production directory `.next-verification` | Fresh build passed; same eight browser checks passed against it |
| Original browser journeys | **2 passed, 0 failed, 0 skipped** |
| Focused production routes | **6 passed, 0 failed, 0 skipped**: `/automl`, `/autonlp`, `/neural`, `/genai`, `/experiments`, `/models`, direct and client navigation |
| Disposable API health and actual backend process restart | Healthy; dashboard/datasets/experiments/models/predictions snapshots unchanged |

Builds were sequential across projects. Installed dependencies and Chrome were reused; no packages, browsers or models were downloaded. Tests used disposable databases/uploads/artifacts. Existing development servers and personal data were not used for test mutations. Browser origins retain ports 3003/8003; a free loopback transport port serves the isolated production copy while the existing development server occupies 3003. Logs and the release report are retained outside this repository under `../portfolio-audit/` in the development workspace.

The original journey now waits for the destination URL, page heading and connected API before continuing. Reload follows completed navigation; no arbitrary delay, skipped assertion or mocked model result was added. Chrome's local-network permission is granted for the test origin so the real isolated API can receive multipart uploads.

## ML training and inference

Backend tests execute classification (logistic regression, random forest, decision tree, GaussianNB), regression (linear, random forest, decision tree, Ridge), K-Means, TF-IDF logistic/MultinomialNB and MLP classification/regression. Each trained pipeline is registered, exported and used for prediction. Persistence tests restart the app and infer with a saved registered artifact.

Leakage checks mutate held-out numeric/categorical values and text tokens, then verify that imputation/scaler/encoder/TF-IDF fitting uses training data only. Tests cover invalid targets, malformed/oversized inputs, non-finite/undefined metrics, incompatible comparisons, prediction schemas, concurrency and controlled artifact paths. Synthetic fixture metrics are demonstrations, not benchmarks.

The complete browser journey executes training, model registration/export, inference with an unseen category, compatible comparison, NLP, clustering, regression and neural training. It verifies persisted history after reload. Mobile navigation, cancellation and horizontal layout also pass.

## Navigation and runtime errors

Fresh production-build and captured production-server logs contain no Instant Navigation, uncovered-Suspense or blocking warning. The six route checks assert substantive workspace controls rather than accepting only a heading or HTTP 200. Browser checks capture page errors; the complete journey reports none. This closes the earlier fresh-build evidence gap. Logs from the user's pre-existing development process were not accessible and are not represented as reviewed.

## Reproduce

```bash
# From repository root, with installed dependencies:
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  backend/.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend run lint
npm --prefix frontend run typecheck
MODELFORGE_BUILD_DIR=.next-verification npm --prefix frontend run build
MODELFORGE_BUILD_DIR=.next-verification ./start.sh --production
# With the frontend available on 3003 and Chrome installed:
npm --prefix frontend run test:e2e
```

The browser fixture starts a temporary API on `127.0.0.2:8003`; it does not use the personal backend store. The release-only extra route assertions were kept in the external release harness. Do not build into a directory currently used by a server. Bind production and development launches to loopback; supplied scripts already do so.

## Known limitations and Ollama

The live Ollama availability check returned **unavailable**, with no installed models returned. Offline detection and generation failure (HTTP 503) passed. **Real LLM generation was not tested**; no response was fabricated and no model was downloaded.

Single-user local use only: no authentication, tenant isolation, hostile-artifact sandbox, public deployment hardening, GPU training, cross-validation or hyperparameter search. Joblib artifacts are executable trusted code; never load untrusted artifacts. Training is synchronous and bounded by input/model limits, without hard process timeout or cancellation. Single-holdout metrics are noisy; convergence warnings and poor scores remain visible.

The pre-existing development frontend was observed listening on all interfaces. Release-owned production tests bind to loopback and the supplied launch defaults are loopback. The existing process was left running because its lifecycle was not owned by this release pass; its owner should relaunch it using the documented script before network use.
