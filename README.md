# USCIS Case Cohort Analyzer

A small, privacy-conscious Python toolkit for the official USCIS Case Status API. The first milestone exercises the USCIS sandbox correctly; the design then supports longitudinal, aggregate analysis of nearby I-765 receipt numbers once USCIS grants production access.

> **Alpha / research use only.** This is not affiliated with USCIS, does not provide legal advice, and must not be used to make decisions about another person. Receipt sequences are not guaranteed to be homogeneous cohorts: nearby numbers can cover different form types, filing channels, and dates.

## What works now

- OAuth 2.0 client-credentials authentication with in-memory token caching
- Official sandbox endpoint and published staging receipt numbers
- A hard sandbox ceiling of 1,000 requests/day and 5 requests/second
- Structured handling of USCIS 4xx/5xx error messages
- Offline preview of a bounded cohort around a receipt number
- Local SQLite snapshots and aggregate I-765 status summaries
- Masked receipt numbers in normal console output
- Zero runtime dependencies (Python 3.11+)

Raw receipt numbers and API payloads are kept in `data/`, which Git ignores. Aggregate results can eventually be published after a privacy review; raw data should not be committed.

## USCIS sandbox requirements

As documented by USCIS (verified September 25, 2026):

1. Create a [USCIS developer account](https://developer.uscis.gov/node/143), a Developer Team, and a Team App.
2. Enable **Case Status API - Sandbox** for that app.
3. Store its Client ID and Client Secret only in environment variables or a secrets manager. The secret must never reach client-side code, logs, or Git.
4. Authenticate with OAuth 2.0 client credentials at `https://api-int.uscis.gov/oauth/accesstoken`. Access tokens last about 30 minutes.
5. Call the sandbox resource at `https://api-int.uscis.gov/case-status/{receiptNumber}`. Only USCIS's published staging receipts work there.
6. Stay within [sandbox limits](https://developer.uscis.gov/node/144): 1,000 Case Status requests/day and 5 transactions/second.
7. Before requesting production access, generate sandbox traffic for at least five consecutive calendar days and demonstrate both successful (`200`) and error (`4xx`) responses. Then contact `developersupport@uscis.dhs.gov`.

Production URLs and credentials are supplied only after USCIS approval. The application deliberately refuses `USCIS_ENVIRONMENT=production` unless both production URLs are explicitly configured.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

export USCIS_CLIENT_ID='your-client-id'
export USCIS_CLIENT_SECRET='your-client-secret'

uscis-cohort sandbox-plan
uscis-cohort check EAC9999103402
```

Do not paste credentials into an issue, command transcript, source file, or screenshot. If a credential is ever exposed, rotate it in the USCIS developer portal.

## Plan an eventual I-765 cohort

Previewing does not call USCIS:

```bash
uscis-cohort plan-cohort --center IOE1234567890 --before 50 --after 50
```

After production approval and configuration, a bounded scan is explicit and requires confirmation:

```bash
export USCIS_ENVIRONMENT=production
export USCIS_BASE_URL='the production resource URL USCIS provides'
export USCIS_TOKEN_URL='the production token URL USCIS provides'

uscis-cohort scan --center IOE1234567890 --before 50 --after 50 --yes
uscis-cohort summary --form I-765
```

The scanner records all returned form types so the analysis can select I-765 cases after collection rather than assuming every nearby receipt is an I-765.

## Analysis roadmap

- Record repeated snapshots to measure status transitions and elapsed time
- Normalize USCIS status text into documented lifecycle categories
- Define cohorts by observed submission date and form type, not proximity alone
- Produce aggregate survival curves and percentile estimates with minimum cell sizes
- Add resumable scans, bounded retries for `429`/`5xx`, and a durable daily quota ledger
- Export de-identified aggregate CSV/JSON reports

## Development

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m uscis_cohort sandbox-plan
PYTHONPATH=src python -m uscis_cohort plan-cohort \
  --center IOE1234567890 --before 2 --after 2
```

The tests use fake HTTP responses and never need credentials or network access.

## Security and responsible use

- `.env`, databases, private exports, and logs are ignored by Git.
- Credentials are loaded from environment variables and are never persisted.
- Access tokens exist only in process memory.
- Normal command output masks receipt numbers.
- `--show-raw` is intentionally opt-in and may expose a full receipt number.
- Keep collection proportionate, obey USCIS terms and limits, and publish aggregates rather than case-level histories.

See [`docs/threat-model.md`](docs/threat-model.md) and [`SECURITY.md`](SECURITY.md) before deploying or sharing data.

## License

MIT

