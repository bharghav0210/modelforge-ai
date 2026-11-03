# ML methodology

All metrics originate in real scikit-learn execution. No model search, hyperparameter optimization, GPU deep learning or transformer training is claimed.

## Supervised evaluation

Datasets require at least 12 labeled rows. Missing/blank labels are rejected rather than dropped. Regression targets must be finite numeric values and nonconstant; classification requires 2–50 classes and at least two examples per class. Targets never enter the feature list. A reproducible seed and test fraction (15–40%) define the split. Classification stratifies when both partitions can hold every class. Missing training classes are rejected. Small test sets and imbalance produce explicit warnings.

Split occurs before any preprocessing is fitted. Numeric features use training medians and StandardScaler. Categorical features use a constant missing marker and OneHotEncoder with unknown-category handling. Empty features are retained; neither target leakage nor silent feature deletion is allowed. Fitted ColumnTransformer and estimator form one Pipeline saved and reused for inference. Prediction requires the complete expected schema, finite numeric JSON values and bounded categorical strings; extra fields, missing fields and target injection are rejected. Numeric null inputs are rejected; categorical nulls use the fitted missing-value handling.

Classification supports logistic regression, a 60-tree random forest, depth-limited decision tree and Gaussian Naive Bayes. Evaluation includes accuracy, macro and weighted precision/recall/F1, ordered confusion counts, full/test class distributions, and probability-based ROC-AUC. Binary positive class is the second sorted estimator class, named explicitly. Multiclass ROC-AUC is macro one-versus-rest. Undefined class precision/recall uses zero. Missing class coverage or unavailable probabilities produce an unavailable ROC-AUC with a reason.

Regression supports linear regression, a 60-tree random forest, depth-limited decision tree and Ridge. Metrics are MAE, MSE, RMSE and R². Constant evaluation targets or fewer than two evaluation samples make R² unavailable with a reason. Non-finite values are never emitted as JSON metrics; overflow is marked unavailable and explained.

## Clustering

K-Means uses 2–12 clusters, n_init=10, a seed, the same numeric/categorical preprocessing and scaling. It fits all uploaded features; upload a feature-only dataset to omit any external labels. It rejects insufficient samples, invalid cluster counts and constant transformed data. Results include row assignments in original order, cluster sizes, numeric means, inertia and silhouette where valid. Silhouette uses at most 1,000 reproducibly sampled rows. Degenerate sampling/cluster configurations yield unavailable with a reason. These are unsupervised diagnostics, never supervised accuracy. The fitted pipeline supports cluster prediction.

## Text and neural baselines

AutoNLP uses one selected text column, training-only TF-IDF (at most 3,000 features), and logistic regression or MultinomialNB. Empty training text becomes an empty string with a warning; empty vocabulary fails usefully. Missing labels are rejected. The target and text columns must differ. Labels, splits and classification metrics follow the shared conventions. Prediction requires nonempty text.

The Neural Network Lab uses sklearn MLPClassifier/MLPRegressor: 1–3 layers of 2–128 units, 20–500 iterations, deterministic seed, no early-stopping split, and the shared tabular pipeline/evaluation. Convergence warnings are persisted and visible. A saved model can be usable without converging; its actual held-out metrics still need inspection. Poor or negative R² is not hidden. This is a CPU baseline, not image/CNN/PyTorch AutoDL.

## Comparisons and limits

Comparisons require successful runs from the same dataset and exact task. Lower MAE/MSE/RMSE/inertia is better; other supported metrics sort descending. Different target, text feature, seed, split fraction or split fingerprint produces a warning and disables best-model selection. Same-seed splits make algorithm comparisons reproducible but a single split remains a noisy estimate. There is no cross-validation or tuning claim. Synthetic sample scores are demonstrations, not benchmarks.

Dense tabular encoding is bounded to 2,000 features and 5 million cells, with at most 10,000 rows and 100 columns. Forests use one job and depth 12. Training sets threadpool limits to one. The launcher also bounds BLAS/OpenMP threads. Local execution time depends on data and hardware; the synchronous training endpoint has no hard process timeout or cancellation.
