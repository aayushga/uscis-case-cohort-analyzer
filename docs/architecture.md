# Architecture

```text
environment variables
        |
        v
  Settings --------> OAuth token endpoint
        |                     |
        v                     v
 cohort planner -----> USCIS client -----> Case Status API
                             |
                             v
                    local SQLite snapshots
                             |
                             v
                    aggregate summaries
```

The cohort planner is independent from network access. Collection saves the complete source payload locally so parsers can evolve without re-querying USCIS. The public boundary is an aggregate report, not the database.

For an eventual I-765 study, a nearby numeric range is only a discovery frame. Membership is determined after collection using returned `formType` and observed submission dates. Repeated snapshots allow transition-time analysis without treating the current status as a complete history.

