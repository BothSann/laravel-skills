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
At most 8 steps of 10–20 minutes, one new idea per step. Show only code the owner types; tests stay in their files. Each check must pass using only earlier steps, usually `php artisan test --filter=<name>` or `php artisan route:list --path=<path>`.

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

<Opener: one plain line saying what this code is, often with a picture.> **New idea: <name>.**

Type this in `<path>`:  (or "Run this:", or "Agent writes `<path>`:")
```php
<tested code, no markers>
```

1. **The imports** — <what each `use` brings in, grouped in one item>
2. **`<a line or short piece of code>`** — <what it does>. <Why it is there.> <What breaks without it, when there's a real error or bug to name.>

**Inside `<method or block>`:**
3. **`<line>`** — <what it does, with a real value, e.g. `POST /api/v1/posts` with `{"body": ""}` → 422>. <Why. Remember `<X>` from step N? …>
4. **`<line>`** — <what and why>. <The trap, if this line has one.>

In short: <one or two sentences: what this code does, start to finish>

Run: `<check command>`
You should see: <expected output>

## Rules this lesson follows
| Choice | Rule |
|---|---|

## Finish
- <gates, criteria proof, and PR base>
````

Writing rules for a step:
- **Opener.** One plain line before the code saying what it is ("This is the bouncer for…"), ending with the step's one new idea in bold. A second new idea means split the step; for a long file, type the shell first, then each method.
- **Walkthrough, every line.** After the code, a numbered list quotes each piece of code in backticks and explains it. Group boring lines (imports, closing braces) into one item. Never skip a line silently.
- **What, then why.** Each item says what the code does, then why it is there. Add what breaks without it only when there's a real error, status, or bug to name. Short sentences, as many as the line needs.
- **Sub-labels for nested code.** When a block has parts (a method body, a closure, a `try`/`catch`), group its items under a bold label like **Inside `handle()`:**, not a new heading.
- **Real values.** Each step shows at least one concrete value moving through the code, using this app's routes and data: a request body, a status, a row, a config value.
- **One picture per step.** An everyday analogy ("the bouncer at the door", "the app's memory box") may stand for the new idea. Reuse the same picture whenever that idea comes back.
- **Point back.** When a line uses something an earlier step or lesson built, say so by name: "Remember the `StorePostRequest` from step 2?"
- **Traps live on their line.** A trap goes in the item for the line where it bites, not in a separate section.
- **In short.** Close each step with one or two sentences recapping the code start to finish, right before Run.
- **Agent-written code gets the same walkthrough.** The owner reads it even without typing it.
- **A step that changes earlier code** walks through only the new or changed lines, and points back to the step that explained the rest: "The rest is the same as step 3."
- **Explain each new word where it first appears.** Use this app's names. "It is best practice" and "when needed" are too vague.
- A generator step gives the exact command, lists the files it creates, and says which lines the owner then changes.
- A plain PHP idea also goes in `php-concepts.md` the first time; later steps link its heading. Explain Laravel magic once, when it first matters.
