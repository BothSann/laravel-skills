# When the agent writes in the app

Only these cases, each limited to its scope.

## Tests
The agent writes all tests in the worktree, in Pest. They're copied in at lesson start, per write.md. If a test must change later, explain why, because the owner reads them and doesn't write them. Follow `testing-best-practices`.

## Scribe attributes
Only when `standingExceptions` includes `scribe`, and only after the owner's code works. Add `#[Group]`, `#[Endpoint]`, `#[Authenticated]`, `#[Response]`, and parameter attributes to the controller, matching what the tests prove, and change nothing else. Then list them in a short `Endpoint | Documented as` table so the owner can read what each one produces. The project's own Scribe conventions come first.

## PHPDoc
Only when `standingExceptions` includes `phpdoc`. Add blocks where a native type can't say enough: array shapes, generics such as `Collection<int, Post>`, and `@throws`. Never repeat what the signature already states.

## "you write it: <item>"
Write that item only, not the one next to it. If it's unclear, ask which. Then explain it like a lesson step: What, Why, When, and How.

## Fixes
Only after "check and fix", or when the owner asks for a specific fix.

## Not exceptions
Models, migrations, generator commands, dependency changes, and route wiring stay with the owner unless named in "you write it". Even then, the owner runs migrations.
