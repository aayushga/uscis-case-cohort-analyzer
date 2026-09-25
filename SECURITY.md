# Security policy

## Reporting

Please report security issues privately to the repository owner. Do not open a public issue containing credentials, access tokens, receipt numbers, or case payloads.

## Secret handling

- Use environment variables locally and an audited secrets manager in deployment.
- Never store USCIS client credentials in browser code, mobile apps, committed files, CI logs, or screenshots.
- Use GitHub Actions secrets if CI ever needs sandbox credentials; prefer tests with fakes.
- Rotate a client secret immediately if it may have been exposed. Rewriting Git history is not a substitute for rotation.

## Data handling

Receipt numbers and case histories can be sensitive. The local database is gitignored, but operators remain responsible for filesystem permissions, backups, retention, access control, and applicable terms or law. Publish only reviewed aggregate outputs with minimum group sizes.

