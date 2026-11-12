# Laravel skills

[![CI](https://github.com/BothSann/laravel-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/BothSann/laravel-skills/actions/workflows/ci.yml)

Agent skills for building scalable, maintainable Laravel API backends. They target Laravel 13 and PHP 8.3 or later, and cover JSON APIs only: no Blade, Livewire, or Inertia.

The skills add to [Laravel Boost](https://github.com/laravel/boost) and never repeat it. When rules disagree, your project's own rule files win, then Boost, then these skills.

## Skills

| Skill | Use it to | Status |
|---|---|---|
| `laravel-modular-monolith` | Add `nwidart/laravel-modules` modules and enforce their boundaries with Deptrac | Available |
| `laravel-api-practices` | Write or review API code against 16 small rules that Boost doesn't cover | Available |
| `laravel-learn` | Learn Laravel and PHP by typing a real app, one coached step at a time | Planned |
| `laravel-review` | Review a pull request and post findings as inline comments | Planned |

## Install

```bash
npx skills add BothSann/laravel-skills
```

Node is needed only for this install command and the token benchmark. The skills' scripts are plain PHP with no dependencies.

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

## What's been tested

- The boundary script, against real Deptrac 4.7.2: generated rules, the self-test, and real violating code in a module tree built by the tests.
- Every PHP example in the API rules parses, and every rule's behaviour was checked once by hand in a Laravel 13.42 app with 9 feature tests. The exception is `run-octane-safe`, which follows the Octane docs and was not run under Octane.
- By hand on one Windows 11 machine, on a new Laravel 13.42 app with `nwidart/laravel-modules` 13.3 and PHP 8.5: generating modules, syncing, and failing on a cross-module model import.
- This repo's tests, lint, and token budgets, on every push and PR, on Linux and Windows with PHP 8.3.

Not tested: an agent using the skill end to end, an existing app with many modules, or macOS.

## Development

```bash
composer install --working-dir tests/tools
python -m unittest discover -s tests
cd scripts && npm ci && node check-tokens.mjs
```

The tests need `php` on your PATH, or its path in the `PHP` environment variable. For branches, versions, and releases, see [RELEASING.md](RELEASING.md).

## Licence

[MIT](LICENSE)
