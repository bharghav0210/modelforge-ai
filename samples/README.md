# Original synthetic datasets

Regenerate with `backend/.venv/bin/python samples/generate.py` (seed 42). Regeneration updates only these bundled sample CSVs, never uploaded data. These noisy examples demonstrate functionality, not benchmark performance. All labels and records are fictional.

| File | Rows | Schema / target |
|---|---:|---|
| customer_churn.csv | 240 | age (years), tenure_months, monthly_charge (fictional currency), contract (monthly/annual/two-year), **churn** (yes/no). Labels are sampled from a probability influenced by tenure, price and contract. |
| house_prices.csv | 240 | area_sqft, bedrooms, location (central/suburban/rural), house_age (years), **price** (fictional currency). Price includes additive Gaussian noise; age is intentionally weak. |
| customer_segments.csv | 240 | annual_spend (fictional currency), visits (count), channel (online/store). No target; overlapping latent populations. |
| product_reviews.csv | 180 | **review** (text feature), **sentiment** (positive/negative label). Generated phrasing, shared context and about 13% probabilistic label noise. |

Small, generated datasets can yield optimistic scores because related patterns recur. Metrics are demonstrations on one held-out split, not evidence of real-world quality.
