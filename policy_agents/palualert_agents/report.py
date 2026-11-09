"""Human-readable outputs of a run: transcript.md and a self-contained report.html."""
from __future__ import annotations

import html
from pathlib import Path

from palualert_agents.catalog import INSTITUTIONS, Y3172

STATUS_LABEL = {"absent": "Not found in national corpus", "weak": "Weakly addressed",
                "addressed": "Addressed"}


def _q(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


# ── markdown ─────────────────────────────────────────────────────────────────
def transcript_md(r: dict) -> str:
    sc, ev = r["scenario"], r["evaluation"]
    out = [f"# {sc['title']}", "",
           f"Run `{r['run_id']}` · model backend `{r['llm']['backend']}`"
           + (f" ({r['llm']['model']})" if r['llm'].get('model') else "")
           + f" · PaluAlert `{r.get('mews')}`", "", sc.get("summary", "").strip(), ""]
    for st in r["steps"]:
        out += [f"## Step {st['step']}: {st['title']}", "", "**Released**", "",
                "| Event | To | Content |", "|---|---|---|"]
        out += [f"| {e['event']} | {', '.join(e['to'])} | {_q(e['text'])} |" for e in st["released"]]
        out.append("")
        for aid, a in st["assessments"].items():
            if not a["new_events"] and not a["actions"]:
                continue
            out += [f"### {INSTITUTIONS.get(aid, aid)}", "", a["summary"], ""]
            for t in a["tool_results"]:
                if "rows" in t:
                    out += [f"Tool `{t['tool']}` on {t['district']} {t['period']} "
                            f"({t['mews']}):", "",
                            "| Input | T °C | RH % | Cases | /1000 | Risk | vs ref |",
                            "|---|---|---|---|---|---|---|"]
                    out += [f"| {x['variant']} | {x['temperature_c']} | {x['humidity_pct']} | "
                            f"{x['predicted_cases']} | {x['incidence_per_1000']} | "
                            f"{x['risk_level']} | {x['vs_reference_pct']:+.1f}% |"
                            for x in t["rows"]]
                    out.append("")
                elif "months" in t:
                    out += [f"Tool `{t['tool']}` on {t['district']} ({t['region']}):", "",
                            "| Month | Model | Cases | /1000 | Risk | Threshold |",
                            "|---|---|---|---|---|---|"]
                    out += [f"| {m['year']}-{m['month']:02d} | {m['model_used']} | "
                            f"{m['predicted_cases']} | {m['predicted_incidence']} | "
                            f"{m['risk_level']} | {m['threshold']} |" for m in t["months"]]
                    out.append("")
                elif "error" in t:
                    out += [f"Tool `{t['tool']}` failed: {t['error']}", ""]
            if a["actions"]:
                out.append("**Proposed actions**")
                for x in a["actions"]:
                    refs = ", ".join(f"[{i + 1}]" for i in x["claim_ids"])
                    out.append(f"- `{x['code']}`{' ⚠ human decision' if x['high_impact'] else ''}"
                               f": {x['rationale']} {refs}")
                out.append("")
            if a["claims"]:
                out.append("**Evidence (admitted by the verbatim gate)**")
                for i, c in enumerate(a["claims"], 1):
                    out.append(f"{i}. {c['citation']}: “{c['quote']}”")
                out.append("")
            if a["rejected_claims"]:
                out += [f"*{len(a['rejected_claims'])} claim(s) rejected by the gate.*", ""]
            if a.get("llm"):
                m = a["llm"]
                out += [f"*Model `{m.get('model')}`: {m.get('assessment') or m.get('error', '')}*", ""]
            out += ["<details><summary>Reasoning trace</summary>", ""]
            out += [f"- {t}" for t in a["trace"]]
            out += ["", "</details>", ""]
        if st["messages"]:
            out += ["**Consultation**", ""]
            for m in st["messages"]:
                q, rep = m["request"], m["reply"]
                out += [f"- **{q['from']} → {q['to']}:** {q['question']}",
                        f"  - *{rep['from']}:* {rep['answer']}"]
            out.append("")
        co = st["coordination"]
        out += ["**Coordination**", ""]
        for c in co["conflicts"]:
            out.append(f"- Conflict `{c['between'][0]}` vs `{c['between'][1]}` ({c['issue']}): "
                       f"{c['resolution']}")
        for o in co["ownership"]:
            out.append(f"- `{o['action']}`: {o['issue']} (proposed by {', '.join(o['proposed_by'])})")
        for d in co["decisions"]:
            out.append(f"- Human decision on `{d['action']}`: **{d['decision']}**; {d['note']}")
        if not (co["conflicts"] or co["ownership"] or co["decisions"]):
            out.append("- nothing to coordinate")
        out.append("")

    out += ["## Gap register", "",
            "| Gap | Category | National status | Practice examples | Y.3172 | AI Readiness |",
            "|---|---|---|---|---|---|"]
    for g in r["gaps"]:
        out.append(f"| {g['title']} | {g['category_label']} | {STATUS_LABEL[g['status']]} "
                   f"(score {g['national_best_score']}) | {len(g['practice_examples'])} | "
                   f"{' '.join(g['y3172'])} | {'; '.join(g['readiness'])} |")
    out.append("")
    for g in r["gaps"]:
        out += [f"### {g['probe_id']}: {g['title']}", "",
                f"*{g['category_label']} · {STATUS_LABEL[g['status']]}* · searched "
                f"{len(g['national_documents_searched'])} national documents · raised by "
                + ", ".join(sorted({f"{t['agent']} (step {t['step']})" for t in g['triggered_by']})),
                ""]
        for e in g["national_evidence"]:
            out.append(f"- National: {e['citation']}: “{e['quote']}”")
        for e in g["practice_examples"]:
            out.append(f"- Practice: {e['citation']}: “{e['quote']}”")
        if g["missing_sources"]:
            out.append(f"- Not yet in the knowledge base, would strengthen this finding: "
                       f"{', '.join(g['missing_sources'])}")
        out += [f"- **Recommendation:** {g['recommendation']}", ""]

    out += ["## Expected vs actual", "",
            f"- Expected actions found: {ev['expected_actions_found']} "
            f"(recall {ev['action_recall']})",
            f"- Expected actions missed: {ev['expected_actions_missed']}",
            f"- Expected gaps found: {ev['expected_gaps_found']} (recall {ev['gap_recall']})",
            f"- Expected gaps missed: {ev['expected_gaps_missed']}",
            f"- Conflicts detected: {ev['conflicts']} · human decisions: {ev['human_decisions']}"
            f" · claims admitted/rejected: {ev['claims_admitted']}/{ev['claims_rejected']}", ""]
    return "\n".join(out)


# ── html ─────────────────────────────────────────────────────────────────────
CSS = """
body{font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif;margin:0;color:#1d2433;background:#f6f7f9}
main{max-width:1100px;margin:auto;padding:24px}
h1{font-size:24px;margin:0 0 4px} h2{font-size:19px;margin:32px 0 8px;border-bottom:2px solid #d9dee7;padding-bottom:4px}
h3{font-size:16px;margin:18px 0 6px} .meta{color:#5b6475;font-size:13px}
.card{background:#fff;border:1px solid #dde2ea;border-radius:8px;padding:12px 16px;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0}
th,td{border:1px solid #dde2ea;padding:4px 8px;text-align:left;vertical-align:top} th{background:#eef1f5}
.tag{display:inline-block;font-size:12px;padding:1px 7px;border-radius:10px;background:#eef1f5;margin-right:4px}
.hi{background:#fde8e8;color:#9b1c1c} .ok{background:#e3f5e8;color:#1e6b34} .weak{background:#fff4d6;color:#8a5a00}
.absent{background:#fde8e8;color:#9b1c1c} .addressed{background:#e3f5e8;color:#1e6b34}
blockquote{margin:4px 0 4px 0;padding:4px 10px;border-left:3px solid #9fb3d1;background:#f7f9fc;font-size:13px}
.cite{font-size:12px;color:#44506a} details{font-size:13px;color:#44506a}
.kpi{display:inline-block;margin-right:18px} .kpi b{font-size:20px;display:block}
"""


def _e(s) -> str:
    return html.escape(str(s))


def report_html(r: dict) -> str:
    sc, ev = r["scenario"], r["evaluation"]
    h = [f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><title>{_e(sc['title'])}"
         f"</title><style>{CSS}</style></head><body><main>",
         f"<h1>{_e(sc['title'])}</h1><div class='meta'>Run {_e(r['run_id'])} · backend "
         f"{_e(r['llm']['backend'])} {_e(r['llm'].get('model', ''))} · PaluAlert {_e(r.get('mews'))}</div>",
         f"<p>{_e(sc.get('summary', ''))}</p>",
         "<div class='card'>"
         + "".join(f"<span class='kpi'><b>{_e(v)}</b>{_e(k)}</span>" for k, v in [
             ("steps", len(r["steps"])), ("claims admitted", ev["claims_admitted"]),
             ("claims rejected", ev["claims_rejected"]), ("conflicts", ev["conflicts"]),
             ("human decisions", ev["human_decisions"]), ("gaps", len(r["gaps"])),
             ("action recall", ev["action_recall"]), ("gap recall", ev["gap_recall"])])
         + "</div>"]
    for st in r["steps"]:
        h.append(f"<h2>Step {st['step']}: {_e(st['title'])}</h2><table><tr><th>Event</th>"
                 "<th>Released to</th><th>Content</th></tr>")
        h += [f"<tr><td>{_e(e['event'])}</td><td>{_e(', '.join(e['to']))}</td>"
              f"<td>{_e(e['text'])}</td></tr>" for e in st["released"]]
        h.append("</table>")
        for aid, a in st["assessments"].items():
            if not a["new_events"] and not a["actions"]:
                continue
            h.append(f"<div class='card'><h3>{_e(INSTITUTIONS.get(aid, aid))}</h3>"
                     f"<p>{_e(a['summary'])}</p>")
            for t in a["tool_results"]:
                if "rows" in t:
                    h.append(f"<div class='cite'>palualert_app {_e(t['tool'])} · {_e(t['district'])} "
                             f"{_e(t['period'])}</div><table><tr><th>Input</th><th>T °C</th>"
                             "<th>RH %</th><th>Cases</th><th>/1000</th><th>Risk</th><th>vs ref</th></tr>")
                    h += [f"<tr><td>{_e(x['variant'])}</td><td>{x['temperature_c']}</td>"
                          f"<td>{x['humidity_pct']}</td><td>{x['predicted_cases']}</td>"
                          f"<td>{x['incidence_per_1000']}</td><td>{x['risk_level']}</td>"
                          f"<td>{x['vs_reference_pct']:+.1f}%</td></tr>" for x in t["rows"]]
                    h.append("</table>")
                elif "months" in t:
                    h.append(f"<div class='cite'>palualert_app {_e(t['tool'])} · {_e(t['district'])} "
                             f"({_e(t['region'])})</div><table><tr><th>Month</th><th>Model</th>"
                             "<th>Cases</th><th>/1000</th><th>Risk</th><th>Threshold</th></tr>")
                    h += [f"<tr><td>{m['year']}-{m['month']:02d}</td><td>{m['model_used']}</td>"
                          f"<td>{m['predicted_cases']}</td><td>{m['predicted_incidence']}</td>"
                          f"<td>{m['risk_level']}</td><td>{m['threshold']}</td></tr>"
                          for m in t["months"]]
                    h.append("</table>")
            if a["actions"]:
                h.append("<ul>")
                for x in a["actions"]:
                    tag = "<span class='tag hi'>human decision</span>" if x["high_impact"] else ""
                    refs = " ".join(f"[{i + 1}]" for i in x["claim_ids"])
                    h.append(f"<li><code>{_e(x['code'])}</code> {tag} {_e(x['rationale'])} "
                             f"<span class='cite'>{refs}</span></li>")
                h.append("</ul>")
            for i, c in enumerate(a["claims"], 1):
                h.append(f"<blockquote>[{i}] “{_e(c['quote'])}”<div class='cite'>"
                         f"{_e(c['citation'])}</div></blockquote>")
            if a["rejected_claims"]:
                h.append(f"<p class='cite'>{len(a['rejected_claims'])} claim(s) rejected by "
                         "the verbatim gate (see audit log).</p>")
            h.append("<details><summary>Reasoning trace</summary><ul>"
                     + "".join(f"<li>{_e(t)}</li>" for t in a["trace"]) + "</ul></details></div>")
        if st["messages"]:
            h.append("<h3>Consultation</h3>")
            for m in st["messages"]:
                q, rep = m["request"], m["reply"]
                cls = "ok" if rep["found"] else "hi"
                h.append(f"<div class='card'><b>{_e(q['from'])} → {_e(q['to'])}</b>: "
                         f"{_e(q['question'])}<br><span class='tag {cls}'>"
                         f"{'answered from KB' if rep['found'] else 'no provision found'}</span>"
                         f" {_e(rep['answer'])}</div>")
        co = st["coordination"]
        items = [f"<li><span class='tag hi'>conflict</span> <code>{_e(c['between'][0])}</code> vs "
                 f"<code>{_e(c['between'][1])}</code> ({_e(c['issue'])}): {_e(c['resolution'])}</li>"
                 for c in co["conflicts"]]
        items += [f"<li><span class='tag weak'>mandate</span> <code>{_e(o['action'])}</code>: "
                  f"{_e(o['issue'])}</li>" for o in co["ownership"]]
        items += [f"<li><span class='tag {'ok' if d['decision'] == 'approve' else 'hi'}'>"
                  f"human: {_e(d['decision'])}</span> <code>{_e(d['action'])}</code>: "
                  f"{_e(d['note'])}</li>" for d in co["decisions"]]
        h.append("<h3>Coordination</h3><ul>" + ("".join(items) or "<li>nothing to coordinate</li>")
                 + "</ul>")

    h.append("<h2>Gap register</h2>")
    for g in r["gaps"]:
        h.append(f"<div class='card'><h3>{_e(g['title'])}</h3><span class='tag'>"
                 f"{_e(g['category_label'])}</span><span class='tag {g['status']}'>"
                 f"{_e(STATUS_LABEL[g['status']])}</span>"
                 + "".join(f"<span class='tag' title='{_e(Y3172.get(y, y))}'>Y.3172 {_e(y)}</span>"
                           for y in g["y3172"])
                 + "".join(f"<span class='tag'>{_e(d)}</span>" for d in g["readiness"])
                 + f"<p class='cite'>{len(g['national_documents_searched'])} national documents "
                   f"searched · best score {g['national_best_score']}</p>")
        for e in g["national_evidence"]:
            h.append(f"<blockquote><b>National</b> “{_e(e['quote'])}”<div class='cite'>"
                     f"{_e(e['citation'])}</div></blockquote>")
        for e in g["practice_examples"]:
            h.append(f"<blockquote><b>Practice</b> “{_e(e['quote'])}”<div class='cite'>"
                     f"{_e(e['citation'])}</div></blockquote>")
        if g["missing_sources"]:
            h.append(f"<p class='cite'>Would be strengthened by sources not yet ingested: "
                     f"{_e(', '.join(g['missing_sources']))}</p>")
        h.append(f"<p><b>Recommendation.</b> {_e(g['recommendation'])}</p></div>")

    h.append("<h2>Expected vs actual</h2><table>" + "".join(
        f"<tr><th>{_e(k)}</th><td>{_e(v)}</td></tr>" for k, v in ev.items()) + "</table>")
    h.append("</main></body></html>")
    return "".join(h)


def write_reports(result: dict, out: Path) -> None:
    (out / "transcript.md").write_text(transcript_md(result), encoding="utf-8")
    (out / "report.html").write_text(report_html(result), encoding="utf-8")
