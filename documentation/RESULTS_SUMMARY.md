# RESULTS_SUMMARY.md

**Climate-Based Malaria Prediction for Cameroon Health Districts**
*Malaria Prediction Based on Environmental Data Collected Through IoT Sensors*

A summary for supervisors and collaborators. All numbers are traceable to
`files (2)/malaria_full_protocol.ipynb` (the declared source of truth) unless a
different notebook is named.

---

## 1 · Research objective

Predict monthly malaria risk at Cameroonian health-district resolution from
environmental variables an IoT sensor network can measure in the field, and
determine **where that prediction stops being trustworthy**.

Two prediction tasks:

| Task | Target | Definition |
|---|---|---|
| Regression | `log_incidence` | `log1p(cases / population × 1000)` |
| Classification | `high` | incidence above the **75th percentile of its region** |

The regional threshold matters: "high" means high *for that ecological zone*, not
high nationally. Northern Cameroon's baseline is several times the South's.

---

## 2 · Methodology

Ten-phase protocol adapted from Nkiruka et al. (2021), *Informatics in Medicine
Unlocked* 22:100508, extended with the spatial and out-of-sample validation the
original lacks.

The central experimental design is a **three-regime contrast**, so the value added
by each feature family is always visible:

| Regime | n features | Contents | Deployable without case surveillance? |
|---|---|---|---|
| **RAW** | 5 | month + 4 raw climate variables | ✅ |
| **RAW+ENG** (NO-LAG) | 16 | + seasonal encoding, geography, climate lags 1–2 | ✅ |
| **+lag_cases** (LAG) | 20 | + `cases_lag1/2/3`, `rolling_mean_3m` | ❌ |

Four evaluation regimes, each stricter than the last: random-split KFold →
time-aware TimeSeriesSplit → Leave-One-Region-Out → external test on unseen years.

---

## 3 · Datasets

| Source | Coverage | Scale |
|---|---|---|
| **PNLP surveillance** (`MAPE16_H_13`, confirmed cases) | Jan 2019 – Feb 2022 | 1 795 health areas → 197 districts × 38 months |
| **Climate reanalysis**: Open-Meteo/ERA5, cross-checked against NASA POWER | Jan 2019 – Feb 2022 | 136 290 daily records, 118 locations, 4 variables |
| **PNLP ground truth** (external test) | 2023–2025 | Foumban, 36 months |
| **Yaoundé deployment climate** | Feb – Jun 2026 | 139 daily records |

Final modelling frame: **7 092 district-months** (197 districts, 10 regions,
36 months) after dropping undefined lags: **6 895** when case lags are required.
Class balance 5 281 low / 1 811 high (`scale_pos_weight ≈ 2.87`).

---

## 4 · Preprocessing pipeline

1. **Numeric repair**: decimal-comma geographic fields → floats.
2. **Health area → district**: geography averaged, area and population summed,
   cluster modal, cases summed.
3. **Wide → long**: 38 `<Mon>_<Year>_MAPE16_H_13` columns melted, French month
   abbreviations parsed.
4. **Climate daily → monthly**: mean for temperature / humidity / pressure,
   **sum** for precipitation.
5. **Spatial join**: 197 districts against 118 climate locations: exact match →
   a 10-entry curated correction map → `rapidfuzz` token-sort at **≥ 55**.
6. **Imputation**: region×month mean, then global mean.
7. **Feature engineering**: incidence rate, `sin_month`/`cos_month`, climate lags
   1–2, case lags 1–3, 3-month rolling case mean, `log1p` targets, per-region 75th
   percentile threshold.

---

## 5 · Models evaluated

**Regression (13)** · LinearReg, Ridge, Lasso, ElasticNet, DecisionTree,
RandomForest, ExtraTrees, GradBoost, XGBoost, LightGBM, CatBoost, SVR, KNN.

**Classification (12)** · LogisticReg, DecisionTree, RandomForest, ExtraTrees,
GradBoost, XGBoost, LightGBM, CatBoost, SVM, KNN, NaiveBayes, MLP.

**Deep learning** · LSTM and GRU with sliding-window sequences, early stopping,
random-search tuning and gradient saliency (`malaria_lstm_gru.ipynb`;
also in `malaria_outbreak_prediction.ipynb` in PyTorch). **Did not beat gradient
boosting.** `Notebook_1` reports negative R² for its LSTM on both tasks.

Total: 52 regression configurations × 6 metrics and 96 classification
configurations × 9 metrics, then Optuna TPE (25 trials) on the top-2 per task.

---

## 6 · Best-performing models

**XGBoost wins both tasks**, with LightGBM statistically indistinguishable.

| | Regressor | Classifier |
|---|---|---|
| Model | XGBoost | XGBoost |
| Tuned params | 500 trees, depth 5, lr 0.062, subsample 0.715, colsample 0.817 | 400 trees, depth 5, lr 0.110, subsample 0.936, colsample 0.831 |
| Optuna best (inner CV) | R² 0.792 | F1 0.747 |
| **KFold (optimistic)** | **R² 0.769** | **F1 0.725** |
| **TimeSeriesSplit (no look-ahead)** | **R² 0.628** | **F1 0.655** |

Both are persisted in `saved_models/` and `deployment_bundle/`.

---

## 7 · Evaluation metrics: the validity envelope

This table is the thesis's central result. Each row is a more realistic test.

| Evaluation regime | Best F1 | Regression R² | What it simulates |
|---|---|---|---|
| RAW · KFold | 0.518 | 0.198 | raw climate, no engineering |
| ENG · KFold *(leaky)* | **0.725** | **0.769** | interpolation within the observed window |
| ENG · TimeSeriesSplit *(no look-ahead)* | **0.651** | **0.628** | **forecasting future months: the operational number** |
| +lag_cases · TimeSeriesSplit | 0.695 | 0.765 | future months with case history available |
| ENG · Leave-One-Region-Out | **0.372** | **−0.461** | deployment in an unseen region |
| **External: Foumban 2023–25** | **0.250** | **−1.74** | **real unseen years and district** |

> The R² above was **corrected on 31 July 2026**. The figure `−68.65` circulated
> previously is an artefact of a corrupted model load: see §9 finding 6 and
> the Foumban experiments of the full thesis package. The classification F1 is unaffected.

**Full classification panel for the best model** (ENG, balanced, KFold):
Accuracy 0.846 · Precision 0.668 · Recall 0.794 · F1 0.725 · Specificity 0.864 ·
ROC-AUC 0.913 · PR-AUC 0.807 · MCC 0.625 · Balanced Accuracy 0.829.

### Naive baselines: how much is real skill?

Same TimeSeriesSplit folds (`malaria_full_protocol_2.ipynb`, Phase 3.5):

| Target | Persistence (ŷₜ = yₜ₋₁) | Seasonal mean | **Environment model (ENG)** |
|---|---|---|---|
| `log_incidence` | **0.751** | 0.533 | 0.623 |
| `log_cases` | **0.892** | 0.799 | 0.836 |

The deployable environment-only model **beats pure seasonality** (+0.089 / +0.038)
but **loses to trivial persistence** (−0.129 / −0.056). Persistence is not
deployable: PNLP reporting latency means last month's confirmed count is
unavailable at forecast time: so this gap is the measured **cost of
deployability**, and it is exactly what the recursive case-history chain recovers.

### Recursive deployment simulation

The `+lag_cases` model needs last month's cases. With sensors only, it must consume
its own predictions:

| | R² (log cases) | MAE (cases) |
|---|---|---|
| Oracle (real lags) | 0.927 | 286 |
| **Recursive (synthetic lags)** | **0.895** | 293 |
| Two-model chain (NO-LAG bootstrap → LAG) | 0.875 | 321 |

Degradation is modest, and error grows with the forecast horizon as each
prediction's error compounds.

---

## 8 · Feature importance and SHAP

**Native gain, tuned regressor**

| Rank | Feature | Importance | Family |
|---|---|---|---|
| 1 | SHP_lat | 0.145 | Geography |
| 2 | cluster | 0.131 | Geography |
| 3 | SHP_lon | 0.126 | Geography |
| 4 | SHP_Area | 0.097 | Geography |
| 5 | sin_month | 0.083 | Seasonal |
| 6 | cos_month | 0.077 | Seasonal |

**Geography dominates both tasks.** The four geographic features take the top four
positions for regression; `SHP_Area` and `SHP_lon` lead for classification. Climate
ranks below seasonality: for the classifier, `Pressure_hPa` (0.064) and
`Humidity_pct_lag1` (0.058) are the strongest climate contributors.

**Interpretation.** Geography encodes the structural ecological-zone baseline: the
between-district burden difference: while climate modulates at the margin. This is
also the mechanistic explanation for the LORO collapse: remove a region from
training and the model has no anchor for its baseline. The importance ranking and
the spatial-validation failure corroborate each other.

**With case history** (`+lag_cases`): `cases_lag1` alone takes **0.332** of the
importance mass and `rolling_mean_3m` 0.048, displacing geography. SHAP beeswarm
(Figure 14) confirms it, which is precisely why the recursive simulation is
required rather than optional.

**Per-prediction SHAP** (`predictions_yaounde_mai_juin_2026.ipynb`,
`generate_all_figures.ipynb` Part 6) decomposes each 2026 forecast into waterfall,
global-importance and heatmap views for both models. For the NO-LAG 2026 Yaoundé
forecast (Figure 19) the four largest contributions are `SHP_Area` (+0.66),
`cluster` (+0.61), `SHP_lat` (+0.46) and `SHP_lon` (+0.12), geography again, an
order of magnitude above anything else, with `Pressure_hPa` (+0.09) the leading
climate contributor and `Humidity_pct` and `sin_month` the only consistently
negative ones.

**Epidemiological alignment.** Temperature and precipitation (current and lagged)
are the leading *climate* drivers, consistent with Nkiruka et al. (2021) and
established malaria epidemiology: mosquito breeding and parasite development are
temperature- and rainfall-dependent, with a delay of weeks. The Yaoundé lagged
correlation confirms this: temperature correlation peaks at **lag 2 (r = 0.41)**.

---

## 9 · Key findings

**1 · Feature engineering is decisive.** Regression R² rises from 0.198 to 0.765
(+0.567) moving from raw climate to the engineered set; classification F1 from
0.503 to 0.736. Raw monthly climate alone is a weak predictor at district
resolution. Seasonal encoding, geographic context and climate lags are what make
the signal usable.

**2 · Temporal leakage is real but modest.** Random-split KFold overstates F1 by a
mean of **0.071** across 12 classifiers relative to TimeSeriesSplit. The time-ordered
number (F1 ≈ 0.65) is the one to quote for an operational early-warning system.

**3 · Spatial generalisation is the binding constraint.** Leave-One-Region-Out
collapses to mean F1 0.372 ± 0.158 and mean R² **−0.461** ± 0.574. Northern, drier
regions transfer best (Nord R² +0.402); southern forested regions worst (Sud
−1.584, Littoral −0.931). A model trained on nine regions does **not** generalise
to a tenth. The same result appears independently at district level
(`malaria_iot_notebook2.ipynb`: LODO median F1-macro ≈ 0.32), with the additional
observation that **simpler models transfer better** (20 features 0.32 vs 44
features 0.29).

**4 · Climate-only prediction has an information ceiling.** Three independent
lines of evidence converge: `Notebook_1` finds climate-only models plateau at
R² ≈ 0.30 regardless of model class or lag depth; `malaria_iot_notebook2`'s
seven-stage ablation ceilings at F1-macro ≈ 0.34; and adding case history lifts
R² from 0.774 to 0.843. The **predictor set, not the architecture, is the limit**,
which is why deep learning did not help.

**5 · Case history is the largest available signal, and it is borrowed.**
Persistence reaches R² 0.751–0.892; `cases_lag1` alone carries a third of the
model's importance mass. But that gain comes from malaria's month-to-month
autocorrelation, not from environmental understanding, and it needs surveillance
data a sensor-only deployment does not have. The recursive chain recovers most of
it (R² 0.895 vs oracle 0.927) at the cost of horizon-dependent error growth.

**6 · The external test failed, but less badly, and in the opposite direction,
than previously reported.** ⚠️ Scored against 36 months of real 2023–2025 PNLP data
for Foumban, the frozen models give **R² −1.74** (log-incidence scale) and
**F1 0.250**, **over**-predicting mean incidence by **28 %** (9.73 predicted vs
7.59 observed). The classifier keeps some ranking ability (ROC-AUC 0.664, recall
0.75) but at precision 0.15: 17 false alarms in 32 normal months. R² is still
negative, so the climate-only model remains worse than predicting the mean:
**internal cross-validation, however careful, substantially overstates real
deployment performance.**

> **Correction (31 July 2026).** The figures `R² = −68.65` and "85 %
> under-prediction" quoted from this notebook's stored output are an artefact of a
> corrupted model load: `final_regressor.joblib` raises
> `XGBoostError: input stream corrupted` on modern xgboost. The `.json` export is
> the verified Phase-8.5 model (500 trees, depth 5, `base_score` = the training
> mean, in-sample R² 0.918) and reproduces the notebook's own written diagnostic
> exactly. **Only the regressor was affected; the classification numbers stand.**
> Full evidence in the Foumban experiments folder of the full thesis package (not in this repository).

**6b · The Foumban failure is temporal drift, not spatial transfer.** Foumban
averaged 9.67 / 1000 during 2019–2022 training and 7.59 / 1000 during 2023–2025:
a **21.5 % decline** that closely matches the +28 % over-prediction. Foumban sat at
the **67th national percentile** during training, so this is not a
"below-average district" problem. And the failure is largely an artefact of the
evaluation protocol: supplying the real case history that Foumban actually reports
cuts MAE by 61 % and removes the bias entirely (see finding 6c).

**6c · Feeding the model case history fixes most of it.** On an identical 24-month
window, teacher forcing with real case lags gives MAE 261 and **R² +0.05** against
the baseline's MAE 664 and R² −3.23. Recursive forecasting (sensors only) reaches
MAE 333: but that is statistically indistinguishable from a naive expanding mean
(339), so a climate model consuming its own output adds nothing measurable on this
district.

**7 · Precipitation cannot be summarised by a monthly mean.** Coefficient of
variation 100.9 %, versus 13.4 % for temperature and 4.4 % for pressure. The
statistical justification for lagged and rolling rainfall features.

---

## 10 · Limitations

**Data**

1. **Short training window**: 36–38 usable months (2019-01 to 2022-02) covers
   barely three annual cycles, limiting what a seasonal model can learn.
2. **Fuzzy district matching**: 197 districts mapped onto 118 climate locations at
   a permissive `token_sort_ratio ≥ 55`. A 10-entry manual correction map exists
   because automatic matches were wrong; some accepted pairs (`Manoka→Manjo`,
   `Ndom→Ndop`) are name-similarity matches between different places. A known
   source of climate-attribution noise, not quantified.
3. **Reanalysis, not sensors**: models are trained on ERA5 gridded reanalysis but
   intended for in-situ IoT readings. The distribution shift between the two is
   untested.
4. **Passive surveillance**: PNLP confirmed cases reflect health-seeking behaviour
   and reporting completeness, not true incidence. Population denominators are
   static across the study period.

**Methodological**

5. **Model selection on the leaky regime**: the source-of-truth notebook selects
   and tunes on random-split KFold, then reports TimeSeriesSplit separately. Both
   are recorded, and the notebook states this explicitly, but selection under
   time-aware CV would be more defensible.
6. **Geography dominance makes it partly a spatial lookup**: the model largely
   learns *where* a district is and adjusts marginally for climate. This inflates
   in-sample scores and explains the LORO collapse.
7. **No spatial autocorrelation handling**: neighbouring districts are treated as
   independent; no CAR/kriging term, and no cross-district contagion.
8. **Small-sample lag correlations**: the Yaoundé lag analysis uses 38 city-level
   months, and the notebook labels it indicative rather than definitive.
9. **No uncertainty quantification**: point predictions only; no prediction
   intervals, which an operational alert system needs.

**Open inconsistencies to resolve before submission**

10. ✅ **The "regressor↔classifier contradiction" is a stale artifact, not a real
    problem: good news, verified.** `predictions_yaounde_mai_juin_2026.ipynb`
    flags an unresolved contradiction: its regressor predicts ~2.10/1000 for Biyem
    Assi (far *below* the 14.28/1000 threshold) while its classifier calls both
    months HIGH, and the notebook warns against presenting the two side by side at
    the defence. **Re-scoring the identical feature rows against the current saved
    models shows the contradiction disappears:**

    | | May 2026 | June 2026 |
    |---|---|---|
    | Regressor (`final_regressor.json`, log_incidence) | **14.60 /1000** (~5 991 cases) | **12.86 /1000** (~5 277 cases) |
    | NO-LAG regressor (`regressor_nolag.joblib`, log_cases) | 13.28 /1000 (5 448 cases) | 12.52 /1000 (5 139 cases) |
    | Classifier P(high) | **0.748** → HIGH | **0.572** → HIGH |
    | Biyem Assi observed 2019–2022 | 14.04 /1000 mean (~5 763 cases/month) | - |

    Two independently trained regressors and the historical mean all agree at
    13–15/1000, straddling the 14.28 threshold, exactly what a P(high) of 0.75
    then 0.57 should look like. The classifier reproduces **bit-for-bit**
    (0.748 / 0.572 identical to the notebook), which confirms the feature rows and
    the district-static row are correct; only the regressor output differs. The
    notebook also printed a SHAP base value of 0.4977 (≈ 0.64/1000) where the saved
    regressor has `base_score = 2.1156` (≈ 8.3/1000). The stored 2.10/1000 output
    therefore came from a stale or mis-scaled regressor artifact loaded in that
    session, not from a modelling flaw. **Action: re-run that notebook against the
    current `final_regressor` and delete the contradiction discussion.**
    *(Verified using the `.json` model exports, since the `.joblib` files cannot be
    loaded under xgboost 3.x: see limitation 14.)*
11. ⚠️ **Corrupted regressor output in the Foumban evaluation: same root cause as
    limitation 10.** The markdown diagnostic reports a **+28 %** positive bias (mean
    predicted 9.74); the executed output shows **−85 %** (mean predicted 1.13).
    **The prose is correct and the stored output is the artefact**: the reverse of
    what was originally assumed here. Verified in the Foumban experiments of the thesis package: the
    `.json` model has 500 trees of depth 5 (matching the recorded Optuna
    parameters), `base_score` 2.1156 (= the training mean of `log_incidence`) and
    in-sample R² 0.918, and it reproduces 9.73 / 1000 exactly. The real baseline is
    **R² −1.74, MAPE 31.4 %, bias +28.2 %**, not R² −68.65 / −85 %. Classification
    numbers are unaffected. **Action: re-run that notebook against the `.json`
    models and update every quotation of the −68.65 figure.**
12. ⚠️ **A failing cell.** `evaluation_foumban_2023_2025.ipynb` cell 14 (per-year
    breakdown) raises `TypeError: cannot convert the series to <class 'int'>`, so
    that table is empty. Fix: `int((s['high']==1) & (s['pred_class']==1)).sum()`
    should be `int(((s['high']==1) & (s['pred_class']==1)).sum())`.
13. ⚠️ **Phase 3.5 is missing from the source of truth.** The naive-baseline
    comparison exists only in `malaria_full_protocol_1/_2.ipynb`. It pre-empts the
    most obvious examiner challenge and should be merged in.
14. ⚠️ **The `.joblib` models are not loadable under xgboost ≥ 3.0**: they raise
    `XGBoostError: input stream corrupted`, because the binary serialisation format
    changed. The `.json` exports in `files (2)/` (`final_regressor.json`,
    `final_classifier.json`, `best_lag_*.json`) load fine and are version-portable.
    **The `deployment_bundle/*.joblib` files have no `.json` counterpart**: they
    load under the current environment, but a future xgboost upgrade would strand
    them and with them the FastAPI service. Export all deployment models to `.json`
    (`model.save_model('...json')`) before archiving the thesis.

---

## 11 · Future work

**Immediate (before submission)**

1. Re-run `predictions_yaounde_mai_juin_2026.ipynb` against the current
   `final_regressor` and remove the contradiction discussion: it resolves to
   ~14.6/1000 and ~12.9/1000, consistent with the classifier (limitation 10).
2. Merge Phase 3.5 naive baselines into the source-of-truth notebook.
3. Update the Foumban prose and fix the failing cell.
4. Export the `deployment_bundle` models to `.json` for version portability.
5. Report the external test result prominently rather than only internal CV:
   it is the most defensible thing in the thesis.

**Methodological**

6. **Recalibration for new regions**: the LORO result and the Foumban failure both
   point the same way. Test how many months of local case data are needed before a
   fine-tuned model beats the global one; that number is the deployment
   prescription.
7. **Bias correction**: the Foumban evaluation already sketches an offset learned
   on one year and validated on the next. Formalise it as a per-district
   calibration layer.
8. **Threshold tuning**: precision 0.15 at the default 0.50 cut-off is not
   operationally usable. The notebook suggests 0.80; tune it against an explicit
   false-alarm cost ratio.
9. **Uncertainty quantification**: quantile regression or conformal prediction to
   attach intervals to every alert.
10. **Spatial modelling**: add a spatial random effect or graph structure over the
    district adjacency already encoded in `SHP_NEIGB`.

**Data**

11. **Extend the series**: the 2023–2025 PNLP data used for the Foumban test
    exists for other districts; retraining on 2019–2025 would nearly triple the
    training window and directly address limitation 1.
12. **Audit the district↔climate mapping**: validate the fuzzy matches against
    real coordinates and quantify the misattribution rate.
13. **Sensor-vs-reanalysis validation**: once IoT readings accumulate, compare
    them against ERA5 for the same district-months and quantify the shift.
14. **Add non-climate covariates**: bed-net coverage, IRS campaigns, health-facility
    density, land use. The R² ≈ 0.30 climate-only ceiling is unlikely to move
    without them.

**Deployment**

15. **Prospective validation**: the May/June 2026 forecasts are on record. Compare
    them against the reported counts when PNLP publishes; that is a real
    pre-registered test.
16. **Operationalise the service**: `app/` is a working skeleton (SQLite, no auth).
    Production needs PostGIS, Alembic migrations, JWT auth and the React dashboard.

---

## 12 · Reproducing these results

| Deliverable | Purpose |
|---|---|
| `generate_all_figures.ipynb` | Regenerates all 19 thesis figures top-to-bottom (≈20–35 min) |
| `FIGURE_INVENTORY.md` | Figure → notebook → cell → related figures provenance |
| `THESIS_WORKFLOW.md` | Full raw-data-to-conclusions workflow |
| `PROJECT_NOTEBOOK_MAP.md` | All 37 notebooks + dependency graph |

Environment verified with pandas 2.3.3, scikit-learn 1.8.0, xgboost 3.3.0,
lightgbm 4.6.0, catboost 1.2.10, optuna 4.8.0, shap 0.46.0, matplotlib 3.10.9,
rapidfuzz 3.12.2. All seeds fixed at 42.
