# Pick a task

1. Run `php <skill-dir>/scripts/learn.php scan <repo>`, with `--no-gh` if `gh` isn't available. Blockers: `no_config` and `no_boost` need [config.md](config.md). `no_git`: the owner initialises Git. `git_unavailable`: fix access and never recreate the repo. `several_apps`: ask, then set `appRoot`.
2. A lesson marked merged but still in-progress: confirm with the owner and set it to done. Then run `learn.php cleanup <repo>` to remove merged worktrees, and report what it removed.
3. Read the plan and confirm scan results in source. Routes come from `php artisan route:list`; the hints are text heuristics.
4. Offer up to three feasible slices, mark one **next**, and say why. Name the Laravel and PHP ideas each one teaches. Wait for the choice.

## Ranking
The project plan and prerequisites beat scores. An in-progress lesson is always first. An empty repo offers the scaffold only.

| Signal | Score |
|---|---|
| Earliest unfinished plan step | +3 |
| `hint: public write` | +3 |
| `planned, not built`, or `hint: no test names this path` | +2 |
| New Laravel or PHP concept (check `grep "^## " learn/php-concepts.md`) | +2 |
| New package needed | -1 |

Split anything over one endpoint, table, or practice, because lessons allow 6 steps. A new module is its own lesson before its first endpoint. If core PHP hasn't come up in several lessons, such as closures, enums, readonly classes, or interfaces, offer a small practice task that uses it in this app.

Scaffold scope: `laravel new` with Pest and no starter kit, API routes with Sanctum, the database in `.env`, and the gates the owner wants (Pint, Larastan, tests). For a modular app add `nwidart/laravel-modules` and the boundary script through `laravel-modular-monolith`. No feature code.

## After the choice
In-progress: give the current step. Proposed: show decisions, then wait for "write the lesson". New: write only `learn/NN-slug/TICKET.md`:

```markdown
---
id: L-NN
status: proposed
kind: scaffold | module | endpoint | practice
branch: feat/short-name
---
# Ticket L-NN: <small task>

## Story
As <actor>, I want <behavior>, so that <reason>.

## Why now
<Plan step and evidence.>

## Scope
<In and out. One teachable slice.>

## Request and answer
<Real method, path, input, and every status code.>

## Acceptance criteria
1. <Observable outcome with concrete values, including refusals.>
2. <Configured gates pass.>

## Decisions
| Question | Proposal | Why |
|---|---|---|
```

Statuses: proposed, in-progress, done, dropped. End with: "Read the ticket, change decisions if needed, then say **write the lesson**."
