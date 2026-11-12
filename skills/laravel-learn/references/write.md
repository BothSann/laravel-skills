# Write a proven lesson

Build the complete solution in a separate worktree, then write docs from what was tested. Keep the project's stack and layout. Read [config.md](config.md) for gates.

## 1. Prepare
1. Read the ticket. Expect status proposed. Confirm open decisions, keeping answers already given.
2. Read project rules, sibling code in the layers you'll touch, and the rules mapped in [check.md](check.md). For version-sensitive APIs use Boost's `search-docs` tool or the installed package source. Report a missing source once.
3. Record `git status --short` and `git rev-parse HEAD`. Copy only needed uncommitted changes into the worktree, never `.env` or `vendor`. If a change is unclear, ask.

## 2. Worktree
Use `<lessonWorktreesPath>/NN-slug`, resolved and confirmed outside the repo:

```text
git worktree add --detach <path> <starting-commit>
```

If the folder exists, reuse it only if it belongs to this lesson and baseline. In `<path>/<appRoot>`, run `composer install`. A scaffold has no lock file yet, so run the same `laravel new` and `composer require` commands the guide teaches, with no nested Git repo.

## 3. Isolate
1. Copy `.env.example` to `.env` in the worktree, run `php artisan key:generate`, and set `DB_DATABASE` to `<owner's name>_lesson`. Fill other values the app needs from the owner's `.env` without printing them.
2. Run `php artisan migrate --force`, which creates that database. Do the same once with `DB_DATABASE=<owner's name>_lesson_test`, and run every test command with that variable set, so it overrides `phpunit.xml`.
3. Before any proof, print the effective database name for both and confirm neither is the owner's.
4. Use the framework's fakes for mail, notifications, storage, and outbound HTTP, and record each one. Serve on a free port. Never touch the owner's server or queue.

## 4. Build and prove
1. Run the existing tests first, and record baseline failures.
2. Write the solution at normal paths, using the same generators the guide will teach (`php artisan make:*`, `module:make-*`) and reviewing what each one creates.
3. Write Pest tests for each criterion and refusal, following `testing-best-practices`. Each step check names one test file or `--filter`, so later steps' missing classes don't break it. Prove "at the same time" criteria with real concurrent requests.
4. Review against the loaded rules, fix, and rerun. A new failure in an old test must be fixed, not hidden.
5. Run every gate in the worktree. Stop only servers and workers you started.

## 5. Write docs in `learn/NN-slug/`
1. Write README, GUIDE, and `check-yourself.md` from [templates.md](templates.md). GUIDE code comes from tested files.
2. Add first-seen PHP ideas to `learn/php-concepts.md`, using the format in [teach.md](teach.md). Check existing headings first.
3. Run `php <skill-dir>/scripts/learn.php guide-size learn/NN-slug/GUIDE.md`. Over the limit: split the ticket and rebuild the smaller slice. Never remove teaching to fit.

## 6. Start the lesson
1. Copy this lesson's test files into the owner's checkout. Never overwrite an existing file: if a shared file such as `tests/Pest.php` changed, show the diff and let the owner apply it. A scaffold or new module copies them at a named step, once the folder exists.
2. Set the ticket to in-progress. Disclose any incomplete proof.
3. Reply with the ticket and reference paths, baseline, changed-file count, criterion and gate results, rules and clashes, and limits. Then say: "Start a fresh session here to keep token use low, and say **start**." The owner may continue here if they prefer.
