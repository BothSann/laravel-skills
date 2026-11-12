# Working on this repo

This repo uses GitHub Flow: `main` plus short-lived branches. There's no `dev` or `next` branch.

`npx skills add` installs from `main`, so anything merged reaches new installs straight away, even before a release. Keep unfinished work on its branch.

## Making a change

1. Branch from `main`, using a name like `feat/...`, `fix/...`, `docs/...`, or `ci/...`.
2. Open a PR. Make it one change, and give it a conventional title, like `feat: add pagination rule`.
3. When CI passes, squash and merge. The PR title becomes the commit message on `main`, and the branch deletes itself.

`main` requires a PR and passing checks, with no exceptions, and blocks force-pushes and deletion. Only squash merges are allowed.

For a big breaking rewrite that takes several PRs, use a temporary `next` branch, then delete it afterwards.

## Choosing a version

All skills share one version.

| Change | Example | Version bump |
|---|---|---|
| Fix | Scanner bug, wrong wording | `0.1.0` → `0.1.1` |
| New and compatible | New rule, new lesson type | `0.1.0` → `0.2.0` |
| Breaking | Changed cue, config field, or layout | `0.1.0` → `0.2.0`; `2.0.0` from `1.x` |

Stay on `0.x` until real lessons have proven the skills.

## Releasing

Release when there's something worth announcing, not on every merge.

1. Open a `chore(release): v0.2.0` PR that changes `version` in every `skills/*/SKILL.md`. CI fails if the skills disagree.
2. Merge it, then tag `main`:

   ```bash
   git switch main
   git pull --ff-only
   git tag -a v0.2.0 -m "v0.2.0"
   git push origin v0.2.0
   ```

3. The Release workflow confirms that the tag is on `main` and matches the skills, reruns CI, and creates the release with generated notes.

If the workflow refuses a tag, delete it, fix the problem, and tag again:

```bash
git push origin --delete v0.2.0
git tag -d v0.2.0
```
