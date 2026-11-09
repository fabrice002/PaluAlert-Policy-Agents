# PaluAlert Policy Agents

**AI agents that check the policy rules around an IoT malaria early-warning system**
Submission to the ITU AI for Good Lab Hackathon: United Arab Emirates (2026)

A malaria early-warning system for 197 Cameroonian health districts. It uses
XGBoost models on climate data from IoT sensors and reanalysis, served by a
FastAPI service with an autonomous MLOps pipeline. On top of it sit five
institutional AI agents:

| Agent | Role |
|---|---|
| surveillance | operates the forecasting models and calls the system's API |
| ministry of health / PNLP | decides the public-health response |
| data protection authority | supervises personal and health data |
| telecom regulator | supervises the radio network and cybersecurity |
| policy adviser | maps situations to global practice and finds gaps |

The agents reason over a bilingual knowledge base of national, regional and
global policy, built from 23 SHA-256-pinned documents. Error scenarios unfold
step by step, and each agent receives only part of the information. Every claim
must be a verbatim quote from a pinned source, every high-impact action waits
for a human, and every step is written to a hash-chained audit log. The output
is a register of policy, standards and responsibility gaps, each mapped to
ITU-T Y.3172 and the ITU AI Readiness Framework 2.0.

```
repository
├── policy_agents/         ★ the hackathon solution: knowledge base, agents, scenarios, reports
├── palualert_app/              the domain application: FastAPI + MLOps + dashboard + model bundle
├── documentation/         model validation results and their limits
├── national_validation/   validation on 2024–2025 national data
├── foumban_incremental/   incremental learning study in Foumban
├── sensor_validation/     IoT sensor compared with ERA5 reanalysis
└── iot_acquisition/       LoRa/Meshtastic sensor network and MQTT bridge

The last five folders hold evidence from the underlying thesis. They are loaded
into the knowledge base as project evidence.
```

## Run it (offline, no API key, about 2 minutes)

```bash
python -m venv env && env/Scripts/activate        # Windows; source env/bin/activate elsewhere
pip install -r policy_agents/requirements.txt -r palualert_app/app/requirements.txt
cd policy_agents
python -m palualert_agents run-all                      # three error scenarios -> outputs/*/report.html
python -m pytest tests -q
```

The processed knowledge base (`policy_agents/kb/processed/chunks.jsonl`)
ships with the repository, so the scenarios run without downloading anything.
To rebuild it from the original documents, run `python -m palualert_agents fetch`
and then `python -m palualert_agents ingest`. This re-downloads every source and
checks it against its SHA-256 pin in `kb/manifest.lock.json`. Scanned PDFs
need Tesseract with the `fra` and `eng` language data.

Example runs are in [`policy_agents/outputs/`](policy_agents/outputs/).
Open any `report.html` in a browser.

## Documentation

- [`policy_agents/README.md`](policy_agents/README.md): architecture, agents, scenarios, model backends
- [`policy_agents/docs/MAPPING_Y3172_READINESS.md`](policy_agents/docs/MAPPING_Y3172_READINESS.md): Y.3172 nodes and AI Readiness 2.0
- [`policy_agents/docs/TECHNICAL_REPORT.md`](policy_agents/docs/TECHNICAL_REPORT.md): technical report (Markdown version)
- [`palualert_app/README_RUN_THIS.md`](palualert_app/README_RUN_THIS.md): the early-warning service and dashboard
- [`documentation/RESULTS_SUMMARY.md`](documentation/RESULTS_SUMMARY.md): model validation and its limits

## Data notice

The knowledge-base sources are public documents from their issuing bodies.
The repository ships their manifest, hashes and processed text chunks; the
original files are re-obtained from the issuers by `fetch`. Raw PNLP
surveillance data from the underlying thesis are not included. The models in
`palualert_app/deployment_bundle/` were trained on district-month aggregates.

## License

The code and documentation of this project are under the MIT License
([`LICENSE.md`](LICENSE.md)). This does not cover third-party content:

- `palualert_app/frontend/vendor/leaflet/`: Leaflet 1.9.4, under its own BSD 2-Clause license.
- `policy_agents/kb/processed/chunks.jsonl` and the quotes in `policy_agents/outputs/`:
  excerpts of public documents, which remain the property of their issuers
  (listed in `policy_agents/kb/manifest.csv`).
- `palualert_app/frontend/src/data/`: Cameroon boundary files from public sources.
