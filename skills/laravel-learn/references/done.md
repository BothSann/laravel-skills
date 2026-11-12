# "done": check, then give the next step

For start or resume, skip to step 2.

## 1. Check the finished step
Run its check if it's read-only (see boundaries.md), otherwise ask the owner to paste the output.

| Step kind | Quick check |
|---|---|
| `composer require` | Package is in `composer.json`, and `composer.lock` changed |
| Generator | The files it creates exist at the expected paths |
| Typed a file | Read it for the step's one idea, then `vendor/bin/phpstan analyse <file>` |
| Route or wiring | `php artisan route:list --path=<path>` shows the route with its middleware |
| Test turned green | `php artisan test --filter=<name>` |
| Migration | Owner pastes `php artisan migrate` output; read the migration file |
| Request with a write | Owner pastes the output; compare with the ticket |
| New module or dependency | `php tools/boundaries.php sync --check`, then `vendor/bin/deptrac analyse` |

Passes: say so in one line. Fails: say what you saw in one or two lines, and don't give the next step. Offer **check** for a full review.

## 2. Give the next step
Run `php <skill-dir>/scripts/learn.php step learn/NN-slug/GUIDE.md <N>`. Don't read the whole guide. Give:
- The step number and title.
- What, Why, When, and How, shortened. For code, point to "GUIDE.md, step N" rather than pasting it, and name the one new idea.
- A new PHP idea: one line, plus its `php-concepts.md` heading.
- The check and its expected output.
- The cue: **done** or **check**.

## 3. Update the README
In "Where you are now", write what's verified and the next step.

No steps left: tell the owner to say **ship it**.
