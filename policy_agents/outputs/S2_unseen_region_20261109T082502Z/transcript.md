# S2 · Scaling the early-warning model to a region it has never been validated in

Run `S2_unseen_region_20261109T082502Z` · model backend `extractive` · PaluAlert `in-process`

The thesis validity envelope says the model ranks districts well nationally (Spearman 0.859) but its absolute forecasts fail in unseen regions (Leave-One-Region-Out R² -0.461) and unseen years (external R² -1.74). A ministerial instruction to scale up, an offer of free fine-tuning on a foreign cloud and a rumour from across the Nigerian border arrive at different agents at different times.

## Step 1: Instruction to deploy nationwide

**Released**

| Event | To | Content |
|---|---|---|
| E1.1 | ministry | The Minister instructs that PaluAlert be used in all 10 regions, including Extrême-Nord, from the 2027 rainy season.  |
| E1.2 | surveillance | Produce the June-August 2027 outlook for Mokolo (Extrême-Nord) with climatological inputs, ahead of the national roll-out.  |
| E1.3 | dpa | MINSANTE plans to use the model's district risk scores to prioritise bed-net distribution and community health worker visits.  |

### PaluAlert surveillance & model operations (PNLP data unit)

Surveillance & Model Operations agent: 1 new event(s); signals low_risk_output, nationwide_deployment_request; proposes LOCAL_CALIBRATION_PERIOD, RANK_ONLY_OUTPUT, PUBLISH_TRANSPARENCY_NOTE.

Tool `predict_series` on Mokolo (Extreme Nord):

| Month | Model | Cases | /1000 | Risk | Threshold |
|---|---|---|---|---|---|
| 2027-06 | NO-LAG | 1051 | 3.45 | Low | 11.59 |
| 2027-07 | LAG | 1127 | 3.69 | Low | 11.59 |
| 2027-08 | LAG | 1669 | 5.47 | Low | 11.59 |

**Proposed actions**
- `LOCAL_CALIBRATION_PERIOD`: Validation shows the model ranks districts well nationally but its absolute forecasts fail in unseen regions and years. [1], [2], [3]
- `RANK_ONLY_OUTPUT`: Validation shows the model ranks districts well nationally but its absolute forecasts fail in unseen regions and years. [1], [2], [3]
- `PUBLISH_TRANSPARENCY_NOTE`: Validation shows the model ranks districts well nationally but its absolute forecasts fail in unseen regions and years. [1], [2], [3]

**Evidence (admitted by the verbatim gate)**
1. EV-RESULTS-SUMMARY (ENSPY thesis (this project), 2026), § 6 · Best-performing models: “Both are persisted in saved_models/ and deployment_bundle/. ## 7 · Evaluation metrics: the validity envelope This table is the thesis's central result.”
2. EV-NATIONAL-VALIDATION (ENSPY thesis (this project), 2026), § national_validation: “It places 68 % of the. truly worst-quartile districts in its own worst quartile, against 25 % by chance.”
3. EV-NATIONAL-VALIDATION (ENSPY thesis (this project), 2026), § What the `dataset/` folder actually contains: “Comparing absolute values instead would. manufacture a spurious 2× over-prediction that says nothing about the model. ### 2 · There was no climate data for 2024–2025 cameroon_districts_climate.csv”

<details><summary>Reasoning trace</summary>

- Known events up to step 1: E1.2
- New this step: E1.2 (tasking)
- Signals: low_risk_output, nationwide_deployment_request
- Rule 'nationwide_deployment_request' matched -> actions ['LOCAL_CALIBRATION_PERIOD', 'RANK_ONLY_OUTPUT', 'PUBLISH_TRANSPARENCY_NOTE']
- Retrieved 1 chunk(s) for: Leave-One-Region-Out deployment in an unseen region
- Retrieved 2 chunk(s) for: ranks district burden Spearman worst-quartile absolute prediction fails
- Retrieved 0 chunk(s) for: do not deploy to a new region without a local calibration period
- Evidence gate: 3 claim(s) admitted, 0 rejected

</details>

### Ministry of Public Health / PNLP, incl. National IHR Focal Point

Ministry of Public Health / PNLP agent: 1 new event(s); signals nationwide_deployment_request; proposes DEPLOY_NATIONWIDE.

**Proposed actions**
- `DEPLOY_NATIONWIDE` ⚠ human decision: Ministerial instruction, consistent with the strategic plan's national targets. [1], [2], [3]

**Evidence (admitted by the verbatim gate)**
1. CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 71: “D’ici 2028, réduire d’au moins 75%, la morbidité liée au paludisme par rapport à la situation de 2015.”
2. CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 60–61: “Surveillance, SNIS, Suivi et évaluation, Recherche o Système de rapportage des données est parfaitement intégré à celui du Système National d'Information Sanitaire (SNIS) ; o Tenue effective des réunions de revue et de validation des données est effective aux niveaux central et au niveau régional ; o Missions de vérification sur site de la qualité des données (MRDQA) sont régulièrement”
3. CM-PSNSN-2026-2030 (Ministère de la Santé Publique, 2026), p. 58: “Plaidoyer et déploiement des ressources humaines en santé numérique dans les structures sanitaires.”

<details><summary>Reasoning trace</summary>

- Known events up to step 1: E1.1
- New this step: E1.1 (instruction)
- Signals: nationwide_deployment_request
- Rule 'nationwide_deployment_request' matched -> actions ['DEPLOY_NATIONWIDE'], consult ['advisor']
- Retrieved 2 chunk(s) for: réduire la morbidité liée au paludisme d'ici 2028
- Retrieved 2 chunk(s) for: santé numérique système d'information sanitaire déploiement national
- Evidence gate: 3 claim(s) admitted, 0 rejected
- High-impact actions routed to human decision: DEPLOY_NATIONWIDE

</details>

### Personal Data Protection Authority (Law 2024/017)

Data Protection Authority agent: 1 new event(s); signals nationwide_deployment_request; proposes no action.

**Evidence (admitted by the verbatim gate)**
1. CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), art. 45, p. 17: “(3) La personne concernée a également le droit : - d'obtenir une intervention humaine de la part du re able du traitement; -_ d'exprimer son point de vue ; - de contester la décision fondée sur le traiteme omalisé.”
2. CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), art. 44, p. 16–17: “ARTICLE 44.- (1) La personne concernéea le droit de s'opposer à toute décision basée exclusivement sur le traitement automatisé de ses données à caractère | personnel, y compris le profilage.”

<details><summary>Reasoning trace</summary>

- Known events up to step 1: E1.3
- New this step: E1.3 (plan)
- Signals: nationwide_deployment_request
- Rule 'nationwide_deployment_request' matched -> actions -
- Retrieved 2 chunk(s) for: décision produisant des effets juridiques fondée sur un traitement automatisé
- Evidence gate: 2 claim(s) admitted, 0 rejected

</details>

**Consultation**

- **ministry → advisor:** What global guidance applies before a health AI tool is scaled to regions where it was not validated?
  - *advisor:* No provision on this point was found in the documents within my mandate; I flag it as a possible gap.

**Coordination**

- Conflict `DEPLOY_NATIONWIDE` vs `LOCAL_CALIBRATION_PERIOD` (deploy now vs. calibrate first): resolved by human decision: DEPLOY_NATIONWIDE rejected
- Human decision on `DEPLOY_NATIONWIDE`: **reject**; Operational use only where a local calibration period has been completed; ranking-only outputs elsewhere.

## Step 2: A free fine-tuning offer on a foreign cloud

**Released**

| Event | To | Content |
|---|---|---|
| E2.1 | surveillance, dpa | A technology partner offers free fine-tuning on its cloud, hosted outside Cameroon, using health-area level DHIS2 confirmed-case counts 2019-2025 for Extrême-Nord.  |

### PaluAlert surveillance & model operations (PNLP data unit)

Surveillance & Model Operations agent: 1 new event(s); signals foreign_cloud_training; proposes PSEUDONYMISE_AGGREGATE.

**Proposed actions**
- `PSEUDONYMISE_AGGREGATE`: Fine-tuning can run in a sandbox, but the data involved are health data. [1], [2]

**Evidence (admitted by the verbatim gate)**
1. ITU-Y3172-2019 (ITU-T, 2019), p. 24–25: “The following points are to be noted: – The reference point between the ML pipeline subsystem and ML sandbox subsystem allows the ML pipelines to interface with the ML sandbox subsystem for the training and updating of ML models. – Data from the ML underlay networks and/or the simulated ML underlay networks may be used to train the ML models in the ML sandbox subsystem. –”
2. ITU-Y3172-2019 (ITU-T, 2019), p. 21–22: “For training or testing, the ML sandbox can use data generated from simulated ML underlay networks and/or live networks.”

<details><summary>Reasoning trace</summary>

- Known events up to step 2: E1.2, E2.1
- New this step: E2.1 (offer)
- Signals: foreign_cloud_training
- Rule 'foreign_cloud_training' matched -> actions ['PSEUDONYMISE_AGGREGATE'], consult ['dpa']
- Retrieved 2 chunk(s) for: Y.3172 sandbox training testing before deployment
- Evidence gate: 2 claim(s) admitted, 0 rejected

</details>

### Personal Data Protection Authority (Law 2024/017)

Data Protection Authority agent: 1 new event(s); signals foreign_cloud_training; proposes REQUIRE_DPIA, PSEUDONYMISE_AGGREGATE, BLOCK_TRANSFER.

**Proposed actions**
- `REQUIRE_DPIA`: Identifiable health data cannot leave the country without the safeguards the law requires; aggregated, pseudonymised data reduce the risk. [1], [2], [3], [4]
- `PSEUDONYMISE_AGGREGATE`: Identifiable health data cannot leave the country without the safeguards the law requires; aggregated, pseudonymised data reduce the risk. [1], [2], [3], [4]
- `BLOCK_TRANSFER` ⚠ human decision: Identifiable health data cannot leave the country without the safeguards the law requires; aggregated, pseudonymised data reduce the risk. [1], [2], [3], [4]

**Evidence (admitted by the verbatim gate)**
1. CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), art. 32, p. 13: “droifé que Jui@onfère la présente loi à l'égard des responsables du traitement. ARTICLE 32.- (1) Le transfert de don a personnel vers un Etat étranger, ou à une organisation inté OMalé, est subordonné à l'obtention d'une autorisation préalable délivrée Par l'Aÿtorité de protection des données à caractère personnel dans les gonditionS%ermettant de garantir l'exercice des droits de la personne concerné 7 (2)AFr | élivr”
2. CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), art. 6, 8, p. 6: “Transfert international de données : acheminement des do à caractère personnel au-delà des frontières d'un pays vers un autre, qûè ce $@it vers un Etat tiers ou une organisation internationale.”
3. AU-MALABO-2014 (African Union, 2014), art. 14, p. 21: “Principle of transparency ofpersonal data processing The principle of transparency requires mandatory disclosure of information on personal data by the data controller. | Principle 6:”
4. CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), art. 19, 20, 21, p. 8–9: “PUBLIQUE PRÉSIDENCE DE LA RE PTSAC PRES RETAS -TE RECQUENTAIRE SERVICE DOEXTOR AFFAIRS en SEE LEGISLATII co CHAPITRE III DES OBLIGATIONS DU RESPONSABLE DU TRAITEMENT DES DONNEES ET DU SOUS-TRAITANT ARTICLE 20.- Le responsable du traitement et le sous-traitant sont assujettis aux mêmes obligations au titre de l’activité de traitement des données à caractère personnel.”

<details><summary>Reasoning trace</summary>

- Known events up to step 2: E1.3, E2.1
- New this step: E2.1 (offer)
- Signals: foreign_cloud_training
- Rule 'foreign_cloud_training' matched -> actions ['REQUIRE_DPIA', 'PSEUDONYMISE_AGGREGATE', 'BLOCK_TRANSFER']
- Retrieved 2 chunk(s) for: transfert de données à caractère personnel vers un pays tiers niveau de protection
- Retrieved 2 chunk(s) for: données sensibles données de santé interdiction traitement exceptions
- Retrieved 2 chunk(s) for: cross-border transfer of personal data adequate level of protection
- Evidence gate: 4 claim(s) admitted, 0 rejected
- High-impact actions routed to human decision: BLOCK_TRANSFER

</details>

**Consultation**

- **surveillance → dpa:** A partner offers to fine-tune the model on health-area case data hosted on a foreign cloud. Under what conditions may these data be transferred abroad?
  - *dpa:* Current position (step 2): REQUIRE_DPIA, PSEUDONYMISE_AGGREGATE, BLOCK_TRANSFER. Identifiable health data cannot leave the country without the safeguards the law requires; aggregated, pseudonymised data reduce the risk. No provision on this point was found in the documents within my mandate; I flag it as a possible gap.

**Coordination**

- Human decision on `BLOCK_TRANSFER`: **approve**; No health-area data leave the country; district aggregates may be used in the ITU sandbox under a processing agreement.

## Step 3: A signal from across the border

**Released**

| Event | To | Content |
|---|---|---|
| E3.1 | ministry, advisor | Community radio reports a rise in fever cases on the Nigerian side of the Mayo-Tsanaga valley. No laboratory confirmation yet.  |
| E3.2 | surveillance | Rank Extrême-Nord border districts for July; Mokolo and Mozogo fall in the top quartile of the model's ranking.  |

### PaluAlert surveillance & model operations (PNLP data unit)

Surveillance & Model Operations agent: 1 new event(s); signals cross_border_signal; proposes RANK_ONLY_OUTPUT.

**Proposed actions**
- `RANK_ONLY_OUTPUT`: The model can rank border districts but cannot confirm cases. [1], [2]

**Evidence (admitted by the verbatim gate)**
1. EV-NATIONAL-VALIDATION (ENSPY thesis (this project), 2026), § Results: “The model knows. which *region* is worse (ρ = 0.915) better than which district inside it.”
2. EV-RESULTS-SUMMARY (ENSPY thesis (this project), 2026), § 10 · Limitations: “Geography dominance makes it partly a spatial lookup: the model largely. learns *where* a district is and adjusts marginally for climate.”

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E1.2, E2.1, E3.2
- New this step: E3.2 (tasking)
- Signals: cross_border_signal
- Rule 'cross_border_signal' matched -> actions ['RANK_ONLY_OUTPUT']
- Retrieved 2 chunk(s) for: between-region ranking geography dominance
- Evidence gate: 2 claim(s) admitted, 0 rejected

</details>

### Ministry of Public Health / PNLP, incl. National IHR Focal Point

Ministry of Public Health / PNLP agent: 1 new event(s); signals cross_border_signal; proposes FIELD_VERIFICATION, NOTIFY_WHO_IHR, INFORM_NEIGHBOUR_COUNTRY.

**Proposed actions**
- `FIELD_VERIFICATION`: A possible cross-border event must be assessed under the IHR before notifying. [1]
- `NOTIFY_WHO_IHR` ⚠ human decision: A possible cross-border event must be assessed under the IHR before notifying. [1]
- `INFORM_NEIGHBOUR_COUNTRY` ⚠ human decision: A possible cross-border event must be assessed under the IHR before notifying. [1]

**Evidence (admitted by the verbatim gate)**
1. WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 83–84: “In public health, predictive analytics can forecast major health events, including outbreaks, before they occur.”

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E1.1, E3.1
- New this step: E3.1 (rumour)
- Signals: cross_border_signal
- Rule 'cross_border_signal' matched -> actions ['FIELD_VERIFICATION', 'NOTIFY_WHO_IHR', 'INFORM_NEIGHBOUR_COUNTRY'], consult ['advisor']
- Retrieved 2 chunk(s) for: notification events public health emergency of international concern 24 hours
- Retrieved 1 chunk(s) for: collaboration transfrontalière pays voisins paludisme
- Evidence gate: 1 claim(s) admitted, 0 rejected
- High-impact actions routed to human decision: NOTIFY_WHO_IHR, INFORM_NEIGHBOUR_COUNTRY

</details>

### Policy & legal adviser (global best practice)

Policy & legal adviser agent: 1 new event(s); signals cross_border_signal; proposes LOG_POLICY_GAP.

**Proposed actions**
- `LOG_POLICY_GAP`: Log a policy, standards or responsibility gap with global examples 

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E3.1
- New this step: E3.1 (rumour)
- Signals: cross_border_signal
- Rule 'cross_border_signal' matched -> actions ['LOG_POLICY_GAP']
- Retrieved 0 chunk(s) for: International Health Regulations notification assessment of events
- Evidence gate: 0 claim(s) admitted, 0 rejected

</details>

**Consultation**

- **ministry → advisor:** Does a model-predicted, unconfirmed risk increase near a border trigger IHR notification?
  - *advisor:* Current position (step 3): LOG_POLICY_GAP. Log a policy, standards or responsibility gap with global examples Under WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 67: “An algorithm that predicts mortality from training data may have learnt that a patient who visits a chaplain is at increased risk of death (181).”

**Coordination**

- Human decision on `INFORM_NEIGHBOUR_COUNTRY`: **approve**; Share the district ranking and its limits with Nigerian counterparts through the existing cross-border malaria initiative.
- Human decision on `NOTIFY_WHO_IHR`: **defer**; Assess with the IHR decision instrument once cases are confirmed; a model ranking is not a confirmed event.

## Gap register

| Gap | Category | National status | Practice examples | Y.3172 | AI Readiness |
|---|---|---|---|---|---|
| Predicted (not yet confirmed) risk has no defined place in IHR notification practice | Coordination problem | Not found in national corpus (score 0.0933) | 1 | D SINK | D7 Strategy Alignment |
| No standard for validating and monitoring a model before and after deployment | Standards gap | Not found in national corpus (score 0.1375) | 1 | M MLFO SANDBOX | D4 Contextualization and Regional Impact; D5 Level of Integration of AI in Workflows; D10 AI & Policies |
| No requirement to publish the validity limits of models used by public bodies | Standards gap | Not found in national corpus (score 0.0779) | 2 | D | D6 Human Interface; D10 AI & Policies |
| No framework for routine data sharing between health, meteorology and telecom actors | Coordination problem | Weakly addressed (score 0.0798) | 2 | SRC C | D3 Cross-Domain Correlation Analysis; D7 Strategy Alignment |
| No sector rule for AI tools used in public-health decision support | Legislative gap | Weakly addressed (score 0.0653) | 3 | M SANDBOX | D10 AI & Policies |
| Automated decisions and profiling in public-health targeting | Legislative gap | Addressed (score 0.1091) | 3 | P M | D8 Collaboration with AI; D10 AI & Policies |
| Conditions for transferring health data abroad for model training are unclear | Legislative gap | Addressed (score 0.2098) | 2 | C SANDBOX | D1 Data/Model Marketplace; D10 AI & Policies |

### G-IHR-PREDICTED: Predicted (not yet confirmed) risk has no defined place in IHR notification practice

*Coordination problem · Not found in national corpus* · searched 7 national documents · raised by advisor (step 3), ministry (step 3)

- National: CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 108: “La coordination et le suivi de la mise en œuvre des activités seront faits par le point focal ISDC du district, les chefs”
- Practice: WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 83–84: “In public health, predictive analytics can forecast major health events, including outbreaks, before they occur.”
- Not yet in the knowledge base, would strengthen this finding: WHO-IHR-2005
- **Recommendation:** Define how model-predicted cross-border risk is assessed against the IHR decision instrument before any notification or neighbour information.

### G-MODEL-VALIDATION: No standard for validating and monitoring a model before and after deployment

*Standards gap · Not found in national corpus* · searched 7 national documents · raised by surveillance (step 1)

- National: CM-PSNSN-2026-2030 (Ministère de la Santé Publique, 2026), p. 30: “DAJC, DRFP, DEPMINSANTE 15 000 000 15 000 000 Budget de l'État/ Appui des PTF Organisation d'un atelier de validation du modèle de fonctionnement et de projets d'actes de création du Centre National de Télémédecine SG, CI.”
- Practice: ITU-AIREADY-2025 (ITU, 2025), p. 23–24: “deployment. Local innovation involves large amounts of data and research efforts. The contextualization will facilitate the deployment of AI integration. Chapter 3 22 AI Ready – Analysis Towards a Standardized Readiness Framework Dimension Metrics Contextualization & Regional Impact • Number/quality of regionally developed patents/technology compo nents/solutions. o Datasets, models, research, guidelines, toolsets, a”
- Not yet in the knowledge base, would strengthen this finding: WHO-AI-REG-2023
- **Recommendation:** Require external validation, a declared validity envelope, local calibration before new-region use, and post-deployment drift monitoring.

### G-TRANSPARENCY: No requirement to publish the validity limits of models used by public bodies

*Standards gap · Not found in national corpus* · searched 7 national documents · raised by surveillance (step 1)

- National: CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 6–7: “Circuit de l’information du niveau opérationnel au niveau central 106 v LISTE DES TABLEAUX Tableau 1 :”
- Practice: WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 42: “Two broad approaches to ensuring intelligibility are improving the transparency and explainability of AI technology.”
- Practice: EU-AI-ACT-SUMMARY (European Union, 2024): “GENERAL PURPOSE AI (GPAI) MODELS - All GPAI providers must provide technical documentation, comply with copyright law, publish training data summaries - Systemic risk GPAI (>10^25 FLOPs training compute): additional obligations including model evaluations, adversarial testing, incident reporting, cybersecurity measures 4.”
- **Recommendation:** Require a public transparency note for any model used in public-health decisions, including where it was shown not to work.

### G-DATA-SHARING: No framework for routine data sharing between health, meteorology and telecom actors

*Coordination problem · Weakly addressed* · searched 7 national documents · raised by advisor (step 1), dpa (step 2)

- National: CM-PSNLP-2019-2023 (Ministère de la Santé Publique / PNLP, 2019), p. 29: “Suivant les dispositions du Décret N° 2013/093 du 04 avril 2013 portant organisation du Ministère de la santé Publique, la Cellule des Informations Sanitaires est chargée entre autres de la conception et du suivi de la mise en œuvre du Système d’Informations Sanitaires et de l’élaboration des indicateurs sanitaires nationaux.”
- Practice: AU-AI-STRATEGY-2024 (African Union, 2024), p. 31–32: “Accelerate the integration of AI in the core sectors outlined in the Digital Transformation Strategy, notably sectors with high social and economic value, including agriculture, education, health, climate change and natural resource management, and regional peace and security. iv.”
- Practice: WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 104: “In 2014, the US National Institutes of Health introduced their Genomic Data Sharing Policy, which is intended to encourage “broad and responsible sharing of genomic research data” (283).”
- Not yet in the knowledge base, would strengthen this finding: CM-PSNSN-2020-2024
- **Recommendation:** Adopt data-sharing agreements between health, meteorology and network operators, with a common schema for climate-health data.

### G-AI-HEALTH-REGULATION: No sector rule for AI tools used in public-health decision support

*Legislative gap · Weakly addressed* · searched 7 national documents · raised by ministry (step 1)

- National: CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 55: “Une étude a été conduite sur la modélisation et l’expansion des ASCP au Cameroun et a permis élaboration d’un outil d’aide à la décision pour augmenter le nombre d’ASCp en vue du passage à l’échelle des Interventions Sous Directives Communautaires.”
- Practice: WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 37–38: “LAWS, POLICIES AND PRINCIPLES THAT APPLY TO ARTIFICIAL INTELLIGENCE FOR HEALTH 4.7 Regulatory considerations Regulation of AI technologies is likely to be developed and implemented by health regulatory authorities responsible for ensuring the safety, efficacy and appropriate use of technologies for health care and therapeutic development.”
- Practice: UN-GOVERNING-AI-2024 (UN High-level Advisory Body on AI, 2024), p. 8–9: “3 Excluding the United Nations Educational, Scientific and Cultural Organization (UNESCO) Recommendation on the Ethics of Artificial Intelligence (2021) and the two General Assembly resolutions on AI in 2024: “Seizing the opportunities of safe, secure and trustworthy artificial intelligence systems for sustainable development” (78/265) and “Enhancing international cooperation on capacity-building of artificial”
- Practice: EU-AI-ACT-SUMMARY (European Union, 2024): “RISK-BASED CLASSIFICATION The Act classifies AI systems into four risk tiers: a) Unacceptable Risk (Prohibited):”
- Not yet in the knowledge base, would strengthen this finding: WHO-AI-REG-2023, AE-DOH-AI-POLICY-2018
- **Recommendation:** Adopt a risk-tiered rule for AI decision-support in health, with pre-deployment evaluation proportionate to impact.

### G-AUTOMATED-DECISION: Automated decisions and profiling in public-health targeting

*Legislative gap · Addressed* · searched 7 national documents · raised by dpa (step 1)

- National: CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), art. 44, p. 16–17: “ARTICLE 44.- (1) La personne concernéea le droit de s'opposer à toute décision basée exclusivement sur le traitement automatisé de ses données à caractère | personnel, y compris le profilage.”
- Practice: AU-MALABO-2014 (African Union, 2014), p. 22: “A person shall not be subject to a decision which produces legal effects concerning him/her or significantly affects him/her to a substantial degree, and which is based solely on automated processing of data intended to evaluate certain personal aspects relating to him/her.”
- Practice: WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 34–35: “Data protection laws also increasingly recognize that people have the right not to be subject to decisions guided solely by automated processes.”
- Practice: UN-GOVERNING-AI-2024 (UN High-level Advisory Body on AI, 2024), p. 33: “34 Increasing reliance on automated decision-making and content-creation by opaque algorithms can undermine fair treatment and safety.”
- **Recommendation:** Clarify whether district-level targeting driven by a model is an automated decision, and what human review and explanation it requires.

### G-HEALTH-DATA-TRANSFER: Conditions for transferring health data abroad for model training are unclear

*Legislative gap · Addressed* · searched 7 national documents · raised by dpa (step 2), surveillance (step 2)

- National: CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), art. 32, p. 13: “droifé que Jui@onfère la présente loi à l'égard des responsables du traitement. ARTICLE 32.- (1) Le transfert de don a personnel vers un Etat étranger, ou à une organisation inté OMalé, est subordonné à l'obtention d'une autorisation préalable délivrée Par l'Aÿtorité de protection des données à caractère personnel dans les gonditionS%ermettant de garantir l'exercice des droits de la personne concerné 7 (2)AFr | élivr”
- Practice: AU-MALABO-2014 (African Union, 2014), art. 10, 15, p. 22–23: “6. a) The data controller shall not transfer personal data to a non-Member State of the African Union unless such a State ensures an adequate EeSE TE EES EE REDS SEE ES OE AN ES LE STE TE BEE ETS E ES PISSEE ee | 22 level of protection of the privacy, freedoms and fundamental rights of persons whose data are being or are likely to be processed.”
- Practice: WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 56–57: “Although confidentiality is a well-recognized pillar of medical practice, the duty of confidentiality may not be sufficient to cover the many types of data now used to guide AI health technologies and may also not be sufficient to control the production and transfer of health data (113).”
- Not yet in the knowledge base, would strengthen this finding: AE-PDPL-2021
- **Recommendation:** Publish implementing rules for cross-border transfers of health data used to train models, including pseudonymisation and processor obligations.

## Expected vs actual

- Expected actions found: ['BLOCK_TRANSFER', 'DEPLOY_NATIONWIDE', 'FIELD_VERIFICATION', 'INFORM_NEIGHBOUR_COUNTRY', 'LOCAL_CALIBRATION_PERIOD', 'NOTIFY_WHO_IHR', 'PSEUDONYMISE_AGGREGATE', 'PUBLISH_TRANSPARENCY_NOTE', 'RANK_ONLY_OUTPUT', 'REQUIRE_DPIA'] (recall 1.0)
- Expected actions missed: []
- Expected gaps found: ['G-AI-HEALTH-REGULATION', 'G-AUTOMATED-DECISION', 'G-HEALTH-DATA-TRANSFER', 'G-IHR-PREDICTED', 'G-MODEL-VALIDATION', 'G-TRANSPARENCY'] (recall 1.0)
- Expected gaps missed: []
- Conflicts detected: 1 · human decisions: 4 · claims admitted/rejected: 17/0
