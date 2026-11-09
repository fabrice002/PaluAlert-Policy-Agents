"""Shared vocabulary of the simulation: actions, institutions, conflicts, and the
ITU reference frames (Y.3172 components, AI Readiness dimensions).

Agents may only recommend actions from this catalog. An action carries its
expected owner (the institution whose mandate covers it) and whether it is
high-impact, in which case it cannot be executed without a human decision.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    code: str
    label: str
    owner: str | None          # agent id whose mandate covers it; None = unassigned
    high_impact: bool = False
    y3172: tuple[str, ...] = ()


ACTIONS: dict[str, Action] = {a.code: a for a in [
    # public-health response
    Action("ISSUE_PUBLIC_ALERT", "Issue a public malaria risk alert for the district",
           "ministry", True, ("D", "SINK")),
    Action("HOLD_ALERT_PENDING_VERIFICATION", "Hold any alert or de-escalation until field data confirm",
           "ministry", False, ("P",)),
    Action("FIELD_VERIFICATION", "Request field verification: RDT positivity, stock levels, DHIS2 completeness",
           "ministry", False, ("SRC",)),
    Action("MAINTAIN_VECTOR_CONTROL", "Keep the planned vector-control / bed-net activities unchanged",
           "ministry", True, ("SINK",)),
    Action("NOTIFY_WHO_IHR", "Notify or consult WHO through the National IHR Focal Point",
           "ministry", True, ("D",)),
    Action("INFORM_NEIGHBOUR_COUNTRY", "Share surveillance information with the neighbouring country",
           "ministry", True, ("D",)),
    # model and data operations (Y.3172 MLFO / sandbox)
    Action("QUARANTINE_SENSOR_FEED", "Quarantine the affected IoT feed; fall back to reanalysis",
           "surveillance", False, ("SRC", "C", "MLFO")),
    Action("APPLY_SENSOR_CORRECTION", "Apply the documented siting-offset correction and flag outputs as corrected",
           "surveillance", False, ("PP",)),
    Action("FLAG_PREDICTIONS_UNRELIABLE", "Flag affected predictions as outside the validity envelope",
           "surveillance", False, ("P", "D")),
    Action("LOCAL_CALIBRATION_PERIOD", "Run a local calibration period before using outputs in a new region",
           "surveillance", False, ("M", "MLFO", "SANDBOX")),
    Action("RANK_ONLY_OUTPUT", "Publish relative district ranking only, not absolute case forecasts",
           "surveillance", False, ("P", "D")),
    Action("RETRAIN_OR_RECALIBRATE", "Recalibrate or fine-tune the model on the new data definition",
           "surveillance", True, ("M", "MLFO", "SANDBOX")),
    Action("VERSION_INDICATOR_DEFINITION", "Record the case-indicator change as a versioned data-contract event",
           "surveillance", False, ("PP", "MLFO")),
    Action("DEPLOY_NATIONWIDE", "Extend operational use of the model to all regions",
           "ministry", True, ("MLFO", "D")),
    Action("SUSPEND_MODEL_IN_REGION", "Do not use the model operationally in the uncalibrated region",
           "ministry", True, ("MLFO",)),
    Action("APPROVE_MODEL_UPDATE", "Formally approve a new model version for operational use",
           None, True, ("MLFO",)),
    # data protection
    Action("REQUIRE_DPIA", "Require a data-protection impact assessment before processing",
           "dpa", False, ("SRC", "C")),
    Action("PSEUDONYMISE_AGGREGATE", "Process only pseudonymised, district-aggregated data",
           "dpa", False, ("PP",)),
    Action("AUTHORISE_TRANSFER", "Authorise the cross-border transfer of health data",
           "dpa", True, ("C",)),
    Action("BLOCK_TRANSFER", "Do not transfer identifiable health data abroad",
           "dpa", True, ("C",)),
    Action("MINIMISE_LOCATION_DATA", "Do not store household-level location of sensor hosts",
           "dpa", False, ("SRC",)),
    # telecom and cybersecurity
    Action("SPECTRUM_COMPLIANCE_CHECK", "Verify radio band, power and duty cycle of the LoRa nodes",
           "telecom", False, ("SRC", "C")),
    Action("SECURE_IOT_CHANNEL", "Require authentication and encryption on the sensor-to-broker channel",
           "telecom", False, ("C",)),
    Action("CERTIFY_SENSOR_SITING", "Certify the siting and calibration of environmental sensors",
           None, False, ("SRC",)),
    # policy adviser
    Action("LOG_POLICY_GAP", "Log a policy, standards or responsibility gap with global examples",
           "advisor", False, ()),
    Action("PUBLISH_TRANSPARENCY_NOTE", "Publish a model card / transparency note with the validity envelope",
           "surveillance", False, ("D",)),
]}

# Mutually exclusive recommendations: proposing both is a conflict to resolve.
CONFLICTS: list[tuple[str, str, str]] = [
    ("ISSUE_PUBLIC_ALERT", "HOLD_ALERT_PENDING_VERIFICATION",
     "alert now vs. wait for verification"),
    ("AUTHORISE_TRANSFER", "BLOCK_TRANSFER", "transfer health data vs. keep it in country"),
    ("DEPLOY_NATIONWIDE", "SUSPEND_MODEL_IN_REGION", "scale up vs. stay inside the validity envelope"),
    ("DEPLOY_NATIONWIDE", "LOCAL_CALIBRATION_PERIOD", "deploy now vs. calibrate first"),
]

INSTITUTIONS = {
    "surveillance": "PaluAlert surveillance & model operations (PNLP data unit)",
    "ministry": "Ministry of Public Health / PNLP, incl. National IHR Focal Point",
    "dpa": "Personal Data Protection Authority (Law 2024/017)",
    "telecom": "Telecommunications Regulatory Board (ART) and ANTIC",
    "advisor": "Policy & legal adviser (global best practice)",
}

Y3172 = {
    "SRC": "Source - where data is generated (IoT node, reanalysis, DHIS2)",
    "C": "Collector - gathers data from sources (MQTT broker, API fetchers)",
    "PP": "Pre-processor - cleans and shapes data (validation, features)",
    "M": "Model - the ML model (XGBoost NO-LAG / LAG chain)",
    "P": "Policy - rules applied to model output (risk thresholds, validity envelope)",
    "D": "Distributor - delivers outputs (API, dashboard, alerts)",
    "SINK": "Sink - the target of the output (district health teams, PNLP)",
    "MLFO": "ML Function Orchestrator - pipeline placement, monitoring, model updates",
    "SANDBOX": "ML sandbox - safe environment to train, validate and test before deployment",
}

READINESS = {
    1: "Data/Model Marketplace", 2: "Generated Content Marketplace",
    3: "Cross-Domain Correlation Analysis", 4: "Contextualization and Regional Impact",
    5: "Level of Integration of AI in Workflows", 6: "Human Interface",
    7: "Strategy Alignment", 8: "Collaboration with AI",
    9: "Impacts of Humans in AI Integration", 10: "AI & Policies",
    11: "AI for Inclusion", 12: "Granular Priorities", 13: "Digital Infrastructure",
}


def conflicts_between(codes: set[str]) -> list[tuple[str, str, str]]:
    return [c for c in CONFLICTS if c[0] in codes and c[1] in codes]
