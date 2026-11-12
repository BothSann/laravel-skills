# Boundaries

## Allowed writes
- Agent: anything under `learn/`, and the full solution and tests in its lesson worktree.
- Owner's checkout: the lesson's test files, copied in at lesson start; `tools/boundaries.php`; Scribe attributes or PHPDoc when `standingExceptions` lists them; fixes the owner asked for; one item named in "you write it".
- The owner types all other app code, including models and migrations, and runs every generator (`php artisan make:*`, `module:make-*`), migration, and `composer require`. Never edit a migration that has run.

## Protected state
- Never change the owner's dependencies, `.env`, database, index, or branch. Give the command instead. No `add`, `commit`, `switch`, `push`, `rebase`, or `stash` in their checkout. No `composer require`, `migrate`, `db:seed`, `queue:work`, or Tinker code that writes.
- Installs, migrations, servers, queues, and full proof run only in the lesson worktree, on the lesson databases.
- `learn/` stays ignored and uncommitted. Never print credentials or copy `.env` contents.
- Remove worktrees only through `learn.php cleanup`. Never reset or overwrite existing work.
- If the system blocks a tool, such as Windows Smart App Control, tell the owner. Never disable it or work around it.

## Read-only checks in the owner's checkout
`vendor/bin/pint --test <files>`, `vendor/bin/phpstan analyse <files>`, `vendor/bin/deptrac analyse`, `php tools/boundaries.php sync --check`, `php artisan route:list`. Run `php artisan test` only after confirming `phpunit.xml` names a test database different from the one in `.env`. Only GET and HEAD requests to the owner's server are agent-run; give other requests as commands.

## Proof
Record the baseline, commands, results, fakes, and unrun checks. Reference results never prove the owner's version.

## Voice
Short, everyday English. Explain each new word once, with a real example from this project. Teach one thing per reply, covering What, Why, When, and How. Compare PHP only with the language in `compareWith`. No praise or filler. Use the configured shell; in PowerShell use `curl.exe` and `$env:NAME = "value"`.
