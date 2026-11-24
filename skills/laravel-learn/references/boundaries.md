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
Short, everyday English. In guides, cards, notes and replies, use the most common word that fits, not an advanced one: "use", not "utilize"; "gets from", not "inherits"; "stays the same", not "persists". A technical term the lesson teaches stays. Explain each new word once, with a real example from this project. Teach one idea per reply. A reply about code uses the step shape in [templates.md](templates.md): an opener, a walkthrough of each line (what it does, then why), and an "In short" line. A plain concept question gets an opener, a few short plain sentences, and "In short". No praise or filler. Use the configured shell; in PowerShell use `curl.exe` and `$env:NAME = "value"`.
