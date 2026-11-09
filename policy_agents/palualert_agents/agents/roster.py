"""The five institutional agents.

surveillance  domain-application agent; the only one with tools (palualert_app)
ministry      institutional participant: MINSANTE / PNLP, National IHR Focal Point
dpa           institutional participant: personal data protection authority
telecom       institutional participant: telecom regulator and cybersecurity agency
advisor       policy and legal adviser: global practice and gap mapping

Rule questions are written in the language of the documents they target:
French for the Cameroonian corpus, English for global guidance and for the
project's own validation evidence.
"""
from __future__ import annotations

from palualert_agents.agents.base import Agent, Event, Rule
from palualert_agents.mews_client import MewsClient, correct_siting_offset


class SurveillanceAgent(Agent):
    id = "surveillance"
    name = "Surveillance & Model Operations agent"
    institution = "PaluAlert technical unit, PNLP data management"
    mandate = ("Operate the malaria early-warning models, report forecasts together with "
               "their validity envelope, detect data and model failures. It may flag, "
               "quarantine and correct data; it may not issue public alerts or change "
               "public-health activities.")
    kb_filters = {"scopes": ["evidence", "standard"]}
    rules = (
        Rule("sensor_bias",
             ("QUARANTINE_SENSOR_FEED", "APPLY_SENSOR_CORRECTION", "FLAG_PREDICTIONS_UNRELIABLE",
              "CERTIFY_SENSOR_SITING"),
             ("sensor sited badly temperature offset dew point costs forecast",
              "provenance rule models trained exclusively on reanalysis no IoT measurement"),
             "The node disagrees with the reanalysis the models were trained on; the "
             "validation study traced this to a siting offset that changes the forecast.",
             (("telecom", "Was the LoRa node relocated or reconfigured, and is it operating within its authorised radio parameters?"),),
             ("G-SENSOR-STANDARD",)),
        Rule("prediction_sensitive_to_sensor", ("FLAG_PREDICTIONS_UNRELIABLE",),
             ("offset-corrected sensor reanalysis no retraining",),
             "Re-scoring the same month with corrected inputs moves the forecast; the raw "
             "feed must not drive decisions."),
        Rule("drift_major", ("FLAG_PREDICTIONS_UNRELIABLE",),
             ("drift detection PSI Kolmogorov-Smirnov monitoring",),
             "Input distribution has shifted beyond the PSI threshold.", (),
             ("G-MODEL-VALIDATION",)),
        Rule("campaign_downscale_request", (),
             ("relative risk within already-observed districts not calibrated absolute incidence",),
             "A Low output produced from a biased feed must not be used to scale down "
             "vector control.",
             (("ministry", "A regional delegation proposes to scale down vector control because the dashboard shows Low risk. What procedure governs changes to planned malaria campaigns?"),),
             ("G-ALERT-AUTHORITY",)),
        Rule("nationwide_deployment_request",
             ("LOCAL_CALIBRATION_PERIOD", "RANK_ONLY_OUTPUT", "PUBLISH_TRANSPARENCY_NOTE"),
             ("Leave-One-Region-Out deployment in an unseen region",
              "ranks district burden Spearman worst-quartile absolute prediction fails",
              "do not deploy to a new region without a local calibration period"),
             "Validation shows the model ranks districts well nationally but its absolute "
             "forecasts fail in unseen regions and years.", (),
             ("G-MODEL-VALIDATION", "G-TRANSPARENCY")),
        Rule("foreign_cloud_training", ("PSEUDONYMISE_AGGREGATE",),
             ("Y.3172 sandbox training testing before deployment",),
             "Fine-tuning can run in a sandbox, but the data involved are health data.",
             (("dpa", "A partner offers to fine-tune the model on health-area case data hosted on a foreign cloud. Under what conditions may these data be transferred abroad?"),),
             ("G-HEALTH-DATA-TRANSFER",)),
        Rule("performance_drift", ("FLAG_PREDICTIONS_UNRELIABLE",),
             ("frozen model degrades over time doing nothing is the worst option",),
             "Errors grow when the model is never updated.", (), ("G-MODEL-VALIDATION",)),
        Rule("indicator_definition_change",
             ("VERSION_INDICATOR_DEFINITION", "RETRAIN_OR_RECALIBRATE"),
             ("indicator break change of definition not epidemiology",
              "recalibration has no hyperparameter fine-tuning fragile"),
             "Part of the apparent drop is a change of case definition; the model must be "
             "recalibrated on one consistent definition.",
             (("ministry", "Who is mandated to approve a new model version before it is used operationally?"),),
             ("G-INDICATOR-GOVERNANCE", "G-MODEL-CHANGE")),
        Rule("model_update_proposal", ("APPROVE_MODEL_UPDATE",),
             ("Model Registry model_versions schema only Retraining Pipeline not implemented",),
             "A new model version should be formally approved before operational use; "
             "the platform records versions but no approval step exists."),
        Rule("cross_border_signal", ("RANK_ONLY_OUTPUT",),
             ("between-region ranking geography dominance",),
             "The model can rank border districts but cannot confirm cases."),
    )

    def __init__(self, *a, client: MewsClient | None = None, **kw):
        super().__init__(*a, **kw)
        self.client = client or MewsClient()

    def run_tools(self, events: list[Event], step: int) -> list[dict]:
        results = []
        for e in events:
            if not e.tool:
                continue
            name, args = e.tool["name"], dict(e.tool.get("args", {}))
            try:
                if name == "compare_inputs":
                    out = self._compare_inputs(**args)
                elif name == "predict_series":
                    out = self._predict_series(**args)
                else:
                    out = {"error": f"unknown tool {name}"}
            except Exception as ex:                 # a failed tool is evidence too
                out = {"error": f"{type(ex).__name__}: {ex}"[:300]}
            out = {"tool": name, "event": e.id, "mews": self.client.mode, **out}
            self.audit.record("tool_call", self.id, {"args": args, "result": out}, step)
            results.append(out)
        return results

    def _compare_inputs(self, district: str, year: int, month: int, precipitation_mm: float,
                        variants: dict, offset_c: float | None = None) -> dict:
        """Score the same district-month under several input variants."""
        if offset_c is not None and "sensor_raw" in variants:
            raw = variants["sensor_raw"]
            t, rh = correct_siting_offset(raw["temperature_c"], raw["humidity_pct"], offset_c)
            variants = {**variants, "sensor_corrected": {
                "temperature_c": t, "humidity_pct": rh, "pressure_hpa": raw["pressure_hpa"]}}
        rows = []
        for label, v in variants.items():
            r = self.client.predict([{"district": district, "year": year, "month": month,
                                      "precipitation_mm": precipitation_mm, **v}])
            m = r["months"][0]
            rows.append({"variant": label, **v, "predicted_cases": m["predicted_cases"],
                         "incidence_per_1000": m["predicted_incidence"],
                         "risk_level": m["risk_level"], "threshold": m["threshold"],
                         "prediction_id": m["prediction_id"]})
        ref = rows[0]["predicted_cases"] or 1
        for r in rows:
            r["vs_reference_pct"] = round(100 * (r["predicted_cases"] - ref) / ref, 1)
        derived = []
        if any(abs(r["vs_reference_pct"]) >= 5 for r in rows if r["variant"] == "sensor_raw"):
            derived.append("prediction_sensitive_to_sensor")
        if any(r["risk_level"] == "High" for r in rows):
            derived.append("high_risk_output")
        if rows and rows[0]["risk_level"] == "Low":
            derived.append("low_risk_output")
        return {"district": district, "period": f"{year}-{month:02d}", "rows": rows,
                "derived_signals": derived}

    def _predict_series(self, district: str, readings: list[dict]) -> dict:
        r = self.client.predict([{"district": district, **x} for x in readings])
        months = [{k: m[k] for k in ("year", "month", "predicted_cases", "predicted_incidence",
                                     "risk_level", "model_used", "threshold")}
                  for m in r["months"]]
        derived = ["high_risk_output"] if any(m["risk_level"] == "High" for m in months) \
            else ["low_risk_output"]
        return {"district": district, "region": r["region"], "population": r["population"],
                "months": months, "derived_signals": derived}


class MinistryAgent(Agent):
    id = "ministry"
    name = "Ministry of Public Health / PNLP agent"
    institution = "MINSANTE, National Malaria Control Programme, National IHR Focal Point"
    mandate = ("Decide the public-health response: alerts, campaigns, field verification, "
               "and notifications under the International Health Regulations. Operational "
               "use of models is its decision.")
    kb_filters = {"scopes": ["national", "global"],
                  "domains": ["health", "malaria", "surveillance", "digital_health"]}
    rules = (
        Rule("campaign_downscale_request",
             ("HOLD_ALERT_PENDING_VERIFICATION", "FIELD_VERIFICATION", "MAINTAIN_VECTOR_CONTROL"),
             ("pulvérisation intradomiciliaire moustiquaires imprégnées campagne planification district",
              "surveillance épidémiologique riposte seuil épidémique district de santé"),
             "Planned vector control follows the national strategic plan; a single model "
             "output is not a basis to scale it down without field confirmation.",
             (("surveillance", "Is the Low-risk output shown for this district reliable enough to change a planned vector-control campaign?"),),
             ("G-ALERT-AUTHORITY",)),
        Rule("low_risk_output", ("FIELD_VERIFICATION",),
             ("complétude promptitude des rapports DHIS2 qualité des données",),
             "Low risk is checked against routine surveillance before any decision."),
        Rule("high_risk_output", ("ISSUE_PUBLIC_ALERT", "FIELD_VERIFICATION"),
             ("détection et riposte aux épidémies de paludisme seuil",),
             "Forecast exceeds the regional threshold.", (), ("G-ALERT-AUTHORITY",)),
        Rule("nationwide_deployment_request", ("DEPLOY_NATIONWIDE",),
             ("réduire la morbidité liée au paludisme d'ici 2028",
              "santé numérique système d'information sanitaire déploiement national"),
             "Ministerial instruction, consistent with the strategic plan's national targets.",
             (("advisor", "What global guidance applies before a health AI tool is scaled to regions where it was not validated?"),),
             ("G-AI-HEALTH-REGULATION",)),
        Rule("cross_border_signal",
             ("FIELD_VERIFICATION", "NOTIFY_WHO_IHR", "INFORM_NEIGHBOUR_COUNTRY"),
             ("notification events public health emergency of international concern 24 hours",
              "collaboration transfrontalière pays voisins paludisme"),
             "A possible cross-border event must be assessed under the IHR before notifying.",
             (("advisor", "Does a model-predicted, unconfirmed risk increase near a border trigger IHR notification?"),),
             ("G-IHR-PREDICTED",)),
        Rule("indicator_definition_change", ("FIELD_VERIFICATION",),
             ("définition de cas paludisme confirmé indicateurs de surveillance",),
             "The indicator change is a data-governance event, not an epidemiological one.",
             (), ("G-INDICATOR-GOVERNANCE",)),
        Rule("model_update_proposal", (),
             ("validation d'outils et de nouvelles technologies comité technique",),
             "No national procedure for approving model versions was identified.",
             (("advisor", "Which body approves updates to an AI system used in health in global practice?"),),
             ("G-MODEL-CHANGE",)),
    )


class DataProtectionAgent(Agent):
    id = "dpa"
    name = "Data Protection Authority agent"
    institution = "Personal Data Protection Authority created by Law No. 2024/017"
    mandate = ("Supervise the processing of personal data, including health data: lawful "
               "basis, minimisation, impact assessment, security and cross-border transfers.")
    kb_filters = {"domains": ["data_protection"], "scopes": ["national", "regional",
                                                             "comparator", "global"]}
    rules = (
        Rule("sensor_relocation_household", ("MINIMISE_LOCATION_DATA", "REQUIRE_DPIA"),
             ("données à caractère personnel localisation personne physique identifiable",
              "minimisation finalité déterminée explicite et légitime"),
             "Storing the GPS position of the household hosting a node is personal data "
             "that the forecast does not need.", (), ("G-DATA-SHARING",)),
        Rule("foreign_cloud_training",
             ("REQUIRE_DPIA", "PSEUDONYMISE_AGGREGATE", "BLOCK_TRANSFER"),
             ("transfert de données à caractère personnel vers un pays tiers niveau de protection",
              "données sensibles données de santé interdiction traitement exceptions",
              "cross-border transfer of personal data adequate level of protection"),
             "Identifiable health data cannot leave the country without the safeguards the "
             "law requires; aggregated, pseudonymised data reduce the risk.", (),
             ("G-HEALTH-DATA-TRANSFER",)),
        Rule("nationwide_deployment_request", (),
             ("décision produisant des effets juridiques fondée sur un traitement automatisé",),
             "District targeting driven by a model may fall under automated-processing rules.",
             (), ("G-AUTOMATED-DECISION",)),
        Rule("indicator_definition_change", (),
             ("qualité des données exactitude mise à jour",),
             "Data accuracy obligations apply to surveillance data reused by models."),
    )


class TelecomAgent(Agent):
    id = "telecom"
    name = "Telecom regulator & cybersecurity agent"
    institution = "Telecommunications Regulatory Board (ART) and ANTIC"
    mandate = ("Regulate radio spectrum and electronic communication networks; supervise "
               "the security of networks and information systems.")
    kb_filters = {"domains": ["telecom", "cybersecurity", "iot"],
                  "scopes": ["national", "regional", "evidence"]}
    rules = (
        Rule("sensor_bias", ("SPECTRUM_COMPLIANCE_CHECK",),
             ("LoRa radio parameters frequency band duty cycle node",),
             "Before trusting a relocated node, confirm it operates within its radio "
             "parameters.", (), ("G-SENSOR-STANDARD",)),
        Rule("new_radio_node", ("SPECTRUM_COMPLIANCE_CHECK", "SECURE_IOT_CHANNEL"),
             ("security of electronic communication networks and information systems audit",
              "MQTT broker gateway encryption channel"),
             "New nodes join a network that carries public-health data.", (),
             ("G-IOT-SECURITY",)),
        Rule("sensor_relocation_household", ("SECURE_IOT_CHANNEL",),
             ("electronic communication operators shall preserve traffic data",),
             "Raw feeds with location data raise the security requirement."),
    )


class PolicyAdvisorAgent(Agent):
    id = "advisor"
    name = "Policy & legal adviser agent"
    institution = "Independent adviser on global AI-for-health practice"
    mandate = ("Map the situation to global and regional practice, identify legislative, "
               "standards, responsibility and coordination gaps, and propose policy options. "
               "It has no executive power.")
    kb_filters = {"scopes": ["global", "regional", "comparator", "standard"]}
    rules = (
        Rule("sensor_bias", ("LOG_POLICY_GAP",),
             ("data quality and accuracy of inputs to AI systems for health",),
             "Input quality is a governance question, not only a technical one.", (),
             ("G-SENSOR-STANDARD",)),
        Rule("campaign_downscale_request", ("LOG_POLICY_GAP",),
             ("human oversight of decisions informed by artificial intelligence",),
             "Global guidance keeps a human accountable for decisions informed by AI.", (),
             ("G-ALERT-AUTHORITY",)),
        Rule("nationwide_deployment_request", ("LOG_POLICY_GAP",),
             ("evaluation of AI systems before deployment in new settings external validity",
              "risk-based regulation high-risk AI systems health"),
             "Scaling outside the validated setting is the classic failure mode named in "
             "global guidance.", (), ("G-AI-HEALTH-REGULATION", "G-MODEL-VALIDATION")),
        Rule("foreign_cloud_training", ("LOG_POLICY_GAP",),
             ("data sovereignty cross-border data flows health data",),
             "", (), ("G-HEALTH-DATA-TRANSFER",)),
        Rule("cross_border_signal", ("LOG_POLICY_GAP",),
             ("International Health Regulations notification assessment of events",),
             "", (), ("G-IHR-PREDICTED",)),
        Rule("indicator_definition_change", ("LOG_POLICY_GAP",),
             ("data standards interoperability metadata",),
             "", (), ("G-INDICATOR-GOVERNANCE", "G-DATA-SHARING")),
        Rule("model_update_proposal", ("LOG_POLICY_GAP",),
             ("monitoring and updating AI systems after deployment",),
             "", (), ("G-MODEL-CHANGE",)),
        Rule("new_radio_node", ("LOG_POLICY_GAP",),
             ("digital infrastructure connectivity energy for AI",),
             "", (), ("G-IOT-SECURITY",)),
    )


ROSTER = {cls.id: cls for cls in (SurveillanceAgent, MinistryAgent, DataProtectionAgent,
                                  TelecomAgent, PolicyAdvisorAgent)}
