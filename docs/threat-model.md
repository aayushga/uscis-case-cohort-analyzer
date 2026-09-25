# Threat model

## Assets

- USCIS client ID, client secret, and access tokens
- Receipt numbers and raw case-status histories
- Aggregate results that may become identifying when groups are small

## Main risks and controls

| Risk | Initial control |
|---|---|
| Credential committed to Git | Environment-only config; `.env*` ignored except the placeholder example |
| Secret shipped to a browser | Backend/CLI architecture; no client-side API calls |
| Receipt numbers leaked through routine logs | Masked console output; local logs ignored |
| Local research database published | `data/`, SQLite files, and private exports ignored |
| Excessive API traffic | Request-rate throttle, daily configuration ceiling, explicit `--yes` for scans |
| Misleading “cohort” conclusions | Filter by returned form type/date; roadmap calls for longitudinal observations and uncertainty reporting |
| Tiny aggregates reveal individuals | Publish only reviewed aggregates with minimum cell sizes |

## Important limitation

The current daily ceiling is a per-run configuration guard, not yet a durable cross-process quota ledger. Until that roadmap item is implemented, operators must not run overlapping scans and must use the USCIS portal analytics to confirm daily consumption.

