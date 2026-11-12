---
name: laravel-api-practices
description: Write, review, or refactor Laravel JSON API code using ranked response, list, write, auth, contract, and runtime rules that Laravel Boost doesn't cover.
license: MIT
metadata:
  author: BothSann
  version: "0.1.0"
---

# Laravel API practices

16 rules; read only those relevant to the task. They cover what Laravel Boost's `laravel-best-practices` and `testing-best-practices` leave out, so load those too. Project rule files win, then Boost, then these rules. Earlier categories win conflicts. If Boost isn't installed, say so and carry on.

Each rule is `rules/<prefix><name>.md`, e.g. `rules/list-always-paginate.md`. Do not load the whole directory. The rules target Laravel 13 and JSON APIs only.

| Category / impact | Prefix | Names |
|---|---|---|
| Responses / CRITICAL | resp- | api-resources, conditional-relations, error-shape, status-codes, iso-dates |
| Lists / CRITICAL | list- | always-paginate, cursor-for-feeds, allow-list-sort-filter |
| Writes / HIGH | write- | transactions, idempotency-keys, dto-input |
| Auth / HIGH | auth- | sanctum-tokens |
| Contract / MEDIUM-HIGH | contract- | route-versions, public-ids |
| Runtime / MEDIUM | run- | strict-models, octane-safe |

## When reviewing
Cite the rule name with each finding, and quote the code that breaks it. Report only what the diff or file shows. Don't flag a rule the project's own rule files override.

Leave these to Boost: N+1 queries outside resources, indexes, caching, queues, locks, mass assignment, policies, rate limits, uploads, validation style, and tests.
