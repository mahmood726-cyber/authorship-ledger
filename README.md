# AuthorshipLedger

AuthorshipLedger is a standalone DOI-deposit and contributor-resolution layer for the C-drive research portfolio.

## Why this exists

The portfolio now has public landing pages and citation packets, but it still lacks the missing governance layer that blocks real DOI registration: named creators, ORCID collection, CRediT roles, and asserted SPDX-style licenses.

## What it does

- reuses bundled `CitationWorkbench` records and packet links
- distinguishes draft-ready deposits from fully registrable deposits
- generates deposit drafts, ORCID intake templates, CRediT role templates, and license recommendations
- scores authorship and governance workflow readiness
- ships a static GitHub Pages dashboard and E156 bundle

## Outputs

- `authorship-ledger.json` - scored governance and authorship-resolution model
- `deposit-manifest.json` - aggregated DOI-deposit queue
- `orcid-request-templates.json` - ORCID collection scaffolds
- `credit-role-templates.json` - CRediT role templates
- `license-recommendations.json` - SPDX-style recommendations
- `exports/` - generated deposit, ORCID, CRediT, and license JSON files
- `queues/` - generated queue pages
- `data.json` and `data.js` - dashboard payloads
- `CITATION.cff` - citation file for AuthorshipLedger itself
- `e156-submission/` - paper, protocol, metadata, and reader page

## Rebuild

Run:

`python C:\Users\user\AuthorshipLedger\scripts\build_authorship_ledger.py`

## Scope note

This project builds resolution scaffolds and deposit queues. It does not verify legal authorship, register DOIs, or replace project-specific contributor consent.
