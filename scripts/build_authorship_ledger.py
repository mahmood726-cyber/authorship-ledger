from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
DATA_SOURCE = ROOT / "data-source"
QUEUES_DIR = ROOT / "queues"
EXPORTS_DIR = ROOT / "exports"
SITE_URL = "https://mahmood726-cyber.github.io/authorship-ledger/"
REPO_URL = "https://github.com/mahmood726-cyber/authorship-ledger"
STEWARD = "Tahir Heart Institute"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def workflow_band(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def recommended_license(resource_type: str) -> tuple[str, str]:
    mapping = {
        "Software": ("MIT", "Software-oriented default for public code release."),
        "Model": ("MIT", "Model artifacts in this portfolio usually behave like software."),
        "Dataset": ("CC-BY-4.0", "Dataset-oriented default for shareable research outputs."),
        "Text": ("CC-BY-4.0", "Text-oriented default for manuscripts and educational content."),
        "Project": ("CC-BY-4.0", "Project records default to a content-style recommendation until code scope is clarified."),
        "Other": ("NOASSERTION", "No stable license recommendation available from the current snapshot."),
    }
    return mapping.get(resource_type, mapping["Other"])


def default_credit_roles(resource_type: str) -> list[str]:
    mapping = {
        "Software": ["Conceptualization", "Software", "Methodology", "Validation", "Writing - original draft"],
        "Model": ["Conceptualization", "Software", "Methodology", "Validation", "Writing - original draft"],
        "Dataset": ["Data curation", "Resources", "Methodology", "Validation", "Writing - original draft"],
        "Text": ["Conceptualization", "Investigation", "Writing - original draft", "Writing - review & editing"],
        "Project": ["Conceptualization", "Project administration", "Methodology", "Validation", "Writing - original draft"],
        "Other": ["Conceptualization", "Methodology", "Writing - original draft"],
    }
    return mapping.get(resource_type, mapping["Other"])


def workflow_score(record: dict) -> tuple[int, list[str]]:
    reasons = []
    score = 0
    if record["draftCoreReady"]:
        score += 15
        reasons.append("DataCite draft core available (+15)")
    if record["publishSignal"]:
        score += 10
        reasons.append("Public release signal available (+10)")
    if record["resolvedStatus"] != "Needs triage":
        score += 10
        reasons.append("Lifecycle status resolved (+10)")
    if record["hasPaper"]:
        score += 10
        reasons.append("Paper evidence present (+10)")
    if record["hasProtocol"]:
        score += 5
        reasons.append("Protocol evidence present (+5)")
    if record["citationReadinessScore"] >= 80:
        score += 10
        reasons.append("Citation packet already strong (+10)")
    elif record["citationReadinessScore"] >= 55:
        score += 5
        reasons.append("Citation packet is at least medium-ready (+5)")
    if record["recommendedLicense"] != "NOASSERTION":
        score += 10
        reasons.append("License recommendation generated (+10)")
    if record["orcidTemplateGenerated"]:
        score += 10
        reasons.append("ORCID intake scaffold generated (+10)")
    if record["creditTemplateGenerated"]:
        score += 10
        reasons.append("CRediT scaffold generated (+10)")
    if record["targetJournal"]:
        score += 5
        reasons.append("Target journal preserved (+5)")
    if record["fairTotal"] >= 60:
        score += 5
        reasons.append("Maturity metadata above threshold (+5)")
    return score, reasons


def primary_gap(record: dict) -> str:
    if not record["publishSignal"]:
        return "Add public release signal"
    if record["resolvedStatus"] == "Needs triage":
        return "Resolve lifecycle status"
    if not record["targetJournal"]:
        return "Preserve journal target"
    return "Resolve named creators and ORCID"


def queue_summary(record: dict) -> str:
    return (
        f"{record['name']} has a draft deposit packet and a recommended {record['recommendedLicense']} license, "
        f"but still requires named creators, ORCID identifiers, and confirmed CRediT roles before real DOI registration."
    )


def deposit_state(record: dict) -> str:
    if record["fullyRegistrable"]:
        return "fully-registrable"
    if record["institutionalDraftReady"]:
        return "institutional-draft-ready"
    if record["publishSignal"]:
        return "awaiting-authorship"
    return "awaiting-release"


def make_orcid_request(record: dict) -> dict:
    return {
        "project": record["name"],
        "slug": record["slug"],
        "recordUrl": record["recordUrl"],
        "packetUrl": record["packetUrl"],
        "requestedFields": [
            "full_name",
            "orcid_id",
            "affiliation",
            "email_or_contact_route",
            "contributor_confirmation",
        ],
        "requestText": (
            f"Please confirm the human contributors for {record['name']}, provide ORCID identifiers for each named creator, "
            "and confirm consent for DOI deposit metadata publication."
        ),
    }


def make_credit_template(record: dict) -> dict:
    return {
        "project": record["name"],
        "slug": record["slug"],
        "defaultRoles": record["recommendedCreditRoles"],
        "notes": "Assign named contributors to these roles before DOI registration.",
    }


def make_license_template(record: dict) -> dict:
    return {
        "project": record["name"],
        "slug": record["slug"],
        "recommendedLicense": record["recommendedLicense"],
        "rationale": record["licenseRationale"],
        "currentState": "unresolved",
    }


def make_deposit_draft(record: dict) -> dict:
    return {
        "state": record["depositState"],
        "creators": [
            {
                "name": STEWARD,
                "nameType": "Organizational",
                "status": "fallback-steward",
            }
        ],
        "titles": [{"title": record["name"]}],
        "publisher": STEWARD,
        "publicationYear": str(record["publicationYear"]),
        "types": {
            "resourceTypeGeneral": record["resourceTypeGeneral"],
            "resourceType": record["recordType"],
        },
        "url": record["recordUrl"],
        "version": "draft-authorship-ledger",
        "rightsList": [{"rightsIdentifier": record["recommendedLicense"], "rights": record["recommendedLicense"]}],
        "relatedUrls": {
            "portfolioCatalog": record["recordUrl"],
            "citationPacket": record["packetUrl"],
            "citationCff": record["cffUrl"],
        },
        "unresolvedRequirements": [
            "named human creators",
            "ORCID identifiers",
            "confirmed CRediT roles",
            "asserted final license",
        ],
    }


def queue_page(record: dict) -> str:
    download_links = [
        ("Deposit Draft", f"../exports/deposit/{record['slug']}.json", "Draft DOI registration envelope"),
        ("ORCID Intake", f"../exports/orcid/{record['slug']}.json", "Contributor identifier request template"),
        ("CRediT Roles", f"../exports/credit/{record['slug']}.json", "Contributor role scaffold"),
        ("License", f"../exports/license/{record['slug']}.json", "Recommended SPDX-style license"),
        ("Citation Packet", record["packetUrl"], "Upstream citation packet"),
    ]
    links_html = "".join(
        f"<a class=\"download-link\" href=\"{escape(href)}\"><strong>{escape(title)}</strong><span>{escape(text)}</span></a>"
        for title, href, text in download_links
    )
    facts = [
        ("Workflow readiness", str(record["workflowReadinessScore"])),
        ("Workflow band", record["workflowBand"]),
        ("Deposit state", record["depositState"]),
        ("Institutional draft ready", "Yes" if record["institutionalDraftReady"] else "No"),
        ("Fully registrable", "Yes" if record["fullyRegistrable"] else "No"),
        ("Recommended license", record["recommendedLicense"]),
    ]
    facts_html = "".join(
        f"<article class=\"fact-card\"><span>{escape(label)}</span><strong>{escape(value)}</strong></article>"
        for label, value in facts
    )
    evidence = [
        f"Public release signal: {'Yes' if record['publishSignal'] else 'No'}",
        f"Paper evidence: {'Yes' if record['hasPaper'] else 'No'}",
        f"Protocol evidence: {'Yes' if record['hasProtocol'] else 'No'}",
        f"Resolved lifecycle status: {record['resolvedStatus']}",
        f"Target journal: {record['targetJournal'] or 'Not preserved'}",
        f"Recommended roles: {', '.join(record['recommendedCreditRoles'])}",
    ]
    evidence_html = "".join(f"<li>{escape(item)}</li>" for item in evidence)
    reasons_html = "".join(f"<li>{escape(item)}</li>" for item in record["reasons"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(record['name'])} | AuthorshipLedger</title>
  <meta name="description" content="{escape(record['queueSummary'])}">
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <div class="queue-shell">
    <header class="hero queue-header">
      <div>
        <p class="eyebrow">Deposit Queue</p>
        <h1 class="queue-title">{escape(record['name'])}</h1>
        <p class="hero-text">{escape(record['queueSummary'])}</p>
        <div class="pill-row">
          <span class="pill {escape(record['workflowBand'])}">{escape(record['workflowBand'])} workflow</span>
          <span class="pill">{escape(record['depositState'])}</span>
          <span class="pill">{escape(record['tier'])}</span>
          <span class="pill">{escape(record['recommendedLicense'])}</span>
        </div>
      </div>
      <div class="download-grid">{links_html}</div>
    </header>

    <main class="queue-grid">
      <section class="panel">
        <div class="section-head"><p class="eyebrow">Facts</p><h2>Queue Summary</h2></div>
        <div class="fact-grid">{facts_html}</div>
      </section>

      <section class="panel">
        <div class="section-head"><p class="eyebrow">Evidence</p><h2>Current Signals</h2></div>
        <ul class="fact-list">{evidence_html}</ul>
      </section>

      <section class="panel">
        <div class="section-head"><p class="eyebrow">Reasons</p><h2>Why This Score</h2></div>
        <ul class="fact-list">{reasons_html}</ul>
      </section>

      <section class="panel">
        <div class="section-head"><p class="eyebrow">ORCID Intake</p><h2>Request Template</h2></div>
        <div class="code-panel"><pre>{escape(json.dumps(record['orcidRequest'], indent=2))}</pre></div>
      </section>

      <section class="panel panel-wide">
        <div class="section-head"><p class="eyebrow">Deposit Draft</p><h2>Registration Envelope</h2></div>
        <div class="code-panel"><pre>{escape(json.dumps(record['depositDraft'], indent=2))}</pre></div>
      </section>
    </main>

    <footer class="panel">
      <div class="footer-links">
        <a class="mini-link" href="../index.html"><strong>Back to dashboard</strong><span>Return to AuthorshipLedger.</span></a>
        <a class="mini-link" href="{escape(record['recordUrl'])}"><strong>Portfolio record</strong><span>Canonical public landing page.</span></a>
      </div>
    </footer>
  </div>
</body>
</html>
"""


def main() -> None:
    source = load_json(DATA_SOURCE / "citation-readiness.snapshot.json")
    packet_index = load_json(DATA_SOURCE / "packet-index.snapshot.json")
    packet_map = {item["slug"]: item for item in packet_index["packets"]}

    QUEUES_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in QUEUES_DIR.glob("*.html"):
        old_file.unlink()
    for subdir, pattern in [
        (EXPORTS_DIR / "deposit", "*.json"),
        (EXPORTS_DIR / "orcid", "*.json"),
        (EXPORTS_DIR / "credit", "*.json"),
        (EXPORTS_DIR / "license", "*.json"),
    ]:
        subdir.mkdir(parents=True, exist_ok=True)
        for old_file in subdir.glob(pattern):
            old_file.unlink()

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    records = []
    deposit_manifest = []
    orcid_requests = []
    credit_templates = []
    license_templates = []

    for item in source["projects"]:
        packet = packet_map[item["slug"]]
        recommended_spdx, rationale = recommended_license(item["resourceTypeGeneral"])
        record = {
            "id": item["id"],
            "name": item["name"],
            "slug": item["slug"],
            "tier": item["tier"],
            "recordType": item["recordType"],
            "recordUrl": item["recordUrl"],
            "packetUrl": packet["packetPage"],
            "cffUrl": packet["cff"],
            "resolvedStatus": item["resolvedStatus"],
            "publishSignal": bool(item["publishSignal"]),
            "hasPaper": bool(item["hasPaper"]),
            "hasProtocol": bool(item["hasProtocol"]),
            "targetJournal": item["targetJournal"],
            "publicationYear": int(item["publicationYear"]),
            "resourceTypeGeneral": item["resourceTypeGeneral"],
            "citationReadinessScore": int(item["citationReadinessScore"]),
            "fairTotal": int(item["fairTotal"]),
            "draftCoreReady": True,
            "personCreatorsResolved": False,
            "orcidResolved": False,
            "creditResolved": False,
            "licenseResolved": False,
            "recommendedLicense": recommended_spdx,
            "licenseRationale": rationale,
            "recommendedCreditRoles": default_credit_roles(item["resourceTypeGeneral"]),
            "orcidTemplateGenerated": True,
            "creditTemplateGenerated": True,
        }
        record["institutionalDraftReady"] = (
            record["draftCoreReady"]
            and record["publishSignal"]
            and record["resolvedStatus"] != "Needs triage"
            and record["hasPaper"]
            and record["hasProtocol"]
        )
        record["fullyRegistrable"] = (
            record["institutionalDraftReady"]
            and record["personCreatorsResolved"]
            and record["orcidResolved"]
            and record["creditResolved"]
            and record["licenseResolved"]
        )
        score, reasons = workflow_score(record)
        record["workflowReadinessScore"] = score
        record["workflowBand"] = workflow_band(score)
        record["depositState"] = deposit_state(record)
        record["primaryGap"] = primary_gap(record)
        record["queueSummary"] = queue_summary(record)
        record["reasons"] = reasons
        record["orcidRequest"] = make_orcid_request(record)
        record["creditTemplate"] = make_credit_template(record)
        record["licenseTemplate"] = make_license_template(record)
        record["depositDraft"] = make_deposit_draft(record)

        write_json(ROOT / "exports" / "deposit" / f"{record['slug']}.json", record["depositDraft"])
        write_json(ROOT / "exports" / "orcid" / f"{record['slug']}.json", record["orcidRequest"])
        write_json(ROOT / "exports" / "credit" / f"{record['slug']}.json", record["creditTemplate"])
        write_json(ROOT / "exports" / "license" / f"{record['slug']}.json", record["licenseTemplate"])
        write_text(ROOT / "queues" / f"{record['slug']}.html", queue_page(record))

        deposit_manifest.append(
            {
                "id": record["id"],
                "name": record["name"],
                "slug": record["slug"],
                "depositState": record["depositState"],
                "institutionalDraftReady": record["institutionalDraftReady"],
                "fullyRegistrable": record["fullyRegistrable"],
                "depositDraftUrl": SITE_URL + f"exports/deposit/{record['slug']}.json",
                "queuePageUrl": SITE_URL + f"queues/{record['slug']}.html",
                "recordUrl": record["recordUrl"],
            }
        )
        orcid_requests.append(record["orcidRequest"])
        credit_templates.append(record["creditTemplate"])
        license_templates.append(record["licenseTemplate"])
        record["generatedAt"] = generated_at
        records.append(record)

    records.sort(key=lambda row: (-row["workflowReadinessScore"], row["name"].lower(), row["id"]))
    tracked = len(records)
    high_ready = sum(row["workflowReadinessScore"] >= 80 for row in records)
    medium_or_high = sum(row["workflowReadinessScore"] >= 60 for row in records)
    institutional_ready = sum(row["institutionalDraftReady"] for row in records)
    fully_registrable = sum(row["fullyRegistrable"] for row in records)
    person_resolved = sum(row["personCreatorsResolved"] for row in records)
    orcid_resolved = sum(row["orcidResolved"] for row in records)
    credit_resolved = sum(row["creditResolved"] for row in records)
    license_resolved = sum(row["licenseResolved"] for row in records)

    gap_counter = Counter()
    tier_groups = defaultdict(list)
    for row in records:
        tier_groups[row["tier"]].append(row)
        if not row["personCreatorsResolved"]:
            gap_counter["Needs named human creators"] += 1
        if not row["orcidResolved"]:
            gap_counter["Needs ORCID identifiers"] += 1
        if not row["creditResolved"]:
            gap_counter["Needs CRediT role confirmation"] += 1
        if not row["licenseResolved"]:
            gap_counter["Needs asserted SPDX license"] += 1
        if not row["publishSignal"]:
            gap_counter["Needs public release signal"] += 1
        if not row["targetJournal"]:
            gap_counter["Needs preserved journal target"] += 1

    tiers = []
    for tier, items in tier_groups.items():
        tiers.append(
            {
                "tier": tier,
                "count": len(items),
                "meanScore": round(mean(item["workflowReadinessScore"] for item in items), 1),
                "institutionalDrafts": sum(item["institutionalDraftReady"] for item in items),
            }
        )
    tiers.sort(key=lambda row: (-row["meanScore"], row["tier"]))

    data = {
        "project": {
            "name": "AuthorshipLedger",
            "version": "0.1.0",
            "generatedAt": generated_at,
            "designBasis": [
                "CitationWorkbench packets reused as upstream deposit inputs",
                "ORCID, CRediT, and SPDX-style scaffolds generated per project",
                "Workflow readiness separated from truly registrable deposit state",
            ],
            "links": {
                "repo": REPO_URL,
                "site": SITE_URL,
                "depositManifest": SITE_URL + "deposit-manifest.json",
                "orcidRequests": SITE_URL + "orcid-request-templates.json",
                "creditTemplates": SITE_URL + "credit-role-templates.json",
                "licenseRecommendations": SITE_URL + "license-recommendations.json",
                "e156": SITE_URL + "e156-submission/",
            },
        },
        "metrics": {
            "trackedProjects": tracked,
            "depositDrafts": tracked,
            "orcidTemplates": tracked,
            "creditTemplates": tracked,
            "licenseRecommendations": tracked,
            "highWorkflowReadyCount": high_ready,
            "highWorkflowReadyPercent": round(high_ready / tracked * 100, 1),
            "mediumOrHighCount": medium_or_high,
            "mediumOrHighPercent": round(medium_or_high / tracked * 100, 1),
            "institutionalDraftReadyCount": institutional_ready,
            "institutionalDraftReadyPercent": round(institutional_ready / tracked * 100, 1),
            "fullyRegistrableCount": fully_registrable,
            "fullyRegistrablePercent": round(fully_registrable / tracked * 100, 1),
            "personCreatorResolvedCount": person_resolved,
            "personCreatorResolvedPercent": round(person_resolved / tracked * 100, 1),
            "orcidResolvedCount": orcid_resolved,
            "orcidResolvedPercent": round(orcid_resolved / tracked * 100, 1),
            "creditResolvedCount": credit_resolved,
            "creditResolvedPercent": round(credit_resolved / tracked * 100, 1),
            "licenseResolvedCount": license_resolved,
            "licenseResolvedPercent": round(license_resolved / tracked * 100, 1),
            "meanWorkflowReadiness": round(mean(row["workflowReadinessScore"] for row in records), 1),
        },
        "gapBreakdown": [{"label": key, "count": value} for key, value in gap_counter.most_common()],
        "tiers": tiers,
        "projects": records,
    }

    sitemap_lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
        f"  <url><loc>{SITE_URL}</loc><lastmod>{generated_at}</lastmod></url>",
        f"  <url><loc>{SITE_URL}e156-submission/</loc><lastmod>{generated_at}</lastmod></url>",
        f"  <url><loc>{SITE_URL}e156-submission/assets/dashboard.html</loc><lastmod>{generated_at}</lastmod></url>",
    ]
    for item in records:
        sitemap_lines.append(f"  <url><loc>{SITE_URL}queues/{item['slug']}.html</loc><lastmod>{generated_at}</lastmod></url>")
    sitemap_lines.append("</urlset>")

    write_json(ROOT / "authorship-ledger.json", {"project": "AuthorshipLedger", "generatedAt": generated_at, "overview": data["metrics"], "projects": records})
    write_json(ROOT / "deposit-manifest.json", {"generatedAt": generated_at, "items": deposit_manifest})
    write_json(ROOT / "orcid-request-templates.json", {"generatedAt": generated_at, "items": orcid_requests})
    write_json(ROOT / "credit-role-templates.json", {"generatedAt": generated_at, "items": credit_templates})
    write_json(ROOT / "license-recommendations.json", {"generatedAt": generated_at, "items": license_templates})
    write_json(ROOT / "data.json", data)
    write_text(ROOT / "data.js", "window.AUTHORSHIP_LEDGER_DATA = " + json.dumps(data, indent=2) + ";\n")
    write_text(ROOT / "sitemap.xml", "\n".join(sitemap_lines) + "\n")

    print(
        "Built AuthorshipLedger "
        f"({tracked} deposit drafts, {data['metrics']['highWorkflowReadyPercent']:.1f}% high workflow readiness, "
        f"{data['metrics']['fullyRegistrablePercent']:.1f}% fully registrable)."
    )


if __name__ == "__main__":
    main()
