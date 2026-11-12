---
name: laravel-review
description: Review a Laravel pull request for bugs and rule breaches, then post the findings as inline GitHub comments. Use for "review PR 12", "re-review", or "post the review".
license: MIT
metadata:
  author: BothSann
  version: "0.1.0"
---

# Laravel pull request review

Finds real defects and rule breaches in a pull request and posts them as one GitHub review of inline comments. This skill holds no rules of its own. Read [findings.md](references/findings.md) before writing a finding, and [method.md](references/method.md) before reading the diff.

## Steps
Run from the repo root. The script is `<skill-dir>/scripts/review.php`.

1. **Context:** `php review.php context <pr>`. A merged or closed pull request: stop unless asked. "nothing new since your last review": say so and stop.
2. **Rules,** in this order of authority:
   1. The project's own files, listed as `rule sources`.
   2. Laravel Boost's `laravel-best-practices` and `testing-best-practices`. If Boost isn't installed, say so once and carry on.
   3. `laravel-api-practices`, and `laravel-modular-monolith` when `layers` lists `modules`.

   A higher source overrides a lower one. Rules for a layer that isn't installed don't apply.
3. **Intent:** read the title, body, and linked issue with `gh pr view <pr> --json title,body,closingIssuesReferences`. Acceptance criteria there are part of what you check.
4. **Review** the range the `review:` line names, reading surrounding code as needed.
5. **Earlier threads:** for each of `your open threads`, check whether the new commits fixed it. Report that in the terminal only. Never reply to, resolve, or repost a thread.
6. **Preview:** write the findings to a JSON file outside the repo and run `php review.php preview <pr> <file>`. Show the owner its output and the state of the earlier threads.
7. **Post** only after the owner confirms, or when their request already said to post:
   - Findings: `php review.php post <pr> <file>`.
   - No findings, and every earlier thread is fixed: `php review.php clean <pr>`.

## Limits
- Reviews are comments only. Never approve, request changes, merge, push, or edit code.
- One review per run. Posting is public and can't be fully undone, so never post unasked.
- Report what you didn't check: code you couldn't read, tests you didn't run, and anything outside the diff.
