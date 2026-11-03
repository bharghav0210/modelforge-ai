# Local demonstration

Launch with `./start.sh`, or reuse existing ModelForge servers on ports 3003/8003. Start on http://localhost:3003. The overview is intentionally empty until you create records; it never fabricates history. Original samples are documented in `samples/README.md`.

1. Open Datasets and upload `samples/customer_churn.csv`. Inspect rows, types and missing counts. Download original verifies the unchanged file.
2. Open AutoML. Choose this dataset, Classification, target `churn`, Logistic Regression, seed 42 and 25% test split. Train. The button reports the real request lifecycle.
3. Inspect accuracy, macro/weighted/positive-class metrics, ROC-AUC, actual-vs-predicted confusion counts, split sizes, configuration and warnings. These are held-out metrics.
4. Give the model a name and Register model. Export its fitted pipeline. Treat the exported joblib as trusted executable code.
5. Open Model Registry, choose the model, edit the prefilled customer values and Run inference. Include a previously unseen contract string to exercise categorical handling. Inspect output probabilities and prediction history.
6. Return to AutoML and train Random Forest Classifier on the same dataset/target/seed/split. Open Experiments, select both successful runs, choose F1 Macro and Compare. Inspect the chart, table and best-run selection. Vary seed in another run to see the compatibility warning.
7. Upload `samples/house_prices.csv`. In AutoML choose Regression, `price`, and Linear Regression. Train and inspect MAE, MSE, RMSE and R². Register and predict if desired.
8. Upload `samples/product_reviews.csv`. In AutoNLP select text `review`, target `sentiment`, and TF-IDF Logistic. Train, inspect confusion counts, register and predict new text.
9. Upload `samples/customer_segments.csv`. AutoML → Clustering → K-Means → 3 clusters. Inspect silhouette, cluster sizes, numeric means and every row's assignment. There is no accuracy label. Register to predict a new customer's cluster.
10. Open Neural Network Lab. It is explicitly a CPU-friendly sklearn MLP baseline. Select churn classification, `churn`, layers `32,16`, and 150 iterations. Train and inspect metrics and any convergence warning. MLP regression is also available.
11. Open GenAI Lab. It shows an actual provider check, installed models if any, or a useful offline state. Generation is available only with a real local model. ModelForge does not download models.
12. Open Settings to inspect fixed limits and storage/trust configuration.
13. Refresh the browser, return to Experiments and confirm saved runs. Backend restart also preserves experiment/registry/prediction records and fitted pipelines.

## Automated acceptance journey

Run `npm --prefix frontend run test:e2e` against an available ModelForge frontend at localhost:3003. The tests use the same real FastAPI app on a second loopback address (`127.0.0.2:8003`) and disposable storage. All model results are actual calculations. The adapter redirects Chromium requests; no ML response or dataset content is mocked. Existing backend data remains untouched. The fixture is cleaned up after the run. Port 8003 on that second loopback address must be available.

The desktop journey uploads datasets, trains two classification algorithms, compares runs, registers/exports a model, predicts an unseen category, trains regression/NLP/clustering/MLP, checks the offline provider, navigates every module, and reloads experiment history. The mobile journey separately uploads a sample, opens/cancels the deletion confirmation and checks page overflow. Browser evidence is written only after the full desktop test succeeds. Backend tests separately verify restart persistence and all supported algorithms.

Actual completed steps, test counts and model metrics are in [VERIFICATION.md](VERIFICATION.md). Screenshots and JSON evidence are generated from the isolated test workspace, not seeded into the real dashboard.
