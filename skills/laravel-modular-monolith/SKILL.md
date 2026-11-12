---
name: laravel-modular-monolith
description: Add nwidart/laravel-modules modules, generate Deptrac boundaries, prove them with a self-test, or assess an existing Laravel app's structure.
license: MIT
metadata:
  author: BothSann
  version: "0.1.0"
---

# Laravel modular monolith

Sets up module structure and boundary checks for apps on `nwidart/laravel-modules`. Never designs business boundaries, invents modules, or moves existing code unasked. Read [structure.md](references/structure.md) before writing module code. Project rule files win, then Laravel Boost's `laravel-best-practices`, then this skill. If Boost isn't installed, stop and ask the owner to install it.

## Setup, once per app
1. `composer require nwidart/laravel-modules`, allow `wikimedia/composer-merge-plugin`, and add `"merge-plugin": {"include": ["Modules/*/composer.json"]}` under `extra` in `composer.json`.
2. `composer require --dev deptrac/deptrac`.
3. Publish the config and set the two generator paths in [structure.md](references/structure.md).
4. Copy [scripts/boundaries.php](scripts/boundaries.php) to `<app>/tools/boundaries.php`, so the gates work without this skill.

## Commands
Run from the app root, or pass `--root <path>` in a monorepo:

| Task | Command |
|---|---|
| Read-only state | `php tools/boundaries.php inspect` |
| New module | `php artisan module:make <Name> --api`, then `composer dump-autoload` |
| Regenerate `deptrac.yaml` after adding a module or editing `boundaries` | `php tools/boundaries.php sync` |
| Prove the rules fail on bad dependencies | `php tools/boundaries.php selftest` |
| Check real code | `vendor/bin/deptrac analyse` |

Add `sync --check`, `deptrac analyse`, and `selftest` to the project's existing gates.

## Steps
1. Run `inspect`. Stop on errors.
2. **New module:** run `module:make`, delete the generated web routes, views, and assets, declare what it uses in `module.json`, then `sync`.
3. **New dependency between modules:** add the module name to `boundaries.uses` and `sync`. Ask the owner first, because each entry is a design decision.
4. **Existing app:** report `inspect` and the `deptrac analyse` violations, grouped by module pair, then suggest one first fix. Change nothing without a request.
5. Verify `sync --check`, `deptrac analyse`, `selftest`, and the project's other gates. All must pass.

## Report
Give the mode, changes, module count, violation count, and self-test count. A passing check proves class dependencies only. It can't see table names in queries, class names in strings, or models reached through another object, so say those weren't checked.

Never edit `deptrac.yaml` by hand, add a baseline or skipped violation, or widen `boundaries` to pass. If a rule seems wrong, explain it and let the owner decide.
