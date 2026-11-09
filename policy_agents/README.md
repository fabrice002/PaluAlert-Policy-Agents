# policy_agents: policy agents for the malaria early-warning system

The submission for the **ITU AI for Good Lab Hackathon (UAE, 2026)**. This
folder adds a knowledge base and a multi-agent layer on top of the malaria
early-warning system in [`../palualert_app`](../palualert_app). The knowledge base holds
Cameroonian law and strategy, regional and global guidance, and the project's
own validation evidence. The agents stand for institutions with different
mandates. They work through step-by-step error scenarios built from the
system's documented failures. Every claim they make has to pass a verbatim
check against its source, and every step is written to a hash-chained audit
log.

```
 scenario (YAML) ── events released step by step, to named recipients only
        │
        ▼
 ┌──────────────── coordinator: 3-phase protocol per step ────────────────┐
 │ A  independent assessment   surveillance · ministry · dpa · telecom ·  │
 │                             advisor, each from its own inbox and its   │
 │                             own slice of the knowledge base            │
 │ B  consultation             questions routed to the mandated agent     │
 │ C  coordination             conflicts · unowned actions · human gate   │
 └──────────┬─────────────────────────────┬──────────────────────────────┘
            │                             │
   surveillance tools               evidence gate (verbatim) ── knowledge base
   palualert_app /predict, sensor           every claim = quote + chunk id     23 docs · ~2 400 chunks
   correction, validity envelope                                       FR + EN, SHA-256 pinned
            │                             │
            └──────────────┬──────────────┘
                           ▼
        audit.jsonl (hash chain) · transcript.md · report.html · gaps.csv
```

## Quick start

```bash
cd policy_agents
pip install -r requirements.txt -r ../palualert_app/app/requirements.txt

python -m palualert_agents fetch        # download and pin the sources (kb/manifest.csv)
python -m palualert_agents ingest       # parse, OCR scanned pages, chunk, index
python -m palualert_agents run-all      # the three scenarios, offline, no model needed
python -m pytest tests -q          # offline checks
```

Each run writes `outputs/<scenario>_<timestamp>/`, which contains:

| File | Contents |
|---|---|
| `report.html` | the readable report: events, assessments, quotes, coordination, gap register |
| `transcript.md` | the same as Markdown, with each agent's reasoning trace |
| `audit.jsonl` | every release, retrieval, tool call, claim, message, conflict, decision and gap, hash-chained |
| `gaps.csv` | the gap register |
| `run.json` | everything, machine-readable |

Check that an audit log has not been edited:

```bash
python -m palualert_agents verify outputs/<run>/audit.jsonl
```

Query the knowledge base directly:

```bash
python -m palualert_agents ask "transfert de données de santé vers un pays tiers" --scope national
```

## Model backends

By default (`AI4G_LLM_BACKEND=extractive`) no language model is called. Each
agent quotes the best-matching sentence from the passages it retrieved and
applies its rule table. This mode is deterministic and reproducible, and it is
the baseline the audit log can be checked against. If you choose a model, it
can add claims and actions, but it cannot remove the rule-based floor. Its
claims still pass through the verbatim gate, and it can only propose actions
from the catalog.

| Backend | Setting |
|---|---|
| Local, the ITU AI-RE toolkit default | `AI4G_LLM_BACKEND=ollama` (`qwen2.5:14b`, `AI4G_OLLAMA_URL`) |
| ITU sandbox or any OpenAI-compatible server | `AI4G_LLM_BACKEND=openai AI4G_OPENAI_BASE_URL=... AI4G_LLM_MODEL=...` |
| Claude | `AI4G_LLM_BACKEND=anthropic` (`claude-opus-5-5`; server-side refusal fallback on; summarised reasoning logged) |

The backend can also be set per run: `python -m palualert_agents run S2_unseen_region --backend ollama`.
Add `--interactive` to take the human decisions at the terminal instead of the scripted ones.

The surveillance agent runs palualert_app in-process against a throwaway database.
To use a running server instead, set `AI4G_MEWS_API_URL=http://localhost:8000`.

## The agents

| Agent | Stands for | Sees in the knowledge base | Tools |
|---|---|---|---|
| `surveillance` | PaluAlert technical unit, PNLP data management | project evidence, ITU standards | palualert_app `/predict`, sensor-offset correction |
| `ministry` | MINSANTE / PNLP, National IHR Focal Point | national + global health documents | - |
| `dpa` | data protection authority created by Law 2024/017 | data-protection documents, national to global | - |
| `telecom` | ART and ANTIC | telecom, cybersecurity and IoT documents | - |
| `advisor` | policy and legal adviser | global, regional, comparator, standards | - |

All 26 actions in [`palualert_agents/catalog.py`](palualert_agents/catalog.py) have an
expected owner. Actions that are high-impact, such as public alerts,
deployment, transfers, notifications and model updates, wait for a human
decision. Two actions have no owner (approving a model version and certifying
sensor siting). When an agent proposes one of these, the coordinator reports it
as a responsibility gap.

## The scenarios

| Scenario | Built from | What it tests |
|---|---|---|
| [S1 sensor siting](scenarios/S1_sensor_siting.yaml) | `sensor_validation`: +7.27 °C siting offset | a biased feed lowers the forecast; a region wants to scale down spraying; the fix creates a privacy problem |
| [S2 unseen region](scenarios/S2_unseen_region.yaml) | `national_validation`, LORO, Foumban external test | a scale-up order collides with the validity envelope; a foreign-cloud fine-tuning offer; a signal from across the border |
| [S3 indicator change](scenarios/S3_indicator_change.yaml) | `foumban_incremental`: A/B ratio 1.31 | a change of case definition looks like a drop in malaria; nobody is mandated to approve a new model version |

Each scenario lists the actions and gaps it expects. The run reports what it
found against that list in its "expected vs actual" section. These lists are
written by the scenario author, so they work as a regression check, not as an
independent benchmark.

## The knowledge base

[`kb/manifest.csv`](kb/manifest.csv) is curated by hand: one row per source,
with issuer, jurisdiction, scope, domains and URL. `fetch` pins each file by
SHA-256 in `kb/manifest.lock.json`. `ingest` keeps page numbers, OCRs scanned
pages (Tesseract `fra` + `eng`; set `AI4G_TESSDATA`) and tags article and
section numbers, so citations read like
`CM-LAW-2024-017 (Présidence de la République du Cameroun, 2024), art. 44, p. 12`.

**Sources still to add.** Seven of the 31 sources could not be fetched
automatically. Four WHO IRIS documents and the WHO AFRO-hosted 2020–2024
digital health plan are blocked for scripts, the Abu Dhabi DoH policy fails
certificate verification, and uaelegislation.gov.ae returns 403. One more file
(the Kenya strategy) downloaded but has no readable pages. To add any of them,
download it in a browser, save it as `kb/raw/<doc_id>.pdf`, then run `fetch`
and `ingest` again. It will be pinned as `"obtained": "manual"`. The gap
register names the missing sources that would strengthen each finding.

The OCR text of scanned laws contains recognition errors. The verbatim gate
compares against that same OCR text, so a quote stays traceable even when a
character is wrong. Before quoting a scanned law in the report, check the
passage against the PDF page cited.

For the ITU sandbox, `python -m palualert_agents.kb.to_chroma --dry-run` validates
the chunks as ChromaDB records in the toolkit's `kb_main` layout. Without
`--dry-run` it embeds them with `nomic-embed-text` and loads them. That path
needs `chromadb` and Ollama, and it has not been run here.

## Layout

```
policy_agents/
├── kb/manifest.csv            curated source list          (input)
├── kb/manifest.lock.json      SHA-256 pins                 (generated)
├── kb/raw/                    downloaded sources           (generated)
├── kb/processed/              chunks.jsonl, index, report  (generated)
├── palualert_agents/
│   ├── kb/                    fetch · ingest · retriever · to_chroma
│   ├── agents/                base (protocol) · roster (5 agents)
│   ├── catalog.py             actions, owners, conflicts, Y.3172, AI Readiness
│   ├── evidence.py            the verbatim gate
│   ├── gaps.py                13 gap probes and their analysis
│   ├── simulation.py          scenario engine and coordinator
│   ├── audit.py               hash-chained log + verifier
│   ├── llm.py                 extractive · ollama · openai · anthropic
│   ├── mews_client.py         palualert_app tools, sensor correction
│   └── report.py              transcript.md, report.html
├── scenarios/                 S1 · S2 · S3
├── docs/                      Y.3172 / Readiness mapping, technical report draft
└── tests/
```
