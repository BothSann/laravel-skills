# Lesson templates

## README.md
Keep it short. `learn.php cleanup` reads the Worktree line, so keep its exact form.

```markdown
# Lesson NN: <task>

## Goal
<Observable behavior and safeguards.>

## New words
| Word | Plain meaning |
|---|---|

## Steps
| Step | Work | Who |
|---|---|---|

## Solution workspace
- Worktree: <absolute path>
- Starting commit: <sha and copied changes>
- Changed files: <list>
- Proof: <tests, gates, criteria, fakes, unrun checks>

## Where you are now
- Verified: none yet
- Next: step 1
```

## GUIDE.md
At most 6 steps of 5–15 minutes, about 4,000 tokens including code. Show only code the owner types; tests stay in their files. Each check must pass using only earlier steps, usually `php artisan test --filter=<name>` or `php artisan route:list --path=<path>`.

```markdown
# Guide: <task>

## The big idea
<Before and after behavior, and the path of one request through the app.>

## Rules this lesson follows
| Choice | Rule |
|---|---|

## Step N: <one command, file, or wiring change>
Who: you type | you run | agent writes

What: <the thing and its exact path>
Why: <the problem here, and what breaks without it>
When: <when it runs, and when you'd write one again>
How: <command or tested code, then one line per new idea>
Check: <command and expected output>

## Finish
<Gates, criteria proof, and PR base.>
```

A generator step gives the exact command, lists the files it creates, and says which lines the owner then changes. Use this app's names in every part. "It is best practice" and "when needed" are too vague. For a first-seen PHP idea, write one line and point to its `php-concepts.md` heading. Explain Laravel magic once, when it first matters.

## check-yourself.md
Write 4–6 questions about this lesson's real code, including one "what breaks if" and one trick question. Answers are 1–3 sentences with a bold short label.

```markdown
1. <Question>

   <details><summary>Answer</summary>

   **<Short answer>.** <Explanation.>

   </details>
```
