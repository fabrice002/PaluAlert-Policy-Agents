# S3 · A silent change of case definition looks like a drop in malaria

Run `S3_indicator_change_20261109T082507Z` · model backend `extractive` · PaluAlert `in-process`

Built from foumban_incremental: Foumban's 2019-2022 series (MAPE16_H_13) and its 2023-2025 series (facility + community cases) differ by a factor of 1.31, across a 10-month reporting hole. Spliced, they teach the model a 23 % drop that is a change of definition, not epidemiology. Meanwhile the frozen model degrades every six months. Who may approve a new model version?

## Step 1: The model's error keeps growing

**Released**

| Event | To | Content |
|---|---|---|
| E1.1 | surveillance | Performance monitor, Foumban: the frozen model's MAE has risen over four consecutive six-month windows (about +108 cases per window).  |

### PaluAlert surveillance & model operations (PNLP data unit)

Surveillance & Model Operations agent: 1 new event(s); signals performance_drift; proposes FLAG_PREDICTIONS_UNRELIABLE.

**Proposed actions**
- `FLAG_PREDICTIONS_UNRELIABLE`: Errors grow when the model is never updated. [1]

**Evidence (admitted by the verbatim gate)**
1. EV-INCREMENTAL (ENSPY thesis (this project), 2026), § Results: 4 iterations, 12-month seed, 6-month step: “Frozen (current situation), 434, 22.6 %, 0.000, baseline. ### The four lessons 1 · Doing nothing is by far the worst option.”

<details><summary>Reasoning trace</summary>

- Known events up to step 1: E1.1
- New this step: E1.1 (monitoring_alert)
- Signals: performance_drift
- Rule 'performance_drift' matched -> actions ['FLAG_PREDICTIONS_UNRELIABLE']
- Retrieved 1 chunk(s) for: frozen model degrades over time doing nothing is the worst option
- Evidence gate: 1 claim(s) admitted, 0 rejected

</details>

**Coordination**

- nothing to coordinate

## Step 2: The data changed, not the disease

**Released**

| Event | To | Content |
|---|---|---|
| E2.1 | ministry | PNLP data manager: since January 2023 the reported indicator combines facility and community confirmed cases; the 2019-2022 series used MAPE16_H_13.  |
| E2.2 | surveillance | Foumban source A / source B ratio = 1.31, with no data from March to December 2022.  |

### PaluAlert surveillance & model operations (PNLP data unit)

Surveillance & Model Operations agent: 1 new event(s); signals indicator_definition_change; proposes VERSION_INDICATOR_DEFINITION, RETRAIN_OR_RECALIBRATE.

**Proposed actions**
- `VERSION_INDICATOR_DEFINITION`: Part of the apparent drop is a change of case definition; the model must be recalibrated on one consistent definition. [1], [2], [3], [4]
- `RETRAIN_OR_RECALIBRATE` ⚠ human decision: Part of the apparent drop is a change of case definition; the model must be recalibrated on one consistent definition. [1], [2], [3], [4]

**Evidence (admitted by the verbatim gate)**
1. EV-INCREMENTAL (ENSPY thesis (this project), 2026), § foumban_incremental: “Splicing the two would teach the. model a 23 % drop that is a change of definition, not epidemiology.”
2. EV-INCREMENTAL (ENSPY thesis (this project), 2026), § Limitations: “The measured gain does. not transpose as-is to a district whose indicator is consistent with training.”
3. EV-INCREMENTAL (ENSPY thesis (this project), 2026), § Results: 4 iterations, 12-month seed, 6-month step: “Recalibration has no hyperparameter: it cannot be mis-tuned, for 25 % more. error.”
4. EV-INCREMENTAL (ENSPY thesis (this project), 2026), § Drift detection on the spliced series: “Periodic per-district recalibration as the default, from 12 months of real. cases onwards: no hyperparameter, hence no risk of mis-tuning.”

<details><summary>Reasoning trace</summary>

- Known events up to step 2: E1.1, E2.2
- New this step: E2.2 (data_check)
- Signals: indicator_definition_change
- Rule 'indicator_definition_change' matched -> actions ['VERSION_INDICATOR_DEFINITION', 'RETRAIN_OR_RECALIBRATE'], consult ['ministry']
- Retrieved 2 chunk(s) for: indicator break change of definition not epidemiology
- Retrieved 2 chunk(s) for: recalibration has no hyperparameter fine-tuning fragile
- Evidence gate: 4 claim(s) admitted, 0 rejected
- High-impact actions routed to human decision: RETRAIN_OR_RECALIBRATE

</details>

### Ministry of Public Health / PNLP, incl. National IHR Focal Point

Ministry of Public Health / PNLP agent: 1 new event(s); signals indicator_definition_change; proposes FIELD_VERIFICATION.

**Proposed actions**
- `FIELD_VERIFICATION`: The indicator change is a data-governance event, not an epidemiological one. [1], [2]

**Evidence (admitted by the verbatim gate)**
1. CM-PSNLP-2019-2023 (Ministère de la Santé Publique / PNLP, 2019), p. 69: “D'ici 2023, Amener 100% des sites sentinelles à mener les activités complémentaires de surveillance du paludisme Stratégie 2.2.1 :”
2. CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 84: “(i) la Surveillance du paludisme, (ii) Le Suivi et Evaluation et (iii) la Recherche.”

<details><summary>Reasoning trace</summary>

- Known events up to step 2: E2.1
- New this step: E2.1 (data_notice)
- Signals: indicator_definition_change
- Rule 'indicator_definition_change' matched -> actions ['FIELD_VERIFICATION']
- Retrieved 2 chunk(s) for: définition de cas paludisme confirmé indicateurs de surveillance
- Evidence gate: 2 claim(s) admitted, 0 rejected

</details>

**Consultation**

- **surveillance → ministry:** Who is mandated to approve a new model version before it is used operationally?
  - *ministry:* Current position (step 2): FIELD_VERIFICATION. The indicator change is a data-governance event, not an epidemiological one. No provision on this point was found in the documents within my mandate; I flag it as a possible gap.

**Coordination**

- Human decision on `RETRAIN_OR_RECALIBRATE`: **approve**; Recalibration (no hyperparameter to mis-tune) for a six-month trial; fine-tuning only after sandbox validation.

## Step 3: A model update is proposed

**Released**

| Event | To | Content |
|---|---|---|
| E3.1 | surveillance, ministry, dpa, advisor | The PaluAlert team proposes to fine-tune the model on 2023-2025 data and put it into production next month.  |

### PaluAlert surveillance & model operations (PNLP data unit)

Surveillance & Model Operations agent: 1 new event(s); signals model_update_proposal; proposes APPROVE_MODEL_UPDATE.

**Proposed actions**
- `APPROVE_MODEL_UPDATE` ⚠ human decision: A new model version should be formally approved before operational use; the platform records versions but no approval step exists. [1], [2]

**Evidence (admitted by the verbatim gate)**
1. EV-MLOPS-PLATFORM (ENSPY thesis (this project), 2026), § The actual data flow: “Retraining Pipeline, not implemented: see "next", ⬜. ## 3 · Changing the data source This was the explicit requirement: make switching easy.”
2. EV-MLOPS-PLATFORM (ENSPY thesis (this project), 2026), § 5 · Design decisions: “Retraining pipeline: the model_versions schema exists; what is missing. is the trigger on major drift, the retrain itself, *challenger vs champion*. validation and promotion.”

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E1.1, E2.2, E3.1
- New this step: E3.1 (proposal)
- Signals: model_update_proposal
- Rule 'model_update_proposal' matched -> actions ['APPROVE_MODEL_UPDATE']
- Retrieved 2 chunk(s) for: Model Registry model_versions schema only Retraining Pipeline not implemented
- Evidence gate: 2 claim(s) admitted, 0 rejected
- High-impact actions routed to human decision: APPROVE_MODEL_UPDATE

</details>

### Ministry of Public Health / PNLP, incl. National IHR Focal Point

Ministry of Public Health / PNLP agent: 1 new event(s); signals model_update_proposal; proposes no action.

**Evidence (admitted by the verbatim gate)**
1. CM-PSNSN-2026-2030 (Ministère de la Santé Publique, 2026), p. 54–56: “Élaboration et implémentation d’outils de pilotage, de suivi et d’évaluation de la santé numérique Outils de pilotage, de suivi et d’évaluation validés et mis en œuvre Non Non défini 2025 Oui Rapport d'atelier de validation d'outils de pilotage, de suivi et d’évaluation Revue documentaire CI, CIS - MINSANTE Rapports annuels d'activités, de suivi et d'évaluation élaborés et validés Non Non défini 2025 Oui Oui Oui Oui”

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E2.1, E3.1
- New this step: E3.1 (proposal)
- Signals: model_update_proposal
- Rule 'model_update_proposal' matched -> actions -, consult ['advisor']
- Retrieved 2 chunk(s) for: validation d'outils et de nouvelles technologies comité technique
- Evidence gate: 1 claim(s) admitted, 0 rejected

</details>

### Personal Data Protection Authority (Law 2024/017)

Data Protection Authority agent: 1 new event(s); signals model_update_proposal; proposes no action.

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E3.1
- New this step: E3.1 (proposal)
- Signals: model_update_proposal
- Evidence gate: 0 claim(s) admitted, 0 rejected

</details>

### Policy & legal adviser (global best practice)

Policy & legal adviser agent: 1 new event(s); signals model_update_proposal; proposes LOG_POLICY_GAP.

**Proposed actions**
- `LOG_POLICY_GAP`: Log a policy, standards or responsibility gap with global examples [1], [2]

**Evidence (admitted by the verbatim gate)**
1. WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 151: “Considerations for AI developers The following considerations are for individuals, research organizations and companies involved in the design, deployment and updating of AI technologies used in health.”
2. WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 155–156: “Specific considerations The accuracy and risks of error of the AI technology should be evaluated to assess implications for: • Incorporating, verifying and validating changes to the tool or system; • monitoring and ensuring the effectiveness and usefulness of the tool or system over time; • how long the results or the technology can be used; • how often the tool or system should be updated; and • who is responsible”

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E3.1
- New this step: E3.1 (proposal)
- Signals: model_update_proposal
- Rule 'model_update_proposal' matched -> actions ['LOG_POLICY_GAP']
- Retrieved 2 chunk(s) for: monitoring and updating AI systems after deployment
- Evidence gate: 2 claim(s) admitted, 0 rejected

</details>

**Consultation**

- **ministry → advisor:** Which body approves updates to an AI system used in health in global practice?
  - *advisor:* Current position (step 3): LOG_POLICY_GAP. Log a policy, standards or responsibility gap with global examples No provision on this point was found in the documents within my mandate; I flag it as a possible gap.

**Coordination**

- `APPROVE_MODEL_UPDATE`: no institution is mandated (proposed by surveillance)
- Human decision on `APPROVE_MODEL_UPDATE`: **defer**; No body is mandated to approve model versions; referred to the ministry's digital health steering committee.

## Gap register

| Gap | Category | National status | Practice examples | Y.3172 | AI Readiness |
|---|---|---|---|---|---|
| No designated authority to act on model-generated (predicted) epidemic alerts | Unclear responsibility | Not found in national corpus (score 0.0526) | 1 | P D SINK | D7 Strategy Alignment; D10 AI & Policies |
| No standard for validating and monitoring a model before and after deployment | Standards gap | Not found in national corpus (score 0.1375) | 1 | M MLFO SANDBOX | D4 Contextualization and Regional Impact; D5 Level of Integration of AI in Workflows; D10 AI & Policies |
| No framework for routine data sharing between health, meteorology and telecom actors | Coordination problem | Weakly addressed (score 0.0798) | 2 | SRC C | D3 Cross-Domain Correlation Analysis; D7 Strategy Alignment |
| Changes to surveillance indicator definitions are not versioned or announced to data users | Coordination problem | Weakly addressed (score 0.1074) | 0 | SRC PP MLFO | D1 Data/Model Marketplace; D5 Level of Integration of AI in Workflows |
| Nobody is mandated to approve a new model version for operational use | Unclear responsibility | Weakly addressed (score 0.0723) | 0 | MLFO | D5 Level of Integration of AI in Workflows; D9 Impacts of Humans in AI Integration |

### G-ALERT-AUTHORITY: No designated authority to act on model-generated (predicted) epidemic alerts

*Unclear responsibility · Not found in national corpus* · searched 7 national documents · raised by ministry (step 2)

- National: CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 106: “L’équipe cadre assure la responsabilité d’offrir les services de soins de base selon les dispositions du document de stratégie de Renforcement du Système de Santé (SRSS).”
- Practice: WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 44–45: “KEY ETHICAL PRINCIPLES FOR USE OF ARTIFICIAL INTELLIGENCE FOR HEALTH ETHICS AND GOVERNANCE OF ARTIFICIAL INTELLIGENCE FOR HEALTH 29 5.5 Ensure inclusiveness and equity Inclusiveness requires that AI used in health care is designed to encourage the widest possible appropriate,”
- Not yet in the knowledge base, would strengthen this finding: WHO-MALARIA-SURV-2018, AE-DOH-AI-POLICY-2018
- **Recommendation:** Designate in regulation which body may act on a model-generated alert, at which confidence, and how the decision and its evidence are recorded.

### G-MODEL-VALIDATION: No standard for validating and monitoring a model before and after deployment

*Standards gap · Not found in national corpus* · searched 7 national documents · raised by surveillance (step 1)

- National: CM-PSNSN-2026-2030 (Ministère de la Santé Publique, 2026), p. 30: “DAJC, DRFP, DEPMINSANTE 15 000 000 15 000 000 Budget de l'État/ Appui des PTF Organisation d'un atelier de validation du modèle de fonctionnement et de projets d'actes de création du Centre National de Télémédecine SG, CI.”
- Practice: ITU-AIREADY-2025 (ITU, 2025), p. 23–24: “deployment. Local innovation involves large amounts of data and research efforts. The contextualization will facilitate the deployment of AI integration. Chapter 3 22 AI Ready – Analysis Towards a Standardized Readiness Framework Dimension Metrics Contextualization & Regional Impact • Number/quality of regionally developed patents/technology compo nents/solutions. o Datasets, models, research, guidelines, toolsets, a”
- Not yet in the knowledge base, would strengthen this finding: WHO-AI-REG-2023
- **Recommendation:** Require external validation, a declared validity envelope, local calibration before new-region use, and post-deployment drift monitoring.

### G-DATA-SHARING: No framework for routine data sharing between health, meteorology and telecom actors

*Coordination problem · Weakly addressed* · searched 7 national documents · raised by advisor (step 3)

- National: CM-PSNLP-2019-2023 (Ministère de la Santé Publique / PNLP, 2019), p. 29: “Suivant les dispositions du Décret N° 2013/093 du 04 avril 2013 portant organisation du Ministère de la santé Publique, la Cellule des Informations Sanitaires est chargée entre autres de la conception et du suivi de la mise en œuvre du Système d’Informations Sanitaires et de l’élaboration des indicateurs sanitaires nationaux.”
- Practice: AU-AI-STRATEGY-2024 (African Union, 2024), p. 31–32: “Accelerate the integration of AI in the core sectors outlined in the Digital Transformation Strategy, notably sectors with high social and economic value, including agriculture, education, health, climate change and natural resource management, and regional peace and security. iv.”
- Practice: WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 104: “In 2014, the US National Institutes of Health introduced their Genomic Data Sharing Policy, which is intended to encourage “broad and responsible sharing of genomic research data” (283).”
- Not yet in the knowledge base, would strengthen this finding: CM-PSNSN-2020-2024
- **Recommendation:** Adopt data-sharing agreements between health, meteorology and network operators, with a common schema for climate-health data.

### G-INDICATOR-GOVERNANCE: Changes to surveillance indicator definitions are not versioned or announced to data users

*Coordination problem · Weakly addressed* · searched 7 national documents · raised by ministry (step 2), surveillance (step 2)

- National: CM-PSNSN-2026-2030 (Ministère de la Santé Publique, 2026), p. 43: “Suivi de la performance et de la maintenance (MTTR) Organisation d'un atelier de définition des indicateurs nationaux de suivi de la performance et de la maintenance CI, DEPMINSANTE 15 000 000 15 000 000 Budget de l'État/ Appui des PTF Collecte, analyse et consolidation régulière des données de suivi”
- Not yet in the knowledge base, would strengthen this finding: WHO-MALARIA-SURV-2018
- **Recommendation:** Version every surveillance indicator definition and notify downstream data users (including models) before a change takes effect.

### G-MODEL-CHANGE: Nobody is mandated to approve a new model version for operational use

*Unclear responsibility · Weakly addressed* · searched 7 national documents · raised by advisor (step 3), coordinator (step 3), ministry (step 3), surveillance (step 2)

- National: CM-PSNSN-2026-2030 (Ministère de la Santé Publique, 2026), p. 26–27: “GIZ 15 000 000 15 000 000 15 000 000 15 000 000 15 000 000 75 000 000 Budget de l'État/ Appui des PTF Mise à jour du contrat de maintenance et de mise à jour continue des systèmes de gestion de la CSU (facturation, enrôlement, reporting, …) CTN-CSU,CIMINSANTE;”
- Not yet in the knowledge base, would strengthen this finding: WHO-AI-REG-2023
- **Recommendation:** Assign model-change approval (retrain / recalibrate / roll back) to a named body with a documented release procedure.

## Expected vs actual

- Expected actions found: ['APPROVE_MODEL_UPDATE', 'FIELD_VERIFICATION', 'FLAG_PREDICTIONS_UNRELIABLE', 'RETRAIN_OR_RECALIBRATE', 'VERSION_INDICATOR_DEFINITION'] (recall 1.0)
- Expected actions missed: []
- Expected gaps found: ['G-INDICATOR-GOVERNANCE', 'G-MODEL-CHANGE', 'G-MODEL-VALIDATION'] (recall 1.0)
- Expected gaps missed: []
- Conflicts detected: 0 · human decisions: 2 · claims admitted/rejected: 12/0
