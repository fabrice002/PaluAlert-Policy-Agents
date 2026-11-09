# S1 · A badly sited IoT sensor quietly lowers the malaria forecast

Run `S1_sensor_siting_20261109T082315Z` · model backend `extractive` · PaluAlert `in-process`

Built from a real finding of the thesis (sensor_validation): the first deployed LoRa/Meshtastic node in Yaoundé reads +7.27 °C and -30.6 RH points against the ERA5 reanalysis the models were trained on, at an identical dew point. The element is sound; the siting is not. Fed raw, the sensor lowers the forecast. Nobody has the full picture: the surveillance unit sees the data, the telecom regulator sees the network, the ministry sees the field, and a regional delegation acts on the dashboard.

## Step 1: First IoT capture disagrees with the reanalysis

**Released**

| Event | To | Content |
|---|---|---|
| E1.1 | surveillance | Node !a0cb4a5c (Biyem Assi health district, Yaoundé) reports for April 2026: temperature 30.73 °C, relative humidity 56.8 %, pressure 927.90 hPa. ERA5 for the same hours: 23.46 °C, 87.4 %, 923.63 hPa.  |
| E1.2 | telecom | Gateway logs: node !a0cb4a5c changed position on 28 March and now relays through a new rooftop repeater; 12 % packet loss on the 868 MHz link.  |
| E1.3 | ministry | Biyem Assi district health team: RDT positivity this April is similar to last April; ACT stocks are adequate.  |

### PaluAlert surveillance & model operations (PNLP data unit)

Surveillance & Model Operations agent: 1 new event(s); signals low_risk_output, prediction_sensitive_to_sensor, sensor_bias; proposes QUARANTINE_SENSOR_FEED, APPLY_SENSOR_CORRECTION, FLAG_PREDICTIONS_UNRELIABLE, CERTIFY_SENSOR_SITING.

Tool `compare_inputs` on Biyem Assi 2026-04 (in-process):

| Input | T °C | RH % | Cases | /1000 | Risk | vs ref |
|---|---|---|---|---|---|---|
| reanalysis | 23.46 | 87.4 | 3835 | 9.35 | Low | +0.0% |
| sensor_raw | 30.73 | 56.8 | 3509 | 8.55 | Low | -8.5% |
| sensor_corrected | 23.46 | 87.0 | 3837 | 9.35 | Low | +0.1% |

**Proposed actions**
- `QUARANTINE_SENSOR_FEED`: The node disagrees with the reanalysis the models were trained on; the validation study traced this to a siting offset that changes the forecast. [1], [2], [3], [4]
- `APPLY_SENSOR_CORRECTION`: The node disagrees with the reanalysis the models were trained on; the validation study traced this to a siting offset that changes the forecast. [1], [2], [3], [4]
- `FLAG_PREDICTIONS_UNRELIABLE`: The node disagrees with the reanalysis the models were trained on; the validation study traced this to a siting offset that changes the forecast. [1], [2], [3], [4]
- `CERTIFY_SENSOR_SITING`: The node disagrees with the reanalysis the models were trained on; the validation study traced this to a siting offset that changes the forecast. [1], [2], [3], [4]

**Evidence (admitted by the verbatim gate)**
1. EV-SENSOR-VALIDATION (ENSPY thesis (this project), 2026), § sensor_validation: “Meshtastic node !a0cb4a5c. ## Running it Needs network: it fetches the matching reanalysis hours from Open-Meteo. ## Main result The sensor is sound, but it is sited badly, and that one fault costs 38 % of. the forecast.”
2. EV-SENSOR-VALIDATION (ENSPY thesis (this project), 2026), § Main result: “Subtracting the offset and recomputing humidity at the sensor's own dew point. brings it back to within 1.3 % of the reanalysis.”
3. EV-IOT-ACQUISITION (ENSPY thesis (this project), 2026), § Two projects, one chain: “See the next section. ## The provenance rule The models in ../palualert_app/deployment_bundle/ were trained and validated exclusively on historical.”
4. EV-IOT-ACQUISITION (ENSPY thesis (this project), 2026), § The provenance rule: “The one place IoT data is used is sensor_validation/,. and there it answers a *hardware* question: does the deployed sensor agree with. the reanalysis the models were trained on?, not a modelling one.”
5. EV-SENSOR-VALIDATION (ENSPY thesis (this project), 2026), § sensor_validation: “Relative humidity predicted from. a +7.27 degC offset at unchanged moisture is 57.0 %; the sensor reads.”

<details><summary>Reasoning trace</summary>

- Known events up to step 1: E1.1
- New this step: E1.1 (iot_reading)
- Signals: low_risk_output, prediction_sensitive_to_sensor, sensor_bias
- Rule 'sensor_bias' matched -> actions ['QUARANTINE_SENSOR_FEED', 'APPLY_SENSOR_CORRECTION', 'FLAG_PREDICTIONS_UNRELIABLE', 'CERTIFY_SENSOR_SITING'], consult ['telecom']
- Rule 'prediction_sensitive_to_sensor' matched -> actions ['FLAG_PREDICTIONS_UNRELIABLE']
- Retrieved 2 chunk(s) for: sensor sited badly temperature offset dew point costs forecast
- Retrieved 2 chunk(s) for: provenance rule models trained exclusively on reanalysis no IoT measurement
- Retrieved 2 chunk(s) for: offset-corrected sensor reanalysis no retraining
- Evidence gate: 5 claim(s) admitted, 0 rejected

</details>

### Ministry of Public Health / PNLP, incl. National IHR Focal Point

Ministry of Public Health / PNLP agent: 1 new event(s); signals none; proposes no action.

<details><summary>Reasoning trace</summary>

- Known events up to step 1: E1.3
- New this step: E1.3 (field_report)
- Signals: none
- Evidence gate: 0 claim(s) admitted, 0 rejected

</details>

### Telecommunications Regulatory Board (ART) and ANTIC

Telecom regulator & cybersecurity agent: 1 new event(s); signals new_radio_node; proposes SPECTRUM_COMPLIANCE_CHECK, SECURE_IOT_CHANNEL.

**Proposed actions**
- `SPECTRUM_COMPLIANCE_CHECK`: New nodes join a network that carries public-health data. [1], [2], [3], [4]
- `SECURE_IOT_CHANNEL`: New nodes join a network that carries public-health data. [1], [2], [3], [4]

**Evidence (admitted by the verbatim gate)**
1. CM-LAW-2010-012 (Présidence de la République du Cameroun, 2010), p. 7–8: “8 - monitor technological developments and issue warnings and recommendations regarding the security of electronic communication networks and certification ; - participate in research, training and studies related to the security of electronic communication networks, certification and information systems; - ensure the regularity and efficiency of security”
2. CM-LAW-2010-012 (Présidence de la République du Cameroun, 2010), art. 7, p. 7: “(2) The Agency referred to in subsection 1 above shall be responsible for the regulation , control and monitoring of activities related to the security of electronic communication networks, information systems, and electronic certification on behalf of the State.”
3. EV-IOT-HARDWARE (ENSPY thesis (this project), 2026), § Sensor node: Heltec V3: “It gathers. telemetry from the mesh over LoRa and republishes it to the MQTT broker over.”
4. EV-IOT-HARDWARE (ENSPY thesis (this project), 2026), § Why these values, briefly: “Each step up in SF roughly doubles time on air and therefore. halves the number of nodes a channel supports.”

<details><summary>Reasoning trace</summary>

- Known events up to step 1: E1.2
- New this step: E1.2 (network_operations)
- Signals: new_radio_node
- Rule 'new_radio_node' matched -> actions ['SPECTRUM_COMPLIANCE_CHECK', 'SECURE_IOT_CHANNEL']
- Retrieved 2 chunk(s) for: security of electronic communication networks and information systems audit
- Retrieved 2 chunk(s) for: MQTT broker gateway encryption channel
- Evidence gate: 4 claim(s) admitted, 0 rejected

</details>

**Consultation**

- **surveillance → telecom:** Was the LoRa node relocated or reconfigured, and is it operating within its authorised radio parameters?
  - *telecom:* Current position (step 1): SPECTRUM_COMPLIANCE_CHECK, SECURE_IOT_CHANNEL. New nodes join a network that carries public-health data. Under EV-IOT-HARDWARE (ENSPY thesis (this project), 2026), § Rainfall travels in the `iaq` field: “In the April 2026 capture the iaq column is empty on all 3 139 rows, so. the rain channel was not reporting during that deployment window regardless. ## 4 · Radio parameters Every node in a Meshtastic network must share identical radio parameters: frequency, spreading factor, coding rate, bandwidth: or they cannot hear each. other at all.”

**Coordination**

- `CERTIFY_SENSOR_SITING`: no institution is mandated (proposed by surveillance)

## Step 2: The dashboard says "Low" and a region wants to scale down

**Released**

| Event | To | Content |
|---|---|---|
| E2.1 | ministry | The Centre regional delegation proposes to postpone the indoor residual spraying round in Biyem Assi because the PaluAlert dashboard has shown "Low" for three weeks.  |
| E2.2 | surveillance | Drift monitor: PSI above 9 on Temperature_C and Humidity_pct for the IoT-fed district against the training reference (major drift).  |

### PaluAlert surveillance & model operations (PNLP data unit)

Surveillance & Model Operations agent: 1 new event(s); signals drift_major; proposes FLAG_PREDICTIONS_UNRELIABLE.

**Proposed actions**
- `FLAG_PREDICTIONS_UNRELIABLE`: Input distribution has shifted beyond the PSI threshold. [1], [2]

**Evidence (admitted by the verbatim gate)**
1. EV-MLOPS-PLATFORM (ENSPY thesis (this project), 2026), § The actual data flow: “Drift Detection, PSI + Kolmogorov-Smirnov (data), Mann-Whitney (performance), ✅.”
2. EV-INCREMENTAL (ENSPY thesis (this project), 2026), § The four lessons: “Improving the regression. does not improve risk detection: which is nonetheless the whole point of an. early-warning system. ## Drift detection on the spliced series A second part, with no claim to performance: the A+B series is knowingly. distorted, and what is checked is that the detector in. palualert_app/app/mlops/monitoring/drift.py spots it.”

<details><summary>Reasoning trace</summary>

- Known events up to step 2: E1.1, E2.2
- New this step: E2.2 (monitoring_alert)
- Signals: drift_major
- Rule 'drift_major' matched -> actions ['FLAG_PREDICTIONS_UNRELIABLE']
- Retrieved 2 chunk(s) for: drift detection PSI Kolmogorov-Smirnov monitoring
- Evidence gate: 2 claim(s) admitted, 0 rejected

</details>

### Ministry of Public Health / PNLP, incl. National IHR Focal Point

Ministry of Public Health / PNLP agent: 1 new event(s); signals campaign_downscale_request, low_risk_output; proposes HOLD_ALERT_PENDING_VERIFICATION, FIELD_VERIFICATION, MAINTAIN_VECTOR_CONTROL.

**Proposed actions**
- `HOLD_ALERT_PENDING_VERIFICATION`: Planned vector control follows the national strategic plan; a single model output is not a basis to scale it down without field confirmation. [1], [2], [3], [4]
- `FIELD_VERIFICATION`: Planned vector control follows the national strategic plan; a single model output is not a basis to scale it down without field confirmation. [1], [2], [3], [4]
- `MAINTAIN_VECTOR_CONTROL` ⚠ human decision: Planned vector control follows the national strategic plan; a single model output is not a basis to scale it down without field confirmation. [1], [2], [3], [4]

**Evidence (admitted by the verbatim gate)**
1. CM-PSNLP-2019-2023 (Ministère de la Santé Publique / PNLP, 2019), p. 61–62: “D'ici 2023, Au moins 80% de la population à risque des districts de santé ciblés est protégée par la Pulvérisation Intra- Domiciliaire (PID) Stratégie 3.5.1:”
2. CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 50: “Entre 2019 et 2022, deux campagnes de distribution des Moustiquaires Imprégnées d’insecticides à Longue Durée d’Action (MILDA) ont été organisées.”
3. CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 84: “Surveillance épidémiologique du paludisme La surveillance épidémiologique du paludisme sera mise en œuvre à travers les interventions de surveillance épidémiologique en routine, surveillance sentinelle, préparation à la riposte aux épidémies, surveillance entomologique et gestion de la résistance aux insecticides.”
4. CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 137–138: “Mécanisme de coordination du M&E 6.3.1 Composante « Surveillance épidémiologique » (SNIS/SIMR) Sous le leadership de la DLMEP, le Ministère de la Santé Publique organise une collecte hebdomadaire des données de morbidité et de mortalité relatives aux maladies à potentiel épidémique, y compris le paludisme.”
5. CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 55–56: “La mise en œuvre régulière de la vérification sur site (FOSA) de la qualité des données, complémentaire à la tenue régulière des réunions de revue et de validation trimestrielle des données au niveau régional a amélioré la qualité des données rapportées en routine.”

<details><summary>Reasoning trace</summary>

- Known events up to step 2: E1.3, E2.1
- New this step: E2.1 (operational_request)
- Signals: campaign_downscale_request, low_risk_output
- Rule 'campaign_downscale_request' matched -> actions ['HOLD_ALERT_PENDING_VERIFICATION', 'FIELD_VERIFICATION', 'MAINTAIN_VECTOR_CONTROL'], consult ['surveillance']
- Rule 'low_risk_output' matched -> actions ['FIELD_VERIFICATION']
- Retrieved 2 chunk(s) for: pulvérisation intradomiciliaire moustiquaires imprégnées campagne planification district
- Retrieved 2 chunk(s) for: surveillance épidémiologique riposte seuil épidémique district de santé
- Retrieved 2 chunk(s) for: complétude promptitude des rapports DHIS2 qualité des données
- Evidence gate: 5 claim(s) admitted, 0 rejected
- High-impact actions routed to human decision: MAINTAIN_VECTOR_CONTROL

</details>

**Consultation**

- **ministry → surveillance:** Is the Low-risk output shown for this district reliable enough to change a planned vector-control campaign?
  - *surveillance:* Current position (step 2): FLAG_PREDICTIONS_UNRELIABLE. Input distribution has shifted beyond the PSI threshold. No provision on this point was found in the documents within my mandate; I flag it as a possible gap.

**Coordination**

- Human decision on `MAINTAIN_VECTOR_CONTROL`: **approve**; Keep the spraying round as planned; the Low output comes from a feed under investigation.

## Step 3: Root cause found, and a fix that creates a new problem

**Released**

| Event | To | Content |
|---|---|---|
| E3.1 | surveillance, ministry, dpa, telecom, advisor | Field visit: the node is mounted on a sun-exposed metal roof. The vendor proposes to move it to a host household's yard and to store raw readings together with the household's GPS position and phone number for maintenance visits.  |

### PaluAlert surveillance & model operations (PNLP data unit)

Surveillance & Model Operations agent: 1 new event(s); signals new_radio_node, sensor_relocation_household; proposes no action.

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E1.1, E2.2, E3.1
- New this step: E3.1 (field_finding)
- Signals: new_radio_node, sensor_relocation_household
- Evidence gate: 0 claim(s) admitted, 0 rejected

</details>

### Ministry of Public Health / PNLP, incl. National IHR Focal Point

Ministry of Public Health / PNLP agent: 1 new event(s); signals new_radio_node, sensor_relocation_household; proposes no action.

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E1.3, E2.1, E3.1
- New this step: E3.1 (field_finding)
- Signals: new_radio_node, sensor_relocation_household
- Evidence gate: 0 claim(s) admitted, 0 rejected

</details>

### Personal Data Protection Authority (Law 2024/017)

Data Protection Authority agent: 1 new event(s); signals new_radio_node, sensor_relocation_household; proposes MINIMISE_LOCATION_DATA, REQUIRE_DPIA.

**Proposed actions**
- `MINIMISE_LOCATION_DATA`: Storing the GPS position of the household hosting a node is personal data that the forecast does not need. [1], [2], [3]
- `REQUIRE_DPIA`: Storing the GPS position of the household hosting a node is personal data that the forecast does not need. [1], [2], [3]

**Evidence (admitted by the verbatim gate)**
1. CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), p. 4: “Destinataire : toute personne physique ou morale, habilitée à recevoir une communication des données à caractère personnel.”
2. CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), art. 10, 11, 12, p. 7: “(2) La période de conservation des données à caractère personnel visée à l'alinéa”
3. CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), p. 4: “Interconnexion des fichiers : mécanisme de connexion consistant en la mise en relation de données à caractère personnel traitées pour une finalité déterminée avec d’autres données traitées, pour des finalités identiques ou non, ou liées par un ou plusieurs responsables de traitement. nes10Hi DE TUE Reetre ETARIAT GEN NTAIRE KOICE DU FICHIER LEGISLATIF E”

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E3.1
- New this step: E3.1 (field_finding)
- Signals: new_radio_node, sensor_relocation_household
- Rule 'sensor_relocation_household' matched -> actions ['MINIMISE_LOCATION_DATA', 'REQUIRE_DPIA']
- Retrieved 2 chunk(s) for: données à caractère personnel localisation personne physique identifiable
- Retrieved 1 chunk(s) for: minimisation finalité déterminée explicite et légitime
- Evidence gate: 3 claim(s) admitted, 0 rejected

</details>

### Telecommunications Regulatory Board (ART) and ANTIC

Telecom regulator & cybersecurity agent: 1 new event(s); signals new_radio_node, sensor_relocation_household; proposes SPECTRUM_COMPLIANCE_CHECK, SECURE_IOT_CHANNEL.

**Proposed actions**
- `SPECTRUM_COMPLIANCE_CHECK`: New nodes join a network that carries public-health data. [1], [2], [3], [4]
- `SECURE_IOT_CHANNEL`: New nodes join a network that carries public-health data. [1], [2], [3], [4]

**Evidence (admitted by the verbatim gate)**
1. CM-LAW-2010-012 (Présidence de la République du Cameroun, 2010), p. 7–8: “8 - monitor technological developments and issue warnings and recommendations regarding the security of electronic communication networks and certification ; - participate in research, training and studies related to the security of electronic communication networks, certification and information systems; - ensure the regularity and efficiency of security”
2. CM-LAW-2010-012 (Présidence de la République du Cameroun, 2010), art. 7, p. 7: “(2) The Agency referred to in subsection 1 above shall be responsible for the regulation , control and monitoring of activities related to the security of electronic communication networks, information systems, and electronic certification on behalf of the State.”
3. EV-IOT-HARDWARE (ENSPY thesis (this project), 2026), § Sensor node: Heltec V3: “It gathers. telemetry from the mesh over LoRa and republishes it to the MQTT broker over.”
4. EV-IOT-HARDWARE (ENSPY thesis (this project), 2026), § Why these values, briefly: “Each step up in SF roughly doubles time on air and therefore. halves the number of nodes a channel supports.”
5. CM-COE-OCTOPUS-2021 (Council of Europe, 2021), art. 20, 25, p. 19: “(2) Network operators and electronic communication service providers shall set up mechanisms for monitoring the traffic data of their networks.”

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E1.2, E3.1
- New this step: E3.1 (field_finding)
- Signals: new_radio_node, sensor_relocation_household
- Rule 'new_radio_node' matched -> actions ['SPECTRUM_COMPLIANCE_CHECK', 'SECURE_IOT_CHANNEL']
- Rule 'sensor_relocation_household' matched -> actions ['SECURE_IOT_CHANNEL']
- Retrieved 2 chunk(s) for: security of electronic communication networks and information systems audit
- Retrieved 2 chunk(s) for: MQTT broker gateway encryption channel
- Retrieved 2 chunk(s) for: electronic communication operators shall preserve traffic data
- Evidence gate: 5 claim(s) admitted, 0 rejected

</details>

### Policy & legal adviser (global best practice)

Policy & legal adviser agent: 1 new event(s); signals new_radio_node, sensor_relocation_household; proposes LOG_POLICY_GAP.

**Proposed actions**
- `LOG_POLICY_GAP`: Log a policy, standards or responsibility gap with global examples [1]

**Evidence (admitted by the verbatim gate)**
1. ITU-AIREADY-2025 (ITU, 2025), p. 34–35: “This dimension measures the availability of digital infrastructure, including devices, computing capability, connectivity, and energy.”

<details><summary>Reasoning trace</summary>

- Known events up to step 3: E3.1
- New this step: E3.1 (field_finding)
- Signals: new_radio_node, sensor_relocation_household
- Rule 'new_radio_node' matched -> actions ['LOG_POLICY_GAP']
- Retrieved 2 chunk(s) for: digital infrastructure connectivity energy for AI
- Evidence gate: 1 claim(s) admitted, 0 rejected

</details>

**Coordination**

- nothing to coordinate

## Gap register

| Gap | Category | National status | Practice examples | Y.3172 | AI Readiness |
|---|---|---|---|---|---|
| No designated authority to act on model-generated (predicted) epidemic alerts | Unclear responsibility | Not found in national corpus (score 0.0526) | 1 | P D SINK | D7 Strategy Alignment; D10 AI & Policies |
| No standard for validating and monitoring a model before and after deployment | Standards gap | Not found in national corpus (score 0.1375) | 1 | M MLFO SANDBOX | D4 Contextualization and Regional Impact; D5 Level of Integration of AI in Workflows; D10 AI & Policies |
| No standard for siting and calibrating environmental sensors used for health decisions | Standards gap | Not found in national corpus (score 0.0439) | 0 | SRC PP | D13 Digital Infrastructure |
| Security baseline for low-cost IoT health-surveillance networks | Technology / infrastructure gap | Not found in national corpus (score 0.0946) | 0 | SRC C | D13 Digital Infrastructure |
| No framework for routine data sharing between health, meteorology and telecom actors | Coordination problem | Weakly addressed (score 0.0798) | 2 | SRC C | D3 Cross-Domain Correlation Analysis; D7 Strategy Alignment |

### G-ALERT-AUTHORITY: No designated authority to act on model-generated (predicted) epidemic alerts

*Unclear responsibility · Not found in national corpus* · searched 7 national documents · raised by ministry (step 2)

- National: CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 106: “L’équipe cadre assure la responsabilité d’offrir les services de soins de base selon les dispositions du document de stratégie de Renforcement du Système de Santé (SRSS).”
- Practice: WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 44–45: “KEY ETHICAL PRINCIPLES FOR USE OF ARTIFICIAL INTELLIGENCE FOR HEALTH ETHICS AND GOVERNANCE OF ARTIFICIAL INTELLIGENCE FOR HEALTH 29 5.5 Ensure inclusiveness and equity Inclusiveness requires that AI used in health care is designed to encourage the widest possible appropriate,”
- Not yet in the knowledge base, would strengthen this finding: WHO-MALARIA-SURV-2018, AE-DOH-AI-POLICY-2018
- **Recommendation:** Designate in regulation which body may act on a model-generated alert, at which confidence, and how the decision and its evidence are recorded.

### G-MODEL-VALIDATION: No standard for validating and monitoring a model before and after deployment

*Standards gap · Not found in national corpus* · searched 7 national documents · raised by surveillance (step 2)

- National: CM-PSNSN-2026-2030 (Ministère de la Santé Publique, 2026), p. 30: “DAJC, DRFP, DEPMINSANTE 15 000 000 15 000 000 Budget de l'État/ Appui des PTF Organisation d'un atelier de validation du modèle de fonctionnement et de projets d'actes de création du Centre National de Télémédecine SG, CI.”
- Practice: ITU-AIREADY-2025 (ITU, 2025), p. 23–24: “deployment. Local innovation involves large amounts of data and research efforts. The contextualization will facilitate the deployment of AI integration. Chapter 3 22 AI Ready – Analysis Towards a Standardized Readiness Framework Dimension Metrics Contextualization & Regional Impact • Number/quality of regionally developed patents/technology compo nents/solutions. o Datasets, models, research, guidelines, toolsets, a”
- Not yet in the knowledge base, would strengthen this finding: WHO-AI-REG-2023
- **Recommendation:** Require external validation, a declared validity envelope, local calibration before new-region use, and post-deployment drift monitoring.

### G-SENSOR-STANDARD: No standard for siting and calibrating environmental sensors used for health decisions

*Standards gap · Not found in national corpus* · searched 7 national documents · raised by coordinator (step 1), surveillance (step 1)

- National: CM-PSNLP-2024-2028 (Ministère de la Santé Publique / PNLP, 2024), p. 27: “La norme nationale de couverture est d’un hôpital pour 150 000 habitants. o Formation Sanitaire de catégorie 3 :”
- **Recommendation:** Reference a siting/calibration standard (e.g. national meteorological service practice) for any sensor feeding a health model, and certify nodes before use.

### G-IOT-SECURITY: Security baseline for low-cost IoT health-surveillance networks

*Technology / infrastructure gap · Not found in national corpus* · searched 7 national documents · raised by advisor (step 3), telecom (step 1), telecom (step 3)

- National: CM-PSNSN-2026-2030 (Ministère de la Santé Publique, 2026), p. 41: “ANTIC 750 000 000 750 000 000 750 000 000 750 000 000 750 000 000 3 750 000 000 Budget de l'État/ Appui des PTF Acquisition des équipements numériques de santé prioritaires (objets connectés de santé) CI, DEPMINSANTE;”
- **Recommendation:** Set a minimum security baseline (authentication, encryption, key management) for IoT nodes feeding public-health systems.

### G-DATA-SHARING: No framework for routine data sharing between health, meteorology and telecom actors

*Coordination problem · Weakly addressed* · searched 7 national documents · raised by dpa (step 3), surveillance (step 2)

- National: CM-PSNLP-2019-2023 (Ministère de la Santé Publique / PNLP, 2019), p. 29: “Suivant les dispositions du Décret N° 2013/093 du 04 avril 2013 portant organisation du Ministère de la santé Publique, la Cellule des Informations Sanitaires est chargée entre autres de la conception et du suivi de la mise en œuvre du Système d’Informations Sanitaires et de l’élaboration des indicateurs sanitaires nationaux.”
- Practice: AU-AI-STRATEGY-2024 (African Union, 2024), p. 31–32: “Accelerate the integration of AI in the core sectors outlined in the Digital Transformation Strategy, notably sectors with high social and economic value, including agriculture, education, health, climate change and natural resource management, and regional peace and security. iv.”
- Practice: WHO-AI-ETHICS-2021 (World Health Organization, 2021), p. 104: “In 2014, the US National Institutes of Health introduced their Genomic Data Sharing Policy, which is intended to encourage “broad and responsible sharing of genomic research data” (283).”
- Not yet in the knowledge base, would strengthen this finding: CM-PSNSN-2020-2024
- **Recommendation:** Adopt data-sharing agreements between health, meteorology and network operators, with a common schema for climate-health data.

## Expected vs actual

- Expected actions found: ['APPLY_SENSOR_CORRECTION', 'FIELD_VERIFICATION', 'FLAG_PREDICTIONS_UNRELIABLE', 'HOLD_ALERT_PENDING_VERIFICATION', 'MAINTAIN_VECTOR_CONTROL', 'MINIMISE_LOCATION_DATA', 'QUARANTINE_SENSOR_FEED', 'REQUIRE_DPIA', 'SECURE_IOT_CHANNEL', 'SPECTRUM_COMPLIANCE_CHECK'] (recall 1.0)
- Expected actions missed: []
- Expected gaps found: ['G-ALERT-AUTHORITY', 'G-IOT-SECURITY', 'G-MODEL-VALIDATION', 'G-SENSOR-STANDARD'] (recall 1.0)
- Expected gaps missed: []
- Conflicts detected: 0 · human decisions: 1 · claims admitted/rejected: 25/0
