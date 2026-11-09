"""Policy, standards and responsibility gap analysis.

A gap probe is a question a deployment of AI early warning in health has to be
able to answer from the national framework ("who may issue an alert based on
a model forecast?"). For each probe triggered during a scenario:

1. the national corpus is searched; the best match and its score are kept.
   Below the absence threshold the finding is an *evidenced absence*: the
   concept was not found in any national document of the knowledge base
   (this is a statement about the corpus, reported with the list of documents
   searched, never a claim that no such rule exists anywhere);
2. global, regional and comparator documents are searched for practice
   examples, each admitted only through the verbatim evidence gate;
3. the probe's category, Y.3172 component and AI Readiness dimension are
   attached, so the gap register maps straight onto the ITU frameworks.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from palualert_agents.evidence import Claim, best_evidence, best_quote, quote_overlap, verify
from palualert_agents.kb.retriever import TfidfRetriever
from palualert_agents.settings import settings

CATEGORIES = {
    "legislative": "Legislative gap",
    "standards": "Standards gap",
    "responsibility": "Unclear responsibility",
    "coordination": "Coordination problem",
    "conflict": "Conflict between objectives",
    "technology": "Technology / infrastructure gap",
    "capacity": "Capacity / financing gap",
}

NATIONAL_SCOPES = ["national"]
PRACTICE_SCOPES = ["global", "regional", "comparator", "standard"]


@dataclass(frozen=True)
class Probe:
    id: str
    category: str
    title: str
    national_query: str
    practice_query: str
    recommendation: str
    y3172: tuple[str, ...]
    readiness: tuple[int, ...]
    # Manifest sources that would strengthen this probe but are not ingested yet.
    missing_sources: tuple[str, ...] = ()


PROBES: dict[str, Probe] = {p.id: p for p in [
    Probe("G-ALERT-AUTHORITY", "responsibility",
          "No designated authority to act on model-generated (predicted) epidemic alerts",
          "autorité habilitée à déclarer une alerte épidémique prédiction modèle système d'alerte précoce paludisme responsabilité",
          "accountability for decisions informed by artificial intelligence in health human oversight responsibility",
          "Designate in regulation which body may act on a model-generated alert, at which "
          "confidence, and how the decision and its evidence are recorded.",
          ("P", "D", "SINK"), (7, 10), ('WHO-MALARIA-SURV-2018', 'AE-DOH-AI-POLICY-2018')),
    Probe("G-AUTOMATED-DECISION", "legislative",
          "Automated decisions and profiling in public-health targeting",
          "décision automatisée profilage traitement automatisé données de santé",
          "automated decision-making profiling right not to be subject to a decision based solely on automated processing",
          "Clarify whether district-level targeting driven by a model is an automated decision, "
          "and what human review and explanation it requires.",
          ("P", "M"), (8, 10)),
    Probe("G-AI-HEALTH-REGULATION", "legislative",
          "No sector rule for AI tools used in public-health decision support",
          "intelligence artificielle santé réglementation outil d'aide à la décision homologation",
          "regulation of artificial intelligence systems for health pre-market evaluation risk classification",
          "Adopt a risk-tiered rule for AI decision-support in health, with pre-deployment "
          "evaluation proportionate to impact.",
          ("M", "SANDBOX"), (10,), ('WHO-AI-REG-2023', 'AE-DOH-AI-POLICY-2018')),
    Probe("G-MODEL-VALIDATION", "standards",
          "No standard for validating and monitoring a model before and after deployment",
          "validation du modèle évaluation des performances suivi après déploiement calibration locale",
          "external validation performance monitoring after deployment local calibration dataset shift",
          "Require external validation, a declared validity envelope, local calibration before "
          "new-region use, and post-deployment drift monitoring.",
          ("M", "MLFO", "SANDBOX"), (4, 5, 10), ('WHO-AI-REG-2023',)),
    Probe("G-MODEL-CHANGE", "responsibility",
          "Nobody is mandated to approve a new model version for operational use",
          "approbation mise à jour du modèle version gestion du changement système d'information sanitaire",
          "change management approval of updates to AI systems version control post-market",
          "Assign model-change approval (retrain / recalibrate / roll back) to a named body with "
          "a documented release procedure.",
          ("MLFO",), (5, 9), ('WHO-AI-REG-2023',)),
    Probe("G-SENSOR-STANDARD", "standards",
          "No standard for siting and calibrating environmental sensors used for health decisions",
          "capteur météorologique installation étalonnage norme station météorologique",
          "sensor calibration siting standard environmental monitoring data quality",
          "Reference a siting/calibration standard (e.g. national meteorological service practice) "
          "for any sensor feeding a health model, and certify nodes before use.",
          ("SRC", "PP"), (13,)),
    Probe("G-HEALTH-DATA-TRANSFER", "legislative",
          "Conditions for transferring health data abroad for model training are unclear",
          "transfert de données à caractère personnel vers un pays tiers données de santé autorisation",
          "cross-border transfer of health data adequate level of protection safeguards",
          "Publish implementing rules for cross-border transfers of health data used to train "
          "models, including pseudonymisation and processor obligations.",
          ("C", "SANDBOX"), (1, 10), ('AE-PDPL-2021',)),
    Probe("G-DATA-SHARING", "coordination",
          "No framework for routine data sharing between health, meteorology and telecom actors",
          "partage de données interopérabilité entre ministères météorologie santé système d'information",
          "data sharing agreements interoperability between sectors health climate data",
          "Adopt data-sharing agreements between health, meteorology and network operators, "
          "with a common schema for climate-health data.",
          ("SRC", "C"), (3, 7), ('CM-PSNSN-2020-2024',)),
    Probe("G-INDICATOR-GOVERNANCE", "coordination",
          "Changes to surveillance indicator definitions are not versioned or announced to data users",
          "définition des indicateurs DHIS2 qualité des données changement de définition notification",
          "data standards metadata indicator definitions data quality surveillance",
          "Version every surveillance indicator definition and notify downstream data users "
          "(including models) before a change takes effect.",
          ("SRC", "PP", "MLFO"), (1, 5), ('WHO-MALARIA-SURV-2018',)),
    Probe("G-IHR-PREDICTED", "coordination",
          "Predicted (not yet confirmed) risk has no defined place in IHR notification practice",
          "règlement sanitaire international notification point focal national événement",
          "notification assessment of events that may constitute a public health emergency of international concern",
          "Define how model-predicted cross-border risk is assessed against the IHR decision "
          "instrument before any notification or neighbour information.",
          ("D", "SINK"), (7,), ('WHO-IHR-2005',)),
    Probe("G-IOT-SECURITY", "technology",
          "Security baseline for low-cost IoT health-surveillance networks",
          "sécurité des réseaux objets connectés chiffrement authentification capteurs",
          "security of connected devices encryption authentication IoT",
          "Set a minimum security baseline (authentication, encryption, key management) for "
          "IoT nodes feeding public-health systems.",
          ("SRC", "C"), (13,)),
    Probe("G-SUSTAINABLE-FUNDING", "capacity",
          "Digital surveillance tools depend on external financing",
          "financement gap de financement durabilité système de surveillance",
          "sustainable financing of digital health and surveillance systems",
          "Budget the operation and maintenance of the early-warning system in the national "
          "malaria plan rather than in project funding.",
          ("MLFO",), (13, 7)),
    Probe("G-TRANSPARENCY", "standards",
          "No requirement to publish the validity limits of models used by public bodies",
          "transparence information du public algorithme limites",
          "transparency explainability documentation of AI systems model cards",
          "Require a public transparency note for any model used in public-health decisions, "
          "including where it was shown not to work.",
          ("D",), (6, 10)),
]}


@dataclass
class Gap:
    probe_id: str
    category: str
    category_label: str
    title: str
    status: str                      # absent | weak | addressed
    national_best_score: float
    national_documents_searched: list[str]
    national_evidence: list[dict]
    practice_examples: list[dict]
    recommendation: str
    y3172: list[str]
    readiness: list[str]
    triggered_by: list[dict] = field(default_factory=list)
    national_overlap: float = 0.0
    missing_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def analyse(probe: Probe, kb: TfidfRetriever, triggered_by: list[dict]) -> Gap:
    from palualert_agents.catalog import READINESS

    national_docs = sorted({c["doc_id"] for c in kb.chunks if c["scope"] in NATIONAL_SCOPES})
    hits = kb.search(probe.national_query, k=4, scopes=NATIONAL_SCOPES, min_score=0.0,
                     max_per_doc=2)
    hit, quote, overlap = best_evidence(hits, probe.national_query)
    score = hit.score if hit else 0.0
    # A concept is addressed when a national sentence both ranks well and actually
    # contains most of the probe's terms; otherwise weak or absent.
    if score >= settings.absence_score and overlap >= 0.45:
        status = "addressed"
    elif overlap >= 0.30:
        status = "weak"
    else:
        status = "absent"

    national = []
    if hit is not None:
        claim = Claim(text=("Closest national text" if status == "absent"
                            else "National provision") + f" for: {probe.title}",
                      quote=quote, chunk_id=hit.chunk_id, score=round(score, 4))
        national = [dict(c.to_dict(), overlap=round(overlap, 2))
                    for c in verify([claim], kb).accepted]

    phits = kb.search(probe.practice_query, k=4, scopes=PRACTICE_SCOPES, max_per_doc=1,
                      min_score=0.04)
    claims = []
    for h in phits:
        q = best_quote(h, probe.practice_query)
        if quote_overlap(q, probe.practice_query) >= 0.3:
            claims.append(Claim(text=f"Practice example for: {probe.title}", quote=q,
                                chunk_id=h.chunk_id, score=round(h.score, 4)))
    practice = [c.to_dict() for c in verify(claims[:3], kb).accepted]

    return Gap(probe.id, probe.category, CATEGORIES[probe.category], probe.title, status,
               round(score, 4), national_docs, national, practice, probe.recommendation,
               list(probe.y3172), [f"D{d} {READINESS[d]}" for d in probe.readiness],
               triggered_by, round(overlap, 2), probe.missing_sources)
