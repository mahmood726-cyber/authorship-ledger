Mahmood Ahmad
Tahir Heart Institute
author@example.com

Protocol: AuthorshipLedger - Deposit Queue and Contributor Resolution Audit

This protocol describes a snapshot-first governance study over bundled `CitationWorkbench` records and packet links for 134 indexed projects. The primary estimand is the proportion of indexed projects reaching full DOI-registrable state, defined as projects with institutional draft readiness plus named human creators, ORCID identifiers, confirmed CRediT roles, and asserted final licenses. Secondary outputs will report institutional draft readiness, workflow readiness, ORCID gaps, contributor-role gaps, license gaps, journal-target preservation, deposit-state counts, and tier summaries. The build process will emit `authorship-ledger.json`, `deposit-manifest.json`, `orcid-request-templates.json`, `credit-role-templates.json`, `license-recommendations.json`, `exports/`, `queues/`, `data.json`, and `data.js`. Generated artifacts will include per-project deposit drafts, ORCID request templates, CRediT templates, and SPDX-style recommendations. Anticipated limitations include institutional fallback creators, heuristic role defaults, recommended rather than asserted licenses, absent contributor consent, and the fact that this queue does not itself register or reserve DOI names.

Outside Notes

Type: protocol
Primary estimand: proportion of indexed projects reaching full DOI-registrable state
App: AuthorshipLedger v0.1
Code: repository root, scripts/build_authorship_ledger.py, exports/, deposit-manifest.json, and data-source/
Date: 2026-03-30
Validation: DRAFT

References

1. DataCite. DataCite Metadata Schema Documentation. Accessed 2026-03-30.
2. NISO. Contributor Roles Taxonomy (CRediT). Accessed 2026-03-30.
3. ORCID. About ORCID and ORCID identifiers. Accessed 2026-03-30.
4. SPDX Workgroup. SPDX License List. Accessed 2026-03-30.

AI Disclosure

This protocol was drafted from versioned local artifacts and deterministic build logic. AI was used as a drafting and implementation assistant under author supervision, with the author retaining responsibility for scope, methods, and reporting choices.
