# Mapping to ITU-T Y.3172 and the ITU AI Readiness Framework 2.0

## 1 · The ML pipeline, node by node

ITU-T Y.3172 describes an ML pipeline of logical nodes, from SRC (source) to
SINK, managed by an ML Function Orchestrator (MLFO) and tested in an ML
sandbox. Every node of the early-warning system already exists in code. The
agent layer adds a governance view of each one.

| Y.3172 node | Malaria early-warning system (palualert_app) | Requirement at this node | Agent that guards it | Documents in the knowledge base |
|---|---|---|---|---|
| **SRC** | LoRa/Meshtastic sensor nodes (`iot_acquisition`), ERA5 / NASA POWER reanalysis, PNLP DHIS2 case reports | sensor sited and calibrated; radio within authorised parameters; case indicator definition versioned | surveillance, telecom | EV-SENSOR-VALIDATION, EV-IOT-HARDWARE, CM-LAW-2010-012, CM-PSNLP-2024-2028 |
| **C** | MQTT broker + `mqtt_logger.py`; `app/mlops/sources/` (open_meteo, nasa_power, csv) | authenticated, encrypted channel; no household-level personal data collected | telecom, dpa | CM-LAW-2010-012, CM-LAW-2024-017, AU-MALABO-2014 |
| **PP** | `stages/validation.py` (16 blocking checks), `stages/features.py` (one shared feature implementation) | reject aberrant inputs; apply documented corrections (siting offset at constant dew point) | surveillance | EV-MLOPS-PLATFORM, EV-SENSOR-VALIDATION |
| **M** | XGBoost NO-LAG to LAG recursive chain (`services/inference.py`) | external validation; a declared validity envelope; local calibration before use in a new region | surveillance, advisor | EV-RESULTS-SUMMARY, EV-NATIONAL-VALIDATION, WHO-AI-ETHICS-2021 |
| **P** | risk threshold: regional 75th percentile; SHAP explanation | outputs outside the envelope are flagged; ranking-only output where absolute values fail | surveillance, ministry | EV-RESULTS-SUMMARY, WHO-AI-ETHICS-2021 |
| **D** | FastAPI `/predict`, `/predictions/latest`, Leaflet dashboard | a transparency note travels with the output; alerts only through the mandated authority | ministry, surveillance | CM-PSNLP-2024-2028, WHO-AI-ETHICS-2021 |
| **SINK** | district health teams, PNLP, regional delegations | a human decides any change to campaigns, alerts or notifications | ministry | CM-PSNLP-2024-2028, (WHO-IHR-2005: to add) |
| **MLFO** | `orchestrator.py`, `scheduler.py`, drift monitor (PSI / KS / Mann-Whitney), `model_versions` | drift triggers flagging; model updates approved by a named body | surveillance, ministry | EV-MLOPS-PLATFORM, EV-INCREMENTAL |
| **ML sandbox** | `test_mlops.py`, the four validation regimes, the ITU AI for Good Lab sandbox | retrain or recalibrate in the sandbox before production; data that enters the sandbox respects transfer rules | surveillance, dpa | ITU-Y3172-2019, CM-LAW-2024-017 |

Each gap in the register carries the Y.3172 nodes it concerns (`y3172` in
`gaps.csv`), and each catalog action carries the nodes it acts on
(`catalog.py`).

## 2 · AI Readiness Framework 2.0, by perspective

| Hackathon perspective | Where it appears in the solution |
|---|---|
| Open data and open-source management | Open corpus, SHA-256 pinned, with re-fetch from the issuing bodies; the code is open in the GitHub repository; the knowledge base exports to the ITU toolkit's ChromaDB layout |
| Generative AI content ecosystem | LLM backends are optional and bounded: they propose, and the verbatim gate and the action catalog decide; refusals and model ids are logged |
| Contextualisation and regional focus | Bilingual FR/EN retrieval; Cameroonian law and strategy; region-specific validity (LORO, Extrême-Nord scenario) |
| AI integration in domains and cross-domain analysis | health × climate × telecom × data protection in every scenario; cross-domain consultations between agents |
| Human interaction and supervision | every high-impact action waits for a human decision (scripted or `--interactive`), and that decision is recorded in the audit chain |
| Policy and implementation opportunity identification | 13 gap probes; each finding is classed as absent, weak or addressed, with national evidence and global practice examples |
| AI for social inclusion | the model's main value is serving districts that do not report cases (no case history needed); bed-net and community health worker targeting raises automated-decision safeguards (S2) |
| Digital infrastructure and energy | low-cost LoRa mesh and edge collection; the IoT security and sustainable funding probes |

### The 13 dimensions

| Dimension | Gap probes and actions that map to it |
|---|---|
| D1 Data/Model Marketplace | G-HEALTH-DATA-TRANSFER, G-INDICATOR-GOVERNANCE |
| D3 Cross-Domain Correlation | G-DATA-SHARING |
| D4 Contextualization and Regional Impact | G-MODEL-VALIDATION, `LOCAL_CALIBRATION_PERIOD` |
| D5 Integration of AI in Workflows | G-MODEL-VALIDATION, G-MODEL-CHANGE, G-INDICATOR-GOVERNANCE |
| D6 Human Interface | G-TRANSPARENCY |
| D7 Strategy Alignment | G-ALERT-AUTHORITY, G-DATA-SHARING, G-IHR-PREDICTED, G-SUSTAINABLE-FUNDING |
| D8 Collaboration with AI | G-AUTOMATED-DECISION |
| D9 Impacts of Humans in AI Integration | G-MODEL-CHANGE |
| D10 AI & Policies | G-ALERT-AUTHORITY, G-AUTOMATED-DECISION, G-AI-HEALTH-REGULATION, G-MODEL-VALIDATION, G-HEALTH-DATA-TRANSFER, G-TRANSPARENCY |
| D13 Digital Infrastructure | G-SENSOR-STANDARD, G-IOT-SECURITY, G-SUSTAINABLE-FUNDING |

D2, D11 and D12 are not covered by a probe; they are discussed in the report
where relevant.
