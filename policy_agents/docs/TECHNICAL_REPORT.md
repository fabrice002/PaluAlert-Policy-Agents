# AI for Good Lab Hackathon (UAE) · Team PaluAlert · PaluAlert Policy Agents

**AI agents that check the policy rules around an IoT malaria early-warning system**

- Team leader: OUANDJI NJANANG HERVÉ FABRICE
- Team members: OUANDJI NJANANG HERVÉ FABRICE, CHAMDJOU NGALEU FRANKLIN DUVAN
- Contact details: fabriceouandji@gmail.com · franklinduvan913@gmail.com
- GitHub link: [repository URL]/policy_agents

---

## 1 · Introduction

Temperature, humidity and rainfall control how fast mosquitoes develop. Cheap
IoT sensors can now measure these values in every health district. This makes
climate-based early warning one of the most useful AI tools for malaria control.

We start from a system that already works:
- it covers 197 health districts in Cameroon;
- it uses XGBoost models trained on 2019–2022 surveillance data and climate
  reanalysis data;
- it runs as a FastAPI service, with an automatic MLOps pipeline and drift
  monitoring;
- it receives data from a LoRa/Meshtastic sensor network.

Our question is: what happens **when the system is wrong**, and **who has the
right to act** when it is?

The system's own tests already show where it is wrong:
- It ranks districts well on new data (Spearman ρ = 0.859 across 194 districts).
- Its case counts do not carry over. R² falls to −0.461 when a whole region is
  left out of training, and to −1.74 on new years in Foumban.
- One badly placed sensor (+7.27 °C) lowered the forecast by 38 % in one district.
- A change in how cases are counted (ratio 1.31) looks like a 23 % fall in malaria.

These are real failures. We use them to build the error scenarios.

We add three parts:
1. **A knowledge base in English and French.** It holds 23 national, regional
   and global documents. Each file is fixed by its SHA-256 hash, and scanned
   files were read with OCR. The text is split into about 2,400 pieces, each
   with its page number.
2. **Five agents, one per institution.** Each agent has its own mandate, its
   own part of the knowledge base and its own information.
3. **A coordination process.** It records how the institutions would respond,
   with the source text for each claim. It also lists where laws, standards or
   mandates leave a question without an answer.

The solution covers every node of ITU-T Y.3172 and the AI Readiness Framework
2.0 (section 4, and `docs/MAPPING_Y3172_READINESS.md`).

## 2 · Description of the use case

**Problem.** Malaria is still a major health problem in Cameroon. The national
strategic plan 2024–2028 aims to cut malaria cases by at least 75 % by 2028,
compared with 2015 (CM-PSNLP-2024-2028, p. 71). Surveillance reports arrive
late, and many districts send incomplete reports. An early warning based on
climate data is therefore useful.

But when a model result reaches a regional office, a campaign planner or a
neighbouring country, it becomes a public-health decision. Several
institutions are involved:
- the Ministry of Health and the National Malaria Control Programme (PNLP);
- the data protection authority created by Law 2024/017;
- the telecom regulator and the cybersecurity agency;
- the IHR focal point (International Health Regulations).

**What existing tools miss.** Early-warning dashboards show a forecast, but not
the conditions under which the forecast can be trusted. They do not say that a
result came from a sensor that was not calibrated, or from a region where the
model was never tested. They also do not say who may act on the result, or
under which law.

**What our solution adds.**
- The agents attach to every result its source and the conditions under which
  it is valid.
- Before acting, an agent asks the institution whose mandate covers the question.
- An agent rejects any claim that it cannot quote word for word from a fixed
  source document.
- High-impact decisions go to a human.
- When no national law or mandate covers a question, the gap is recorded, with
  the closest national text and examples from other countries.

## 3 · Use case requirements

| Node | Requirement |
|---|---|
| SRC | Sensors are placed and calibrated to a written standard. Nodes stay within their allowed radio settings (868 MHz, duty cycle). The definition of a malaria case has a version number. |
| C | The link from sensor to broker is authenticated and encrypted. The purpose of the data collection is stated. No household identifiers are stored. |
| PP | Every batch must pass 16 checks before use. Only documented corrections are applied, such as the sensor placement offset at constant dew point. Corrected results are marked. |
| M | External validation, with a published statement of where the model is valid. Local calibration before use in a new region. Recalibration rather than untested fine-tuning. |
| P | Results outside the valid range are marked. Only rankings are given where case counts are not reliable. SHAP explanations. |
| D | A note on the model's limits comes with every result. Alerts, and decisions to lower an alert, go through the institution in charge. |
| SINK | A human decides changes to campaigns, alerts, notifications and deployments, and the decision is logged. |
| MLFO / sandbox | Drift monitoring (PSI / KS) and performance monitoring. Model updates are tested in the sandbox and approved by a named body. |

## 4 · Mapping with ITU-T Y.3172, Readiness 2.0 and domain policies

| Node | Use case (malaria early warning) | Readiness 2.0 | Documents (knowledge base) |
|---|---|---|---|
| SRC | LoRa sensor nodes, ERA5 reanalysis, PNLP DHIS2 reports | D13 Digital infrastructure; D1 Data | EV-SENSOR-VALIDATION; CM-LAW-2010-012 (ANTIC, s. 7); CM-PSNLP-2024-2028 |
| C | MQTT broker, climate source adapters | D13; D10 AI & policies | CM-LAW-2024-017 (art. 32: prior authorisation for transfers); AU-MALABO-2014 |
| PP | 16 blocking checks; shared features; sensor placement correction | D5 Integration in workflows | EV-MLOPS-PLATFORM |
| M | XGBoost NO-LAG → LAG chain | D4 Contextualisation | EV-RESULTS-SUMMARY; EV-NATIONAL-VALIDATION; WHO-AI-ETHICS-2021 |
| P | regional 75th-percentile threshold; valid range of the model; SHAP | D8 Collaboration with AI; D10 | CM-LAW-2024-017 (art. 44–45: automated decisions, human intervention) |
| D | API, dashboard, note on model limits | D6 Human interface | WHO-AI-ETHICS-2021 (transparency, explainability) |
| SINK | district teams, PNLP, regional delegations, IHR focal point | D7 Strategy alignment | CM-PSNLP-2024-2028 (surveillance, epidemic response) |
| MLFO / sandbox | scheduler, drift monitor, model versions, ITU sandbox | D5; D9 Humans in AI | ITU-Y3172-2019 (sandbox); EV-INCREMENTAL |

The full table, and how the eight hackathon perspectives are covered, are in
`docs/MAPPING_Y3172_READINESS.md`.

**How the agents work.** There are five agents:

| Agent | Role |
|---|---|
| surveillance | runs the early-warning system; the only agent that calls palualert_app |
| ministry | MINSANTE / PNLP and the IHR focal point |
| dpa | the data protection authority |
| telecom | ART and ANTIC |
| advisor | practice in other countries, and gaps |

Each agent receives only the events sent to it, and searches only its own part
of the knowledge base. It proposes actions from a shared list of 26. Each action
has an expected owner, and 13 of them are high-impact. For each step, the
coordinator runs three phases:
- **A.** Each agent makes its own assessment.
- **B.** Each question goes to the agent whose mandate covers it.
- **C.** Coordination. The coordinator finds proposals that conflict, actions
  that no institution is in charge of, and owners who were not asked. It sends
  high-impact actions to a human.

A claim is accepted only if its quote appears word for word in the cited piece
of text, and only if the agent actually retrieved that piece. Every data
release, search, tool call, claim, message, decision and gap is written to a
JSONL log. Each record contains the SHA-256 hash of the one before it, and
`python -m palualert_agents verify` checks the whole chain.

By default, no language model is used: the agents quote text directly from the
documents, and the output is the same on every run. Ollama, an
OpenAI-compatible endpoint such as the ITU sandbox, or Claude can be turned on.
A language model can add claims and actions, but they go through the same check
and the same action list.

## 5 · Error scenarios

The three runs below are offline, without a language model, with palualert_app
running in the same process. Each run produced an audit log of 35 to 47
records, and each log passed the hash check.

**S1: A badly placed sensor lowers the forecast.**
1. *Step 1.* Only the surveillance agent sees the node reading (+7.27 °C
   compared with ERA5). It runs the forecast again for Biyem Assi, April 2026,
   through palualert_app:
   - raw sensor data: 3,509 cases;
   - reanalysis data: 3,835 cases (−8.5 % with this month's example rainfall;
     −37.9 % in the thesis case);
   - corrected sensor data: 3,837 cases (+0.1 %).

   The agent stops using the sensor feed, corrects it, marks the affected
   results, and asks for the sensor placement to be certified. The coordinator
   reports that **no institution has the mandate to certify sensor placement**.
   Separately, the telecom agent sees only that the node has moved. It proposes
   a radio spectrum check under the ANTIC mandate (Law 2010/012, s. 7).
2. *Step 2.* A regional office wants to delay indoor spraying because the
   dashboard shows "Low". Lowering an alert is the ministry's decision. The
   ministry orders a field check and proposes to keep the campaign. The human
   in charge of the exercise approves.
3. *Step 3.* The vendor proposes to move the node into a household yard, and to
   store the household's GPS position and phone number. The data protection
   agent asks to collect less data and to run an impact assessment. The telecom
   agent asks for a secure channel.

**S2: Using the model in a region where it was never tested.**
1. *Step 1.* The minister orders national use. The surveillance agent runs the
   forecast for Mokolo (Extrême-Nord) through palualert_app: Low for June–August
   2027. It cites the national validation: the model places 68 % of the
   worst-quartile districts correctly, against 25 % by chance, but its case
   counts are not reliable. It proposes local calibration, rankings only, and a
   note on the model's limits.

   The coordinator finds a conflict between `DEPLOY_NATIONWIDE` and
   `LOCAL_CALIBRATION_PERIOD`, and the human rejects national use. The data
   protection agent is told that the scores will be used to target bed nets and
   community health worker visits. It cites Law 2024/017 art. 44–45: people have
   the right to object to decisions made only by automated processing, and to
   ask for a human to step in.
2. *Step 2.* A partner offers to fine-tune the model on a foreign cloud with
   health-area data. The data protection agent cites art. 32: sending data
   abroad needs prior authorisation from the authority. It asks for an impact
   assessment and for the data to be aggregated, and proposes to block the
   transfer. The human approves.
3. *Step 3.* An unconfirmed rumour comes from across the Nigerian border. The
   ministry proposes a field check and an IHR consultation. The human waits for
   confirmed cases before any notification, and approves sharing the ranking
   with the neighbouring country.

**S3: A change in how cases are counted, with no announcement.** The error of
the frozen model grows, and the data manager reports the change of indicator
(ratio 1.31). The surveillance agent gives the case definition a version number
and proposes recalibration. The human approves. Then a fine-tuned version is
proposed for production, and the agent asks who may approve it. The ministry
finds no rule for this, and the coordinator reports `APPROVE_MODEL_UPDATE` as an
action that no institution is in charge of.

**Limits of the solution.**
1. We wrote the lists of expected results for each scenario ourselves. The
   100 % score on actions and gaps therefore only shows that nothing changed
   between runs. It is not an independent benchmark.
2. Search uses TF-IDF with an English–French glossary. Some accepted quotes are
   on the right topic but weak. A reviewer must read the quote itself, not only
   the reference.
3. The scanned laws were read with OCR (Tesseract, French and English), and the
   quotes keep the reading errors.
4. Seven sources could not be downloaded automatically: WHO IHR, WHO regulatory
   considerations, the WHO surveillance manual, the WHO GTS, the 2020–2024
   digital health plan, the Abu Dhabi DoH policy and the UAE PDPL. The Kenya PDF
   cannot be read. Findings that depend on these sources say so.
5. Without a language model, the quote check cannot catch anything, because the
   quotes are copied from the text itself. The check matters when a language
   model is used. The tests show that it rejects paraphrases, unknown text
   pieces, and pieces the agent did not retrieve.
6. These runs did not use any language model backend.

## 6 · Policy and standards gaps

"Not found" means *not found in the seven national documents of the knowledge
base*. It describes these documents only, and it comes with the closest national
text. It does not mean that no rule exists.

| Gap | Category | National documents | Practice elsewhere (knowledge base) | Raised in |
|---|---|---|---|---|
| No one is named to act on model alerts, or on decisions to lower them | Unclear responsibility | not found | WHO 2021 ethical principles (weak match; WHO surveillance manual to add) | S1, S3 |
| No standard for placing and calibrating sensors that feed health models; no certifying body | Standards gap | not found | none in the knowledge base (WMO guidance to add) | S1 |
| No standard for validating health models or monitoring them after deployment | Standards gap | not found | ITU AI Readiness, contextualisation metrics (weak match; WHO 2023 regulatory considerations to add) | S1–S3 |
| No approval process for new model versions | Unclear responsibility | weak (only maintenance contracts found) | none accepted (WHO 2023 regulatory considerations to add) | S3 |
| Changes to indicator definitions are not versioned or announced to data users | Coordination problem | weak (the 2026–2030 digital health plan plans indicator workshops) | none accepted (WHO surveillance manual to add) | S3 |
| A predicted, unconfirmed cross-border risk has no place in IHR practice | Coordination problem | not found | WHO 2021: predictive analytics can forecast outbreaks (IHR text to add) | S2 |
| No rule requiring public bodies to explain the models they use | Standards gap | not found | WHO 2021 transparency/explainability; EU AI Act documentation duties | S2 |
| No health-sector rule for AI decision support | Legislative gap | weak | WHO 2021 §4.7; EU AI Act risk tiers | S2 |
| No security baseline for IoT networks used in health surveillance | Technology gap | not found (ANTIC's security mandate exists in Law 2010/012, s. 7) | none accepted above the relevance threshold | S1 |
| Data sharing between health, weather and telecom bodies | Coordination problem | weak (Cellule des Informations Sanitaires mandate, Decree 2013/093) | AU AI Strategy; WHO 2021 (NIH data-sharing policy example) | S1–S3 |
| Automated decisions used for targeting | Legislative | **covered**: Law 2024/017 art. 44–45 | Malabo Convention; WHO 2021 | S2 |
| Sending health data abroad | Legislative | **covered**: Law 2024/017 art. 32 (prior authorisation) | Malabo Convention (adequate protection) | S2 |

Two findings matter for policy:
1. **The data protection law is ahead of the health sector.** Cameroon's 2024
   law already covers automated decisions and data transfers abroad. What is
   missing is a set of rules, inside the health sector, for AI results: who may
   act on them, how they are validated, versioned and certified, and how their
   limits are shown to users.
2. **Most gaps are about responsibilities and standards, not laws.** They can be
   closed by assigning mandates and adopting standards, without new laws.

These gaps are not specific to Cameroon. Any health ministry that uses
climate-based AI early warning faces the same questions: who may raise or lower
an alert, who approves a model change, who certifies sensors, and how the
model's limits are shown.
