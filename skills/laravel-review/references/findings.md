# Findings

## Severity

| Level | Meaning | Needs |
|---|---|---|
| P1 | Wrong result, data loss, or a security hole in normal use | The code path, and what goes wrong |
| P2 | Wrong under a condition that will happen: two requests at once, a failed call, a retry, a queue delay. Or an acceptance criterion with no test that proves it | The condition, and what goes wrong |
| P3 | Breaks a written rule, with no wrong behavior yet | The rule and where it is written |

When unsure between two levels, choose the lower one.

## Evidence
Every finding must be true of the code as it is, and checked:
- Name the exact line. Read the code it calls, and the config it depends on, before claiming what it does.
- State the concrete failure: which input or timing, and what the user or the data ends up with.
- A P3 names its source, such as the project's `AGENTS.md` or the `list-always-paginate` rule.

Drop a finding when you can't verify it, when it's a preference with no rule behind it, when a formatter or static analysis already enforces it, or when a higher rule source allows the code. Don't soften a guess into a question. Fewer true findings beat many doubtful ones.

## Comment shape
One paragraph: a bold severity and a title that says what to do, then the evidence, the consequence, and the fix.

```text
**P2 — Remove push subscriptions before reporting success.** This listener is queued, and the default queue connection is asynchronous. Until a worker runs it, the customer's subscriptions remain, so a notification can still reach their devices after deletion was confirmed. Remove the rows inside the deletion transaction, and queue only the external cleanup.
```

- The title is an instruction, without a trailing period: "Check every deletion result", not "Deletion result ignored".
- Write for the author: plain words, no praise, no hedging, no rule IDs without their meaning.
- Suggest the fix in words. Add code only when words would be longer.
- One finding per comment. If one cause shows up in several places, comment on the first and list the others in its body.

## File format
```json
[
  {
    "severity": "P3",
    "title": "Use TitleCase enum case names",
    "body": "The project's `AGENTS.md` requires TitleCase enum cases, but this enum uses `PASSWORD` and `OTP`. Rename them to `Password` and `Otp`, keeping the backed values.",
    "path": "Modules/Account/app/Enums/DeletionMethod.php",
    "line": 9,
    "source": "AGENTS.md, Enums"
  }
]
```

`line` is the line in the new version of the file. The script posts a finding inline when the pull request changes or shows that line, lists it in the review body when it doesn't, and skips it when one of your open threads on that file already has the same title.
