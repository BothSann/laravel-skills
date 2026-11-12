# Project config

`learn/learn.config.json` holds personal facts. Preserve existing values, and adapt to the project rather than reshaping it.

| Field | Meaning |
|---|---|
| appRoot | Required. App folder from the repo root; `.` or e.g. `apps/api` |
| baseBranch | Required. Shipping target, e.g. `origin/main` |
| shell | Required. `powershell` or `bash` |
| baseUrl | Required. Local API URL with prefix, e.g. `http://127.0.0.1:8000/api/v1` |
| planDoc | Plan with endpoint tables and a "Build order" list |
| gates | Required commands; default below |
| commitStyle | Message convention |
| lessonWorktreesPath | Default: sibling `<repo-name>-lessons` |
| standingExceptions | Any of `scribe`, `phpdoc`; or `[]` |
| compareWith | A language the owner knows, e.g. `TypeScript`; or `null` |

Default gates, run from `appRoot`: `vendor/bin/pint --test`, `vendor/bin/phpstan analyse`, `php tools/boundaries.php sync --check`, `vendor/bin/deptrac analyse`, `php tools/boundaries.php selftest`, `php artisan test`. Use only those the project has set up. If `composer.json` defines scripts that run them, such as `composer check`, use those names.

## First run
Read `learn.php scan` output, `git symbolic-ref refs/remotes/origin/HEAD`, the `composer.json` scripts, and `bootstrap/app.php`. Ask for the rest in one message, with your guesses as defaults. Then:
1. Write the config.
2. Run `git check-ignore learn/`. If it isn't ignored, tell the owner to add `learn/` to `.git/info/exclude`.
3. Scan again.

## Missing Boost
`no_boost` stops everything. The owner runs `composer require --dev laravel/boost` and `php artisan boost:install`, because the lessons take their Laravel rules from Boost.

## Empty repo
With `no_laravel_app`, the first lesson is `kind: scaffold`. With `no_commits`, give the owner the commands for a first commit, because worktrees need one. Default `appRoot` to `apps/api` if a frontend is planned, otherwise `.`.

## No plan
Offer to draft `docs/plan.md` with the owner, or use `idea-to-plan`. The owner owns and commits it. Use full paths:

```markdown
## 1. Account
| Method | Path | Auth | Does |
|---|---|---|---|
| POST | `/api/v1/auth/register` | public | Sign up |

## Build order
1. Account
```
