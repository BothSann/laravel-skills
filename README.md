# Laravel skills

[![CI](https://github.com/BothSann/laravel-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/BothSann/laravel-skills/actions/workflows/ci.yml)

Agent skills for building scalable, maintainable Laravel API backends. They target Laravel 13 and PHP 8.3 or later, and cover JSON APIs only: no Blade, Livewire, or Inertia.

The skills add to [Laravel Boost](https://github.com/laravel/boost) and never repeat it. When rules disagree, your project's own rule files win, then Boost, then these skills.

## Skills

| Skill | Use it to |
|---|---|
| `laravel-modular-monolith` | Add `nwidart/laravel-modules` modules and enforce their boundaries with Deptrac |
| `laravel-api-practices` | Write or review API code against 16 small rules that Boost doesn't cover |
| `laravel-learn` | Pick a task, get a proven lesson, and be coached while you type it |
| `laravel-review` | Review a pull request and post the findings as inline GitHub comments |

## Install

```bash
npx skills add BothSann/laravel-skills
```

Node is needed only for this install command and the token benchmark. The skills' scripts are plain PHP with no dependencies.

`laravel-learn` also needs Git, Laravel Boost in the app, and optionally the GitHub CLI, `gh`, which lets the agent see merged PRs. `laravel-review` needs Git and an authenticated `gh`.

## How a lesson works

1. **"What next?"** The agent scans your project, offers up to three tasks, and writes a ticket for the one you pick.
2. **"Write the lesson."** In a separate Git worktree with its own databases, the agent builds the whole solution and proves it. It then writes the guide and copies the tests into your project.
3. **You type.** Each step takes 5–15 minutes and explains What, Why, When, and How, with a command that checks it. You run every Artisan generator and migration yourself.
4. **"Ship it."** You run the gates, commit, and open the PR. After the merge, the agent deletes the lesson's worktree.

| You say | The agent |
|---|---|
| `done` | Checks the step, then gives the next one |
| `check` | Reviews your code without changing it |
| `check and fix` | Reviews, fixes what it found, and shows what changed |
| `you write it: <item>` | Writes that one item and explains it |
| `ship it` | Walks you through proof, gates, commits, and the PR |

Paste an error or ask a question at any time, and you'll get the root cause and the smallest fix.

You type all app code, including models and migrations. The agent writes the Pest tests and, if you turn them on, Scribe attributes and PHPDoc.

PHP ideas go into `learn/php-concepts.md` the first time they appear, in plain words, compared with a language you already know.

## Pull request review

`laravel-review` holds no rules of its own. It reads your project's rule files first, then Boost, then `laravel-api-practices`, and reviews a pull request against them and against what the pull request says it does.

- **P1** is a wrong result, data loss, or a security hole in normal use. **P2** is wrong under a condition that will happen, such as two requests at once, or a criterion with no test. **P3** breaks a written rule, and names it.
- Every finding must be checked against the code and state the concrete failure. Guesses are dropped.
- You see the findings in the terminal first. On your confirmation they're posted as one review of inline comments, each shaped as `**P1 — What to do.** Evidence, consequence, fix.`
- A re-review covers only the commits since the last one and skips findings that already have an open thread. When nothing is left, it posts one "no issues found" comment.

It only ever comments. It never approves, requests changes, resolves threads, or pushes code.

## Module boundaries

`nwidart/laravel-modules` organises code into modules but doesn't stop one module reaching into another. `laravel-modular-monolith` adds that check:

- A module's `Contracts/` and `Events/` namespaces are public. Everything else is private.
- A module declares the modules it depends on in its `module.json`.
- `tools/boundaries.php sync` turns those declarations into a `deptrac.yaml`.
- `tools/boundaries.php selftest` plants a violation for every rule and confirms Deptrac reports each one, so a passing check means something.

Deptrac sees class dependencies only. It can't see table names in queries, class names in strings, or models reached through another object.

## API rules

`laravel-api-practices` holds only what Boost leaves out. Each rule is one small file with an example to avoid, an example to follow, and a link to its official source.

| Category | Rules |
|---|---|
| Responses | API Resources, conditional relations, one error shape, status codes, ISO-8601 dates |
| Lists | Always paginate, cursor pagination for feeds, allow-listed sort and filter |
| Writes | Transactions, idempotency keys, readonly data objects |
| Auth | Sanctum token abilities, expiry, and revocation |
| Contract | Versioned routes and deprecation headers, public IDs |
| Runtime | Strict models, Octane-safe code |

## Token use

Limits are tested in `scripts/check-tokens.mjs`, counted with `o200k_base`.

| Loaded for | Limit | Measured |
|---|---|---|
| A skill's description | 40 | 33 |
| `laravel-modular-monolith` entry | 800 | 692 |
| Writing module code | 1,600 | 1,340 |
| `laravel-api-practices` entry | 600 | 399 |
| A rule file | 350 | 263 at most |
| `done`, before the current step | 1,800 | 1,499 |
| `check` | 2,100 | 1,709 |
| Picking a task | 2,000 | 1,743 |
| Writing a lesson | 3,600 | 3,051 |
| A lesson guide | 4,000 | checked per lesson |
| Reviewing a pull request | 2,200 | 1,988 |

## What's been tested

- The boundary script, against real Deptrac 4.7.2: generated rules, the self-test, and real violating code in a module tree built by the tests.
- Every PHP example in the API rules parses, and every rule's behaviour was checked once by hand in a Laravel 13.42 app with 9 feature tests. The exception is `run-octane-safe`, which follows the Octane docs and was not run under Octane.
- The lesson script: scanning stand-in apps, printing guide steps, and removing worktrees in real Git repos, with `gh` output stubbed. Its scan was also run by hand on a real Laravel 13 app.
- The review script, against a stand-in `gh`: choosing the review range, finding open threads, placing findings inline or in the body, skipping duplicates, and the exact review it would post. Its read-only `context` command was also run on a real pull request.
- By hand on one Windows 11 machine, on a new Laravel 13.42 app with `nwidart/laravel-modules` 13.3 and PHP 8.5: generating modules, syncing, and failing on a cross-module model import.
- This repo's tests, lint, and token budgets, on every push and PR, on Linux and Windows with PHP 8.3.

Not tested: a review posted to a real pull request with `laravel-review`, a full lesson written and taught with `laravel-learn`, an agent using the other skills end to end, an existing app with many modules, or macOS.

## Development

```bash
composer install --working-dir tests/tools
python -m unittest discover -s tests
cd scripts && npm ci && node check-tokens.mjs
```

The tests need `php` on your PATH, or its path in the `PHP` environment variable. For branches, versions, and releases, see [RELEASING.md](RELEASING.md).

## Licence

[MIT](LICENSE)
