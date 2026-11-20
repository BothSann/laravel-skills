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
At most 8 steps of 5–15 minutes, one new idea per step. Show only code the owner types; tests stay in their files. Each check must pass using only earlier steps, usually `php artisan test --filter=<name>` or `php artisan route:list --path=<path>`.

````markdown
# Guide: <task>

## The big idea
Before:
- <what happens today, e.g. the route is a 404>

After:
- <what works after this lesson>
- <each refusal: status and when>

One request, layer by layer:
```text
<METHOD /path → middleware → form request → controller → action → resource → status>
```
New this lesson: <the new layer, in one line>

## Step N: <one command, file, or wiring change> (~N min)
Goal: <what works after this step, in one line>

Type this in `<path>`:  (or "Run this:", or "Agent writes `<path>`:")
```php
<tested code, with // ① ② ③ on the lines that matter>
```
- ① <what that line does>

### New idea: <name>
**What it is**
- <one plain fact>

**Why we use it**
- <the problem it solves in this app>

**What breaks without it**
- <what you'd see: the error, status, or bug>

**Like in <compareWith>**
- <a real match: a function, library, or pattern>

**When you'll use it again**
- <the next situations in this app>

**Watch out** (optional)
- <one trap>

<details><summary>Deeper</summary> <optional extra detail> </details>

Run: `<check command>`
You should see: <expected output>

## Rules this lesson follows
| Choice | Rule |
|---|---|

## Finish
- <gates, criteria proof, and PR base>
````

Writing rules:
- Bullets, not paragraphs. One fact per bullet, about 15 words at most, at most 3 under a heading. More goes in "Deeper" or `php-concepts.md`.
- One new idea per step. A second idea means split the step; for a long file, type the shell first, then each method.
- At most 3 markers per code block, one line each.
- A step with no new idea skips the card: "Same shape as `<file>`; only <difference> changes."
- "Like in" is a real programming match from `compareWith`, never an everyday object. No honest match, or `compareWith` is `null`: leave the heading out.
- Explain each new word where it first appears. Use this app's names. "It is best practice" and "when needed" are too vague.
- A generator step gives the exact command, lists the files it creates, and says which lines the owner then changes.
- A plain PHP idea's card also goes in `php-concepts.md` the first time; later steps link its heading. Explain Laravel magic once, when it first matters.
