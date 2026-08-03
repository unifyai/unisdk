<!--
    GENERATED FILE - DO NOT EDIT DIRECTLY.

    Regenerate with:  python3 .agents/global-rules/build_agents_md.py

    Edit the sources instead:
      .agents/repo.md              this repo's overview and always-on guidance
      .agents/rules/*.md           this repo's own rules
      .agents/shared.txt           which shared rules this repo includes
      .agents/global-rules/rules/  rules shared across all unifyai repos
                                   (submodule: unifyai/global-agent-rules)
-->

# UniSDK: The Python SDK for Orchestra

UniSDK is a thin Python SDK that wraps Orchestra's REST API, providing a clean programmatic interface for projects, logging, contexts, and storage operations.

## Core Functionality

- **Projects**: `create_project()`, `list_projects()`, `delete_project()`, `activate()`
- **Logging**: `log()`, `get_logs()`, `create_fields()`, `delete_logs()`
- **Contexts**: `create_context()`, `get_context()`, `commit_context()`, `rollback_context()`
- **Storage**: `get_signed_url()`, `download_object()`
- **Utilities**: `map()` for parallel operations with automatic logging

## Design Philosophy

The SDK abstracts away HTTP communication, handles authentication via `UNIFY_KEY`, and provides a Pythonic interface. This creates clean separation: consuming code (like Unify) focuses on business logic while UniSDK handles API communication.

## Position in the System

UniSDK sits between Unify and Orchestra. When Unify's managers need to persist data, they call UniSDK functions rather than making raw HTTP calls. This indirection allows Orchestra's API to evolve independently of its consumers, with UniSDK providing a stable interface.

## Related Repositories

- **orchestra**: The backend API that UniSDK wraps
- **unify**: Primary consumer of UniSDK for all persistence operations
- **unillm**: Independent (parallel SDK, not dependent on UniSDK)
- **unify-deploy**: Hosted communication stack may use UniSDK for logging/storage operations
- **console**: Uses Orchestra API directly (TypeScript), not the Python SDK

---

# Repository rules

# Local Development Environment

## Package Manager

This project uses **uv** for dependency management. Do not use pip, poetry, or other package managers.

## Python Interpreter

- Use `uv run` to execute commands within the virtual environment.
- uv creates a local `.venv` directory in the project root.
- To check the environment: `uv venv --python 3.12` (if needed)

## Environment Bootstrap

If the environment is not set up, install dependencies with:

```bash
uv sync --group dev
```

## Running Tests

### Default Contributor Check

```bash
uv run pre-commit run --all-files
```

### Mocked Smoke Tests

These tests do not require the internal Orchestra/GCP stack:

```bash
uv run pytest tests/test_async_admin.py tests/test_storage.py tests/test_http.py -v
```

### Full Integration Suite

Most of the test suite exercises a live backend or a local Orchestra deployment.
Set `UNIFY_KEY` and optionally `ORCHESTRA_URL` in `.env`, then run the target
pytest path directly.

```bash
# Single test file
uv run pytest tests/test_contexts.py -v

# Specific test function
uv run pytest tests/test_projects.py::test_create_project -v

# Multiple specific tests
uv run pytest tests/test_async_admin.py tests/test_storage.py -v

# Entire directory
uv run pytest tests/ -v
```

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. They include:
- Black (formatting)
- isort (import sorting)
- autoflake (unused import removal)
- YAML/TOML/whitespace hygiene checks

If a commit fails due to auto-formatting, simply re-run the commit command - the hooks will have fixed the files.

## Dependencies

- Config file: `pyproject.toml`
- Lock file: `uv.lock`
- Do not edit `uv.lock` manually. Use `uv add`, `uv remove`, or `uv sync`.

---

# Shared rules

These apply across every unifyai repo. Edit them in the `unifyai/global-agent-rules` submodule, not here.

# Aggressive Refactoring & Zero Backward Compatibility

## Context
This project is a prototype in rapid development. We prioritize a clean, minimal, and correct codebase over stability, backward compatibility, or risk aversion.

## Critical Rules

### 1. Zero Backward Compatibility
- **Assume NO Backward Compatibility**: Unless explicitly requested, break APIs, data structures, and protocols freely.
- **Immediate Updates**: When changing an interface, update all call sites immediately. Do not create adapters, aliases, or optional parameters to "soften" the change.
- **Purge Old Patterns**: If you introduce a new design pattern (e.g., for state management), strictly remove all instances of the old pattern. Do not leave mixed patterns in the codebase.

### 2. Destructive vs. Additive Editing
- **Avoid "Stapling"**: Do not merely add new logic on top of old logic (additive editing). This creates bloat and "staples upon staples".
- **Rewrite and Simplify**: When requirements change, **rewrite** the affected code to optimally support the *new* requirements as if they were the original ones.
- **Delete Aggressively**: If code is no longer the "best" way to do something, delete it. Do not comment it out. Do not keep it "just in case".

### 3. No Defensive Coding
- **No Preemptive Exception Handling**: Do not wrap code in try/catch or try/except blocks to prevent crashes unless you are handling a specific, expected, and recoverable runtime error (e.g., network timeout). Fail loud and fast.
- **No Defensive Checks**: Do not add null checks or type checks unless strictly necessary for the logic. Trust the type system and the caller contract.
- **Clean Implementation**: Code should look like the "happy path". Avoid cluttering logic with defensive branches for edge cases that shouldn't happen in a correct system.

### 4. Review and Reflect
- **Simplify First**: Before adding a feature, ask: "Can I simplify the existing code to make this feature natural to implement?"
- **Remove Bloat**: actively look for and remove redundant code, unused variables, and overly complex abstractions.

# No Temporal or Chat-Specific Comments

## Context
Code comments and docstrings must be **timeless** and describe the code as it currently exists. They must **never** reflect the history of changes, the current chat session, or the fact that code is "new".

## Critical Rules

### 1. No "New" or "Updated" Markers
- **Forbidden**: Never use words like "New", "Updated", "Added", "Modified", "Refactored" in comments to mark changes.
- **Reasoning**: Code is only "new" for the moment it is written. Next week, it is old. These comments rot immediately and create noise.
- **Correct Approach**: Just write the comment describing what the code does. Git history tracks what is new.

### 2. No Chat Context
- **Forbidden**: Do not reference "the user request", "this chat", "per instruction", or specific reasoning from the current conversation.
- **Reasoning**: The codebase must stand alone. Context from a chat session is lost to future readers.
- **Correct Approach**: If a complex decision needs explanation, document the *technical why* (e.g., "Use X because Y is slow"), not the *conversational why* ("User asked for X").

### 3. Clean Documentation
- **Focus**: Comments should explain **why** tricky code exists or **how** it functions.
- **Avoid**: "Here is the implementation of..." or "Standardized composer utilities". The code itself shows it is an implementation.
- **Example**:
  - BAD: `NEW: Added this function to handle retries`
  - BAD: `Updated to support the new API`
  - GOOD: `Retries the request with exponential backoff to handle transient network errors.`

If a test is failing, we should **never** add test-specific information or shortcuts to production code as a hack to get the test passing. No details about specific test cases should ever make their way into production code—no special-case branches, no hardcoded values that match test inputs, no conditional logic that only exists to satisfy a test.

All fixes must be fully general and **much** broader than the specific failing test. We do **not** want to overfit production code to a specific set of tests.

# Git Safety

## Rule: Pull Before Editing a Repository

Before making any file edits in a repository, run `git pull --rebase` once to sync with the remote. This prevents the agent from working on a stale branch and silently overwriting others' commits.

- **Once per repo per session** is sufficient — no need to pull on every turn.
- **After a push rejection + rebase**: re-read any files you plan to edit next. The rebase changed them on disk but your in-memory copies are stale.
- **Exception**: only skip if the user explicitly asks you not to pull.

## Context: Explicit Path Commits
When multiple agents run in parallel in `local` mode, there is a race condition risk if they use the shared git index (staging area).
- Agent A: `git add fileA`
- Agent B: `git add fileB`
- Agent A: `git commit -m "msg"` -> Commits BOTH fileA and fileB!

## Rule: Explicit Path Commits
To eliminate this risk, **NEVER** run `git commit` without explicit file arguments.

### Incorrect
```bash
git add myfile.json
git commit -m "Update myfile"
```

### Correct
```bash
# For modified files:
git commit myfile.json -m "Update myfile"

# For new (untracked) files:
git add myfile.json
git commit myfile.json -m "Add myfile"
```

### Reasoning
Passing filenames to `git commit` bypasses the shared index for that specific commit operation, ensuring that Agent A only commits what it intends to, regardless of what Agent B has staged.

## Rule: Push Only When Explicitly Asked

Do **not** push commits unless the user explicitly asks you to. This includes all forms of pushing:

- `git push`
- `git push origin <branch>`
- `git push --force` or `git push -f` (especially dangerous)
- `git push --force-with-lease`

### Reasoning
Pushing affects shared remote state. The user must decide when and where to push. Force pushing is particularly dangerous as it rewrites remote history and can destroy other collaborators' work.

### What To Do
- Commit changes locally (following the explicit path commits rule above)
- Inform the user that changes are committed and ready for them to push
- If the user explicitly asks you to push, push to the **current branch** only (e.g., `git push origin HEAD`)
- **Never** force push unless the user explicitly requests it and understands the consequences

## Rule: Staging-First Promotion

For repositories with a `staging` branch, **never open, retarget, auto-merge, or merge a feature/fix branch directly into `main` or `master`** unless the user explicitly says to bypass staging.

Required flow:

1. Land the change into `staging` first.
2. Let the staging deployment/validation run.
3. Promote with a `staging` -> `main`/`master` PR or merge.

Before any PR creation, PR retarget, merge, or auto-merge command, verify and state the base/head:

```bash
gh pr view <number> --json baseRefName,headRefName
```

Allowed:

- `feature-or-fix-branch` -> `staging`
- `staging` -> `main`

Forbidden unless explicitly approved by the user as a staging bypass:

- `feature-or-fix-branch` -> `main`
- `feature-or-fix-branch` -> `master`
- enabling auto-merge on either forbidden pattern

If a PR is already targeting `main`/`master` from a non-`staging` branch, stop before merging, disable auto-merge if it is enabled, and retarget/recreate the PR against `staging`.

## Rule: Agent PR Approval (`magic-marty`)

`unifyai/*` repos enforce branch protection: every PR to `main` or `staging`
requires at least one approving review from a Unify engineer **other than the
author** (SOC 2 CC8.1 separation of duties). Detect the active author first:

```bash
gh api user --jq .login
# or: gh auth status
```

When an agent authors a PR under that account, the approving review cannot come
from the same account.

The local `gh` CLI has two authenticated accounts:

| Account | Role |
|---|---|
| `<author>` (from `gh api user --jq .login`) | Author — create PR, enable auto-merge, merge after approval |
| `magic-marty` | Reviewer — approve only; satisfies the non-author review requirement |

`magic-marty` is a GitHub service account (Security Lead accountable). Use it
only for the approval step, not for authoring commits or opening PRs.

### When this applies

- Any `staging` → `main` release PR the agent opens under the active author account
- Any feature/fix PR to `staging` or `main` the agent authored under the active author account
- After `./staging_to_main.sh` or `gh pr merge --auto` — auto-merge stays
  blocked at `REVIEW_REQUIRED` until `magic-marty` approves

### Standard release flow (`staging` → `main`)

```bash
AUTHOR=$(gh api user --jq .login)

# 1. Author — create PR and queue auto-merge
gh pr create --base main --head staging \
  --title "Release: staging → main" \
  --body "Release PR from staging to main."
gh pr merge <number> --auto --merge

# 2. Approve as magic-marty (different reviewer than author)
gh auth switch --user magic-marty
gh pr review <number> --repo unifyai/<repo> --approve \
  -b "Release approval: staging CI green."

# 3. Merge as author — auto-merge completes once CI + approval land
gh auth switch --user "$AUTHOR"
gh pr view <number> --repo unifyai/<repo> \
  --json mergeStateStatus,reviewDecision
```

If auto-merge does not fire, merge explicitly as the author:

```bash
gh pr merge <number> --repo unifyai/<repo> --merge
```

### Invariants

- **Never self-approve.** The author account must not `gh pr review --approve` on a PR
  it authored.
- **Always switch back.** After approving as `magic-marty`, run
  `gh auth switch --user "$AUTHOR"` before any further git/gh work.
- **Verify base/head** before approving or merging (see Staging-First Promotion).
- **Approval is `magic-marty`; merge is the author.** If `magic-marty` cannot
  merge (e.g. unverified email), that is expected — only the approval must
  come from `magic-marty`.

### Batch promotions across repos

For "merge staging into main in each repo" requests, repeat per repo in order:

1. Author account — create PR + `--auto --merge`
2. `magic-marty` — `--approve` on each open PR
3. Author account — confirm `reviewDecision=APPROVED`, then let auto-merge complete

## Rule: Cross-Repo Push Semantics

When the user says "commit and push to all repos", "push across repos", or similar, interpret that as:

- For each repo that has a `staging` branch locally or on origin: commit directly to `staging` and push `staging`.
- For each repo without a `staging` branch: commit directly to `main` or `master` and push that branch.
- Do not create feature branches or PRs unless the user explicitly asks for a PR workflow.
- Do not merge a non-`staging` branch into `main`/`master` as part of a cross-repo push.

Before committing or pushing in each repo, verify its integration branch:

```bash
git branch --list staging main master
git branch -r --list origin/staging origin/main origin/master
```

If `staging` exists, use it. If it does not exist, use `main`/`master`.

# Worktree Mode: Direct Commits, No Feature Branches

## Context
When running in **worktree mode**, the mental model is fundamentally different from traditional feature development:

- **Worktrees are for small-scale parallel fixes**, not large-scale feature development
- **Multiple agents on the same branch** = multiple collaborators working in parallel, each with their own local working directory
- The overhead of `feature branch → PR → merge → cleanup` is **overkill** for this workflow

## Critical Rules

### 1. NEVER Create Feature Branches
When asked to make changes, commit, or push:
- **DO NOT** create a new branch (e.g., `git checkout -b feature/...`)
- **DO NOT** suggest creating a branch for the work
- **COMMIT DIRECTLY** to whatever branch is currently checked out

The worktree already provides isolation. Creating additional branches defeats the purpose.

### 2. NEVER Create Pull Requests
- **DO NOT** use `gh pr create` or suggest creating a PR
- **DO NOT** push to a new remote branch with the intent of opening a PR
- If the user wants changes merged, they will handle the merge strategy themselves

### 3. The Correct Workflow
```bash
# 1. Make your changes to files

# 2. Commit directly to the current branch (following git-commit-safety rules)
git commit <specific-files> -m "Description of change"

# 3. Only if the user explicitly asks you to push, push to the CURRENT branch
git push origin HEAD
```

### 4. Mental Model
Think of worktree agents as **multiple developers pair-programming on the same branch**:
- Each has their own local checkout (the worktree)
- All commit to the same branch
- No one creates personal feature branches for small fixes
- Coordination happens through communication, not branch isolation

## Why This Matters
The alternative workflow creates significant noise:
1. **Stale branches accumulate** - agents create branches, users forget to delete them
2. **PR overhead** - reviewing, merging, and closing PRs for trivial fixes wastes time
3. **Context switching** - users must mentally track multiple branches for what should be one stream of work
4. **Merge conflicts** - more branches = more opportunities for conflicts

## Exception
If the user **explicitly asks** for a feature branch or PR workflow, follow their instructions. But **never default to this behavior** in worktree mode.

# Git History for Context

## Context
This rule applies when you are trying to understand the *rationale* behind specific code blocks, the evolution of a module, or when deciding whether "weird" looking code is essential or legacy technical debt.

## Rules

### 1. Strategic Git Usage
- **Use as a Second Level of Analysis**: If the code's purpose isn't clear from the current state alone (static analysis), use `git blame` or `git log` to uncover the "why".
- **Not a Mandate**: Do not check git history for every file you touch. This creates noise. Use it selectively when you lack context.

### 2. Understanding Code Evolution
- **Identify Legacy Code**: If you suspect code is redundant or outdated, check its commit date and message. If it was added months ago for a feature that is no longer relevant, this confirms it can likely be purged.
- **Find the "Why"**: Expressive commit messages often contain the reasoning that comments lack. Use them to understand the author's original intent before refactoring or deleting complex logic.

### 3. Targeted Queries
- **Be Surgical**: When querying git, look for the history of specific lines or changes (e.g., `git blame -L n,m filename` or `git log -p filename`) rather than dumping the entire history into the context.
- **Synthesize**: Use the information to form a narrative about the code's lifecycle (e.g., "This was added in commit X to fix bug Y, but since we rewrote the bug Y subsystem, this is now dead code").

### 4. Investigating Regressions with Git Diff

When debugging test failures or regressions, git history can pinpoint exactly what changed.

**When the user proactively provides context:**
If the user says something like "the test was passing at commit `<hash>`, and the relevant changes are in `<path>`", use this optimally:
- Run `git log --oneline <hash>..HEAD -- <path>` to see which commits touched the area
- Run `git diff <hash>..HEAD -- <path>` to get the **aggregate diff** (not serial diffs commit-by-commit)
- Cross-reference the diff with commit messages to understand developer intent
- The overall diff is mathematically equivalent to composing serial diffs, but far more token-efficient and cognitively cleaner

**When debugging hits a roadblock:**
If direct code analysis and debug logging (`CURSOR_DEBUG_LOG`) aren't yielding answers, *then* ask the user:
- "Do you know when this test was last passing? If you have a commit hash and know which files/folders are likely involved, that would help narrow down what changed."
- Don't front-load this question—often the user doesn't know the answer. Try direct debugging first.

**Avoid wasteful patterns:**
- Don't ask the user to provide diffs—ask for the commit hash and run git commands yourself
- Don't read diffs commit-by-commit and mentally compose them; use the aggregate diff
- Don't dump entire file histories; scope queries to the relevant path(s)

# Staging→Main Release Gates Are Fail-Closed

Every repo's `Staging->Main` ruleset requires at least one status check whose
job makes an expensive or conditional run (full pytest matrix, paid LLM smoke
tests, E2E). Those jobs don't run on every push — they're gated on a
`[run-tests]`/`[run-flows]`-style commit-message tag, or on the PR event
itself. As of **2026-07-31**, the required context for that job is published
**unconditionally** on every push: an explicit pass or fail, never an
implicit pass from a skip.

## Why: the orchestra incident

Before 2026-07-31, the required context was only published when the gated
job actually ran; an ordinary push that skipped it published nothing, and
**GitHub counts a skipped required check as satisfied**. A staging→main
release PR shares its head SHA with whatever was last pushed to staging, so
that stale implicit pass could satisfy branch protection before the real
PR-triggered run finished. In orchestra this let four release PRs (#125,
#127, #128, #129) merge into main carrying a skipped/failing suite — #125
merged 83 seconds into an 11-minute test run that later came back failing,
leaving a broken test on main for thirteen hours.

The fix — "make the gate fail closed" — makes an aggregator job republish the
required context unconditionally, so a push that didn't run the suite now
reports that context **red**, not green-by-default.

Rolled out the same week to: orchestra (`pytest`), unillm (`pytest`), unify
(`Flow smoke`), unify-deploy (`Integration smoke`), console (`Push Gate`).
Check name and trigger tag differ per repo; the fail-closed shape is the
same. unisdk, brain, docs, and landing-page have no equivalent
expensive/conditional gate, so this doesn't currently apply there — but
treat it as the default shape for any new staging→main required check in
any repo.

## The `if:`-scoping approach does NOT work — verified 2026-08-03

An earlier version of this rule described scoping the aggregator job's own
`if:` to `pull_request`/`workflow_dispatch` (unify's `05fbdcce9`) as the
fix for the fail-closed-on-push problem below. **That is wrong, and left
orchestra and unify-deploy releases merging on a stale pass again**, plus
unify itself carrying an unnoticed stale pass on its own staging HEAD.

The reasoning behind that approach assumed an `if:`-scoped job produces *no
check run at all* when its condition is false. It does not: **GitHub Actions
still publishes a "skipped" check run for a job whose `if:` evaluates to
false**, even when that job is the required aggregator itself, and a skipped
required check is satisfied exactly like a pass. Scoping only the aggregator
job's `if:` — while the *workflow file* it lives in still triggers on
`push` — just changes what an ordinary push publishes from an explicit
failure back to a skip, which is the original 2026-07-31 bug, verbatim.

## The real fix: no `push` trigger on the gate's workflow file at all

The only way to guarantee an ordinary push publishes **nothing** under the
required context name is for the *workflow file* that defines the
aggregator to never be triggered by `push` in the first place. A workflow
with no `push` in its `on:` block simply never runs on a push event, so
none of its jobs — passing, failing, or skipped — produce a check run for
that SHA. The context sits genuinely `pending` until the real
`pull_request`-triggered run supplies an answer.

Concretely: split the gate into two workflow files.

- **The everyday/ad-hoc workflow** (existing file) keeps `push` (gated by
  the `[run-tests]`/`[run-flows]`/`[run-integration]`-style tag) and
  `workflow_dispatch`, for ordinary developer feedback. It must **not**
  define the aggregator job, and its own expensive test job must not share
  a job id/name with the required context (see the collision gotcha below).
- **A new, dedicated workflow file** (e.g. `pytest-release-gate.yml`,
  `flow-smoke-release-gate.yml`, `integration-smoke-release-gate.yml`)
  triggers **only** on `pull_request: branches: [main]` and
  `workflow_dispatch`. It contains its own copy of the expensive test job
  plus the aggregator job that publishes the required context. Because this
  file has no `push` trigger, an ordinary push can never populate that
  context under any name defined in it.

Applied 2026-08-03 to orchestra (`pytest-release-gate.yml`), unify
(`flow-smoke-release-gate.yml`), unillm (`pytest-release-gate.yml`), and
unify-deploy (`integration-smoke-release-gate.yml`). console's `Push Gate`
was checked and found **not** vulnerable to this bug: its push-triggered run
genuinely executes the full suite unconditionally (no tag-gating), so there
is no skip to exploit — no fix needed there.

## Gotcha: job-id collision reintroduces the same bug

After removing the explicit aggregator from the everyday workflow, check
that its own expensive test job doesn't accidentally publish the exact same
context name. In orchestra, the plain development `pytest:` matrix job had
no explicit `name:`, so its check run defaulted to its job id — which
happened to be the literal string `pytest`, the required context. A job
whose matrix never expands (because its own `if:` evaluated false) still
publishes **one** check run under that bare job id, not per-shard, so this
silently recreated the stale-skip bug via a different job. Fix: give the
everyday job a distinct job id and/or explicit `name:` (orchestra renamed it
to `pytest-dev`). Always verify this when doing this split — confirm the
everyday workflow's job names don't coincide with any required-check context
string, matrix or not.

## Gotcha: don't write the trigger tag in prose in a commit message

The `push` gating check on these jobs is a naive substring match against the
full commit message (subject + body) for `[run-tests]` / `[run-flows]` /
`[run-integration]`. Writing that literal bracketed tag *anywhere* in a
commit message — including inside a sentence explaining how the tag
mechanism works — re-triggers the real (sometimes paid, sometimes
live-infra) job on that push. This happened twice while rolling out the fix
above: a commit message explaining unify's ad-hoc `[run-flows]` trigger
accidentally fired a real paid Flow Smoke run (caught and cancelled before
much cost), and a commit message explaining unify-deploy's
`[run-integration]` trigger fired a real live Integration Smoke run against
staging infra that ran to completion (~18 minutes) before failing on an
unrelated live-infra teardown timeout — cleanup steps still ran, so no
resource leak, but wasted CI/infra time. When a commit touches one of these
workflow files and needs to describe its trigger tag, break up the literal
bracket sequence (e.g. quote it without brackets) so the substring match
cannot fire.

## What to do when a release PR is stuck or merges on a stale pass

**Stuck/blocked** — `reviewDecision: APPROVED`, `mergeable: MERGEABLE`,
`mergeStateStatus: BLOCKED`, and the required context shows both a
`FAILURE` and a `SUCCESS` entry for the same PR head SHA from two different
workflow runs (one push-triggered, one pull_request-triggered): this is the
pre-`if:`-scoping failure mode. Push a small commit carrying the trigger tag
to give the release PR a fresh head with a single, unambiguous run, and
apply the real fix above so it stops recurring.

**Merges anyway on a stale pass** — the required context shows `SKIPPED` on
a push-triggered run for the PR's head SHA, and the PR merges (or already
merged) before the real `pull_request`-triggered run finished: this is the
`if:`-scoping-is-insufficient failure mode described above. Apply the real
fix (dedicated no-`push` workflow file) — do not consider the job's `if:`
condition alone a fix.

In both cases: do not force-merge, disable the ruleset, or bypass the check
to route around this — the real fix satisfies the gate on its own terms.

# Python Formatting & Pre-commit

Every first-party Python repo (`orchestra`, `unify`, `unisdk`, `unillm`,
`unify-deploy`, `docs`) enforces formatting with **black** (plus
`isort`/`autoflake` where configured), and CI rejects unformatted code. A
missing local hook or a drifting Black target/Python version is the single
most common avoidable CI failure. This rule keeps local and CI identical so
it stops blocking us — for Cursor, Claude Code, Codex, and humans alike.

## Single source of truth: the locked `lint` group

The formatters are ordinary, locked dependencies — not a version hardcoded in
the pre-commit hook or in CI YAML.

- Each repo declares its formatters in a dedicated **`lint` dependency
  group**, pinned and committed to the lockfile (`uv.lock` / `poetry.lock`).
  The `dev` group includes `lint` so a normal sync gives developers everything.
  - uv repos: `[dependency-groups]` → `lint = ["black==X", "isort>=…",
    "autoflake>=…"]`, and `dev = [ …, {include-group = "lint"} ]`.
  - poetry repos: `[tool.poetry.group.lint.dependencies]` (or `dev` where
    that is the established home).
- **Both** the pre-commit hook and CI run that **same locked** tool via the
  package manager — never a separate pin:
  - pre-commit hook: `entry: uv run black` / `poetry run black`,
    `language: system` (no `additional_dependencies`).
  - CI (uv): `uv sync --only-group lint --no-install-project` then
    `uv run --no-sync black --check .` on **Python 3.12**.
  - CI (poetry): `poetry install --only lint --no-root` then
    `poetry run black --check .` on **Python 3.12**.
- Pin Black's language target in every Python repo so local Mac Pythons and
  CI 3.12 cannot disagree (Black 26+ defaults toward newer targets):

```toml
[tool.black]
target-version = ["py312"]
```

- Never introduce a second black version or a parallel invocation anywhere
  (CI YAML, Dockerfiles, docs, ad-hoc `pip install black`, hook
  `additional_dependencies`). The locked `lint` group is authoritative; this
  rule deliberately does not restate the number — look it up in the repo's
  `pyproject.toml` / lockfile so guidance can never drift from reality.
- Keep the version **in lockstep across all the Python repos**: a bump is one
  coordinated change per repo (the `lint` pin + lockfile) applied to every
  repo so they don't diverge.

## Committed hooks (required once per clone / worktree)

`.git/hooks/` is a per-checkout artifact. Fresh clones, Cursor/Codex/Claude
worktrees, and cloud agents start with **no** hooks, which is why unformatted
code reaches CI.

Each Python repo commits `.githooks/pre-commit`. Enable it with the shared
helper (idempotent, tool-agnostic):

```bash
python3 .agents/global-rules/ensure_git_hooks.py
```

That sets local `core.hooksPath=.githooks`. Do this before the first commit
in any new clone or worktree. Coding agents (Cursor, Claude Code, Codex)
MUST run it at session start when working in a checkout that has
`.pre-commit-config.yaml`.

`pre-commit install` alone is no longer enough — it writes into `.git/hooks/`,
which worktrees and new clones miss. Prefer `ensure_git_hooks.py`.

## Before you commit (required)

1. Ensure committed hooks are wired (above).
2. Let the hook run on `git commit`, or run it explicitly on what you changed:

```bash
pre-commit run --files <changed-files>   # or: pre-commit run --all-files
```

3. Never bypass hooks: do not use `git commit -n` / `--no-verify`.

## Formatting across multiple repos

When juggling several repos, do not invoke a globally-installed `black` —
versions drift between machines and repos and produce diffs CI rejects.
Always format through the repo's pinned tooling, which uses that repo's
locked version:

```bash
pre-commit run black --all-files          # or: uv run black .  /  poetry run black .
```

## Release gates

`black` is a required status check on `staging → main` (ruleset and/or branch
protection) for the Python repos. Direct pushes to `staging` stay open for
the worktree workflow — the committed git hook is the staging-side gate.
CI still runs `black` on every push so failures are visible immediately.

## Why this matters

Without committed `.githooks` + `ensure_git_hooks.py`, the first place
formatting is checked is CI — which then burns agent turns on mundane
reformats. Pinning Black's target and CI Python to 3.12 removes the
"works on my Mac, fails in Actions" class of failures.

# Shared agent conversation archive

Unify keeps a private repo of **raw** agent transcripts at **`~/shared_context`**
(GitHub: `unifyai/shared_context`), keyed by **GitHub login** (e.g. `djl11`).

## Design (important)

- **Adjacent clone, not a submodule.** `shared_context` sits next to product
  checkouts (`~/unify`, `~/orchestra`, `~/brain`, …). It is **not** nested under
  any public or private product repo.
- **Why:** `unify` (and other open repos) stay public; transcript data stays
  private. Public cloners never need or see this tree. One clone serves agents
  in **every** eng repo that pulls `unifyai/global-agent-rules`.
- **Applies everywhere** this rule is loaded: `unify`, `orchestra`, `unisdk`,
  `unillm`, `unify-deploy`, `console`, `brain`, `docs`, `landing-page`, and any
  other repo that includes these global rules.

## When to load this

Use before answering questions about past investigations or decisions across the
team — e.g. "did we set up X?", "who changed Y?", "why did we do Z?" — when the
answer might live in someone else's Cursor / Claude Code / Codex session, not
only the current chat.

## How to search

Prefer ripgrep over reading whole files. Search **tracked** login trees only —
**do not** search `yours/` unless the user explicitly asks about their local /
unexported chats:

```bash
rg -n -i "keyword" ~/shared_context/derived/index.jsonl
rg -n -i "keyword" ~/shared_context -g '!yours/**' -g '!tools/**' -g '!.git/**'
```

`derived/index.jsonl` is rebuilt locally by `tools/sync.sh` / `tools/export.py`
after pull (gitignored). If it is missing, search tracked trees directly or run:

```bash
python3 ~/shared_context/tools/export.py --index-only
```

Sessions live at
`<github_login>/{cursor|codex|claude-code}/<yyyy-mm>/<id>/{meta.json,transcript.jsonl}`.

`yours/{cursor,codex,claude-code}` are local symlinks to personal stores and are
gitignored.

If `~/shared_context` is missing, say so and suggest:

```bash
git clone git@github.com:unifyai/shared_context.git ~/shared_context
```

Do **not** suggest `git submodule add` / nesting it under a product repo.

## Citing

Cite **user**, **tool**, **date**, and **path** so a human can open the same session.

## Do not

- Do not confuse this with `brain` (curated company memory).
- Do not scrub or rewrite historical transcripts.
- Do not push/sync unless the user asked you to.
- Do not grep `yours/` unless the user asked for local-only context.

# OpenAI is reached only through OpenRouter

Every LLM call in every repo routes through **OpenRouter**, using
`OPENROUTER_API_KEY`. The company's direct OpenAI account is not active — it
answers `429 billing_not_active` — so any code path that talks to OpenAI
natively is dead code that fails slowly.

## Canonical endpoint form

```
openai/<model-id>@openrouter      # openai/gpt-5.6-terra@openrouter
```

Never `<model-id>@openai`. In UniLLM, `@openai` and `@openrouter` are distinct
providers (`unillm/endpoints/utils.py`): `@openrouter` resolves through the
OpenRouter catalog, `@openai` resolves to a native OpenAI endpoint and litellm
sends it straight to OpenAI with `OPENAI_API_KEY`.

**The alias changed meaning.** `gpt-*@openai` used to be *transported* via
OpenRouter inside UniLLM. It now means native OpenAI. Model strings written
before that change did not move — they silently re-pointed at a dead account.
The Orchestra migration `2026-08-13-00-00_openrouter_model_endpoints.py`
rewrote stored assistant endpoints for exactly this reason; source code was not
covered by it.

## Why this fails slowly rather than loudly

OpenAI reports the billing fault as **HTTP 429**, the same status as
rate-limiting. UniLLM's `_is_retryable` classifies 429 as transient and retries
`UNILLM_TRANSIENT_RETRY_COUNT` (default 6) times with 1/2/4/8/16/32s backoff —
63s of sleeping per call, multiplied by litellm's own internal retries, before
it finally raises. Under any concurrency this is indistinguishable from a hang,
and scheduled jobs look stuck rather than broken. Do not "fix" such a stall by
raising a timeout; check the endpoint's provider suffix first.

## Hard rules

- New LLM call sites use `openai/<id>@openrouter`. Non-OpenAI providers
  (Anthropic, Google, …) are unaffected by this rule and keep their own routing.
- Never read `OPENAI_API_KEY` directly, and never construct `openai.OpenAI()`
  against it, in application code.
- Env defaults and `.env.example` entries carry the `@openrouter` form, so a
  fresh checkout cannot inherit a dead route.
- When a provider call stalls for ~a minute and then fails, suspect a native
  provider suffix before suspecting the network.

## The one legitimate direct-OpenAI path

Masked image edits (`images.edit` with `gpt-image-2`) have no OpenRouter
equivalent — OpenRouter's unified Image API does not expose the mask parameter.
That path may use a separately-named credential (`OPENAI_DIRECT_API_KEY`), must
never fall back to reading `OPENAI_API_KEY`, and must degrade loudly when the
credential is absent. It is the only exception; adding another needs an
explicit reason, not convenience.
