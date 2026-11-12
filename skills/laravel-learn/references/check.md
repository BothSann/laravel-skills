# "check" and "check and fix"

## Review
1. Read the owner's changes: `git diff <base>`, plus `git status` for new files.
2. Run read-only checks from boundaries.md. Give write requests to the owner as commands.
3. Compare in order: ticket criteria, project rules, then the rules and checklist below. The reference is a guide, not the only valid answer.
4. Report **Right**, **Breaks**, then **Style**, with file:line and why. Say what you ran and didn't run. Don't fix anything.

A Breaks finding needs a rule, a criterion, or proof you ran. A Style finding without a rule is optional or dropped.

## Check and fix
Fix only what the review found. Report a `File:line | Was | Now | Why` table, then rerun the checks.

## Rules
Load only touched areas. Boost rules are `laravel-best-practices/rules/<name>.md`. API rules are `laravel-api-practices/rules/<name>.md`.

| Work | Boost rules | API rules |
|---|---|---|
| Routes, controllers | routing | contract-route-versions, resp-status-codes |
| Input | validation | list-allow-list-sort-filter, write-dto-input |
| Output | none | resp-api-resources, resp-conditional-relations, resp-iso-dates |
| Lists | db-performance | list-always-paginate, list-cursor-for-feeds |
| Services | architecture | write-transactions |
| Models, queries | eloquent, advanced-queries | run-strict-models |
| Schema | migrations | contract-public-ids |
| Writes that may repeat | architecture | write-idempotency-keys |
| Auth | security | auth-sanctum-tokens |
| Errors | error-handling | resp-error-shape |
| Jobs, events, mail | queue-jobs, events-notifications, mail | run-octane-safe |
| Caching, config | caching, config | none |
| Tests | the `testing-best-practices` skill | none |
| Modules | none | `laravel-modular-monolith`, structure.md |

## Checks that have no rule file

| Area | Check |
|---|---|
| Layers | Controllers hold no queries or business rules. Services don't read the request. |
| Modules | No query on another module's table, and no model reached through another module's object. Deptrac can't see these. |
| Races | Unique constraints settle duplicates, mapped to 409. Counters and one-time tokens update conditionally or under a lock. |
| Jobs | They recheck state before acting, and have a final failure path. |
| Contract | Stable keys and paging. Status codes match the ticket. The Scribe page lists reachable errors. |
| PHP | `==` where `===` is meant, `empty()` on a value that may be `"0"`, missing return types, untyped arrays crossing a class boundary, and vague names. |
