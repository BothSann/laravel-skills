# How to review

Read the whole diff once for what it is trying to do. Then go through it again in this order, because the early items cost the most when missed.

## 1. Does it do what was asked
Match each acceptance criterion to the code that meets it and the test that proves it. A criterion with no code is a P1. A criterion with no test, or a test that can't fail, is a P2.

## 2. Does it stay correct when things go wrong
Trace each write from the route to the database.

| Look for | Typical defect |
|---|---|
| Several writes | No transaction, or a slow outside call inside one |
| Check, then write | Two requests pass the check together; needs a unique index, a conditional update, or a lock |
| Return values | A call that reports failure by returning `false` or `null`, and the result is ignored |
| Queued work | A listener, job, mail, or notification assumed to have run already, or dispatched before the commit |
| Retries | A job or request that runs twice and does the work twice |
| Stale models | A model loaded earlier, used for a decision after another process may have changed the row |
| Deletes | Files, cache entries, tokens, or rows in other tables left behind |
| Authorization | A route with no policy check, or one that checks the wrong record |
| Input | A field used without validation, or a client-chosen column, sort, or page size |
| Output | A model returned without a resource, or a relation loaded once per row |
| Migrations | A change that locks a large table, or can't run while the old code is live |

## 3. Does it follow the rules
Load only the rule files for what the diff touches. Boost rules are `laravel-best-practices/rules/<name>.md`. API rules are `laravel-api-practices/rules/<name>.md`.

| Diff touches | Boost rules | API rules |
|---|---|---|
| Routes, controllers | routing | contract-route-versions, resp-status-codes |
| Requests | validation | list-allow-list-sort-filter, write-dto-input |
| Resources | none | resp-api-resources, resp-conditional-relations, resp-iso-dates |
| List endpoints | db-performance | list-always-paginate, list-cursor-for-feeds |
| Services | architecture | write-transactions, write-idempotency-keys |
| Models, queries | eloquent, advanced-queries | run-strict-models |
| Migrations | migrations | contract-public-ids |
| Auth | security | auth-sanctum-tokens |
| Exceptions | error-handling | resp-error-shape |
| Jobs, events, mail | queue-jobs, events-notifications, mail | run-octane-safe |
| Cache, config | caching, config | none |
| Tests | the `testing-best-practices` skill | none |
| Modules | none | `laravel-modular-monolith`, structure.md |

For modules, run `vendor/bin/deptrac analyse` if the project has it, and also check what it can't see: a query on another module's table, and a model reached through another module's object.

## Before you write a finding
- Read the code on both sides of the line: the caller, and what it calls.
- Check the project's config when the behavior depends on it, such as the queue connection or a disk's `throw` option.
- Look for an existing test or sibling class that shows the project already does it this way on purpose. Consistency with the codebase beats a lower rule source.
