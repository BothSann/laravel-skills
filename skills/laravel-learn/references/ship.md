# "ship it"

The owner runs every command. Give them in order and read the output.

1. **Prove each criterion:** one test, request, or log line per ticket criterion. Record them in a `# | Criterion | Command | Result` table for the PR.
2. **Gates:** every command in `gates`. All must pass; a failure goes to `check`. Lesson tests ship with the owner's code.
3. **Docs:** update what the change touches, such as the plan or `.env.example`. If `standingExceptions` includes `scribe`, add the attributes now, per [exceptions.md](exceptions.md), and have the owner run `php artisan scribe:generate` and open the page.
4. **Commits:** give exact commands, one small piece per commit, in `commitStyle`. Name the files; never `git add -A` or `git add .`. Have the owner confirm `git status` shows no `learn/`, `.env`, or `vendor`.
5. **PR:** the owner pushes and opens it against `baseBranch`. Write the body:

```markdown
## Summary
- <What changed.>

## Scope
In: <this slice>. Out: <the next one>.

## Acceptance criteria
<The table from step 1.>

## Gates
<Each gate and its real result.>
```

6. **Close:** set the ticket to done and the README to "Done. PR #N." Offer **what next**.

Cleanup runs later: once the PR is merged, the next "what next" run removes the reference worktree. To remove it sooner, run `php <skill-dir>/scripts/learn.php cleanup <repo>` after the merge, and report what it removed. If the lesson is abandoned, ask the owner first, then use `--abandoned NN-slug`. Lesson docs in `learn/` stay. The two lesson databases are reused by the next lesson; dropping them is the owner's choice.
