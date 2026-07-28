<!--
    GENERATED FILE - DO NOT EDIT DIRECTLY.

    Regenerate with:  python3 .agents/global-rules/build_agents_md.py

    Edit the sources instead:
      .agents/repo.md              this repo's overview and always-on guidance
      .agents/rules/*.md           this repo's own rules
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

# Full Local Stack First

This is internal agent/developer guidance. It intentionally differs from the
public `unify` README: the README is for open-source users who run `unify`
against hosted Orchestra and do not have the private `unify-deploy` repo. For
internal cross-repo work, default to the private full local stack in
`unify-deploy/selfhost/`.

Before starting, stopping, rebuilding, or repairing any local service, assume the
full stack may already be running and inspect it first:

```bash
bash ~/unify-deploy/selfhost/stack.sh status
```

Default commands:

- Start full source stack from an agent session: `bash ~/unify-deploy/selfhost/stack.sh up --durable`
- Start full source stack from a long-lived human terminal: `bash ~/unify-deploy/selfhost/stack.sh up`
- Repair only Console: `bash ~/unify-deploy/selfhost/stack.sh repair-console`
- Smoke test: `bash ~/unify-deploy/selfhost/stack.sh smoke`

When a A coding agent is asked to deploy or start the full local source stack for
the user, always use `up --durable`. Do not keep the stack alive with `nohup`, a
backgrounded shell, or a sleep loop inside a agent shell job. The durable
launcher owns the `unity-stack` tmux session, waits for readiness, and verifies
`http://localhost:3000/`.

Do not run isolated commands against a live stack unless the user explicitly asks
for isolated mode: `npm run dev`, `next dev`, `next build`, `npm run ci`,
`console/scripts/local.sh start`, `orchestra/scripts/local.sh start`, or
`unify/scripts/local.sh start`.

If isolated mode is explicitly requested, use the relevant override env var and
explain which full-stack guarantees are being bypassed.

## Isolated Orchestra and Cursor process reaping (macOS)

Prefer the durable full stack above. When isolated Orchestra is required
(`orchestra/scripts/local.sh start`, or `parallel_run.sh` bringing Orchestra up):

- **macOS has no `setsid`.** `local.sh` falls back to `bash -c … &` + `disown`.
  `disown` does **not** create a new process group — Orchestra stays in the
  agent shell’s PGID. When that shell’s process group is torn down, Orchestra
  dies and tests mid-flight see `Connection refused` on `127.0.0.1:8000`.
- **Never** treat a one-shot agent shell `local.sh start` as durable. Start
  Orchestra in a long-lived human terminal, or hold a watcher shell on the
  server pid for the whole session. `parallel_run` only keeps Orchestra alive
  for as long as *that* runner’s process group survives — and only if it
  started Orchestra itself rather than reusing an instance from a short-lived
  prior shell.
- Mid-run `Connection refused` to `:8000` is infra death until proven otherwise.
  Check `orchestra/scripts/local.sh status` / `curl` before diagnosing product
  or LLM failures.
- `local.sh stop` ends with `pkill -9 -f -- "-m orchestra"`, which kills the
  **shared** instance for every agent on the machine. Do not stop/restart
  Orchestra from one agent session while another’s tests are using it.

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

# Orchestra / DataManager: Server-Side Queries First

Orchestra is a Postgres-backed query engine. **DataManager** (and brain store
adapters that wrap it) is the public surface for table I/O. Both surfaces expose
the `filter` keyword, metrics, and filtered updates. Coding agents
(one-off scripts **and** production ticks) must use that surface.
Downloading a table into Python and filtering locally is almost always wrong.

In **brain**, UniSDK is not a parallel authoring API for Orchestra rows —
see `brain/.agents/rules/brain-datamanager-only.md`. Actor plans use
`primitives.data.*` (DataManager). UniSDK remains an implementation detail
under DataManager (and a few non-table exceptions listed in that rule).

## Invariant

For any lookup, count, membership check, or bulk mutation against an Orchestra
context (especially tables at 10⁴+ rows such as GTM `Prospects`):

1. **Prefer a server-side filter** — `DataManager.filter` / store
   `find_many` / `find_one` / `find_by_field` with `filter`.
2. **Prefer server-side aggregation** — `DataManager.reduce(metric="count"|…)`,
   store `count_rows`.
3. **Prefer filtered / batched writes** — `update_rows` / `update_by_ids` /
   store updates on ids from `filter(..., include_ids=True)`; bulk insert via
   `insert_rows` / `parallel_create_logs` / `ingest`. Do not invent a
   full-table client scan to decide which rows to touch.

Equality on a typed field (e.g. `best_email == "..."`) is a sub-second
server query even on ~10⁵-row contexts. A client `iter_all` + Python `if`
is minutes of HTTP pagination and will silently throttle any tick that
calls it in a hot path.

## Required patterns

```python
# Lookup by field (server-side) — brain store adapter
rows = store.find_many(
    "Prospects",
    filter=f'best_email == "{email}"',
    limit=3,  # existence / small-cardinality checks: use a tiny limit
)

# Or DataManager directly (absolute Teams/ paths are fine)
from unify.data_manager.data_manager import DataManager
dm = DataManager()
rows = dm.filter(
    "Teams/11/Data/GTM/Prospects",
    filter=f'best_email == "{email}"',
    limit=3,
    include_ids=True,  # when a later update_by_ids is needed
)

# Counts — never download to len()
n = store.count_rows("Prospects", filter='enrich_status == "enriched"')
# or: dm.reduce(path, metric="count", columns="<any indexed col>", filter=...)
```

House examples in brain: `brain/gtm/outbound/enrollments.py`,
`brain/gtm/stargazer/enrich.py` (`_sync_email_shared_2x_flags`),
`brain.gtm.store.DataManagerGTMStore.find_by_field`. Expanded recipes:
`brain/docs/operations/orchestra-data-access.md`.

## Hard refuse (anti-patterns)

Do **not** ship or land one-off scripts that:

- Call `iter_all` / paginate with **no** (or vacuous) filter, then
  compare fields in Python (`if row["best_email"] == email`)
- Pull an entire large context to compute a count, distinct set, or "does
  any row match?"
- Nest a full-table scan inside a per-row hot loop (enrich, draft, poll)
- Reach for raw `unisdk.get_logs` / `create_logs` for Brain/Assistants
  domain tables when DataManager already covers the need

`iter_all(..., filter=...)` is acceptable only when you truly need
**every** matching row and the filter is selective enough that the result
set is bounded. Unfiltered `iter_all` on large tables requires an explicit
operator rationale in the change description.

## Before you write a scan

Ask: "Can Orchestra answer this with DataManager `filter` / `reduce` / a
small `limit`?" If yes, do that. If a capability is missing, extend
DataManager in unify — do not default to downloading the table via UniSDK.

The frozen derived-template persistence schema still uses the nested
`"filter_expr"` key. That stored key is not a public DataManager or brain store
keyword and must not be renamed.

## Related

- Auth / tenant key pitfalls: `orchestra-admin-vs-user-api-access.md`
- Brain DataManager-only invariant: `brain/.agents/rules/brain-datamanager-only.md`
- Brain env, bulk-write footguns, `limit=1000` pagination:
  `brain/.agents/rules/brain-orchestra-staging.md`
- Playbook with copy-paste recipes:
  `brain/docs/operations/orchestra-data-access.md`

# Infra command safety

Two traps here fail *silently* — wrong output rather than an error — so they
cannot be discovered by trying.

**`gcloud` is regional and the default lies.** Most resources are regional or
zonal, and several `gcloud` surfaces default to `global` and return stale or
empty output **without erroring**. Cloud Build is the worst: with no
`--region`, `gcloud builds …` hits `global`, where the main project looks
empty and the saas project hides every `orchestra`/`console` build. Reading
that as "the build never ran" or "the service doesn't exist" is a recurring
mistake. Pass the location flag explicitly — the estate is `us-central1` —
and suspect a wrong location before a wrong project.

**Some live resources keep legacy `droid-*` / `unity-*` names on purpose.**
The platform was renamed additively, so code targets those names deliberately.
A name mismatch fails at *runtime* (404/401/empty config), not at build, and
has caused silent production outages. When something infra-related 404s or
"doesn't exist", suspect a legacy name before changing the code constant.

Full topology — projects, regions, where things run, and the exhaustive
legacy-name list — is in
[`.agents/global-rules/situational/deployed-system-topology.md`](.agents/global-rules/situational/deployed-system-topology.md).
Read it before any non-trivial infra work.

# Deployed System Topology (shared context)

This is broad orientation so agents in **any** repo know the shape of the deployed
system without re-exploring it every time. The **authoritative, exhaustive source of
truth** (every resource name, secret, CI trigger, and rename loose-end) is the
**`unify-deploy` repo root `README.md`**. Read that before deep infra work; do not
rediscover it from scratch.

## Repos

`unify` (runtime/brain, public), `unify-deploy` (private: hosted comms app + adapters,
assistant VM/tunnel infra, self-host stack, client overlay, prod CI/CD), `orchestra`
(backend API + Postgres, hosted), `console` (Next.js UI, hosted), `unisdk` (Python SDK,
public), `unillm` (LLM layer, public). Dependency `magnitude` is consumed at branch
`unity-modifications`. All repos: `main` = prod, `staging` = dev; promote `staging`→`main`.

## GCP projects (4)

| Project ID | Role |
|---|---|
| `responsive-city-458413-a2` (display "Unity LiveKit") | Main runtime: GKE cluster `unity`, Cloud Run `droid-comms-app`/`droid-adapters` (+`-staging`), Pub/Sub fleet, most buckets, tunnel servers, Artifact Registry |
| `unity-assistant-vms` | Assistant desktop VM pool: pool images/families, pool VMs, static IPs, per-assistant archives |
| `saas-368716` ("SaaS") | **Orchestra + Console + landing page** (Cloud Run) and **Cloud SQL** Postgres (`prod-ssd-usc1`/`staging-ssd-usc1`, us-central1) |
| `unify-dns-server` | Public DNS zone `unifyai` → `unify.ai` (incl. `vm.unify.ai`, `tunnel.unify.ai`) |

## gcloud regions (don't trust the defaults)

Almost every resource is **regional/zonal**, and several `gcloud` surfaces **default to the wrong location and return stale/empty output without erroring** — misreading that ("the build never ran", "service doesn't exist") is a recurring mistake. **Pass the location flag explicitly; suspect a wrong/`global` location before suspecting a wrong project.**

- **Cloud Build is the #1 trap — it's regional and the `global` default lies.** All triggers + builds for **both** `responsive-city-458413-a2` and `saas-368716` are in **`us-central1`**. With no `--region`, `gcloud builds …` hits `global`, where `responsive-city-458413-a2` is **empty/months-stale** and `saas-368716` shows **only `landing-page`** (hiding all `orchestra`/`console` builds). Always: `gcloud builds {list,describe,log,triggers list,triggers run} --region=us-central1`.
- **GKE cluster `unity`**, Cloud Run comms/adapters, tunnel/pool VMs → **`us-central1`** (VM zones `-a`/`-f`).
- **saas Cloud Run** `orchestra`/`landing-page`/Console (prod + staging) → **`us-central1`**. **Cloud SQL** `prod-ssd-usc1`/`staging-ssd-usc1` → **`us-central1`**. (Consolidated from europe-west1/west3 in July 2026; the entire estate is now `us-central1`.)
- **Secret Manager** + **Cloud DNS** → global (no region flag; `--project` only).
- Org GitHub var `GCP_LOCATION=us-central1` is the saas Cloud Run default; the whole estate now shares `us-central1`.

Full per-surface table + exact service names: `unify-deploy` README §3 "gcloud region/zone cheat-sheet".

## Where things run

- **Assistant runtime** = `unity` container as on-demand GKE Jobs (label `app=droid`) on cluster `unity`. Idle→live via Pub/Sub `droid-startup[-staging]` / `droid-{assistant_id}[-staging]`. 7-min inactivity timeout; jobs retained for logs; `job-watcher` (kopf) does crash-safe cleanup.
- **Hosted comms**: adapters (inbound webhooks) + comms app (outbound + infra control plane `/infra/*`) on Cloud Run; the comms-app image also runs the GKE `assistant-session-controller`/`-pool-controller`.
- **Assistant desktops**: pooled Ubuntu/Windows VMs in `unity-assistant-vms`; runtime syncs `~/Unity/Local` over rclone SFTP (user `unityuser`, port 2222); cross-session home persisted to `gs://droid-assistant-archives/{id}.tar.gz`; optional rathole tunnel relay (`unity-tunnel-server`) for user machines.
- **Backend/UI/DB** all in `saas-368716`. Orchestra at `https://api.unify.ai/v0`.
- **Fleet audit** (`AssistantJobs`): Orchestra `is_system` project; writes via
  comms `/infra/assistant-jobs/*` (pod `UNIFY_KEY`) or Console hosted reads with
  `ORCHESTRA_ADMIN_KEY` as `__system__`. Never a Workspace `User` API key.

## Legacy Resource Naming Reality (critical)

The platform has gone through additive renames rather than a single in-place resource cutover.
Consequence: some live GCP/GitHub resources still intentionally use legacy `droid-*` or
`unity-*` names. A name mismatch
fails at *runtime* (404/401/empty config), not at build — this has caused silent prod outages.

**Immutable / permanently `unity` (do NOT try to "fix" in code — code targets these on purpose):**
project IDs `unity-assistant-vms` & `responsive-city-458413-a2`, all service-account emails
(`pool-vm-sa@unity-assistant-vms`, `comm-sa@responsive-city-458413-a2`), and GKE cluster `unity`
(`DROID_GKE_CLUSTER_NAME` default `unity`).

**Canonical names that commonly confuse (use these, verify before assuming):**
- GKE cluster: `unity`; VM/image project: `unity-assistant-vms`.
- Tunnel: VM `unity-tunnel-server`, bucket `unity-tunnel-config` (there is **no** `droid-tunnel-config`).
- Desktop pool: Ubuntu migrated to `droid-pool-ubuntu-*` (image family `droid-pool-ubuntu-vm`); **Windows still `unity-pool-windows-*`**.
- Archive bucket: `droid-assistant-archives` (live); `unity-assistant-archives` is legacy rollback.
- Data buckets (recordings/logs/artifacts) and ~84% of Pub/Sub topics/subs are still `unity-*`.
- CI: GitHub org secrets are still `UNITY_ADAPTERS_URL`/`UNITY_COMMS_URL` while workflows read `DROID_*` (so they can resolve empty).
- Deliberate legacy-named identifiers (not typos): `UnitySystemEvent` gateway envelope (unity↔console wire contract), `UnityTests` default test project, `unity-user-filesync` SSH key comment, `WaitingForUnity` state labels, `magnitude@unity-modifications`.

When something infra-related "doesn't exist" or 404s/401s, suspect a legacy resource-name mismatch
and confirm the real resource name against the `unify-deploy` README (or `gcloud`/`gh`) rather
than trusting the code constant.

# Fleet audit auth (AssistantJobs)

Platform fleet audit (`AssistantJobs` / `startup_events` / Console liveview
discovery) is authenticated as Orchestra **`__system__`** via
`ORCHESTRA_ADMIN_KEY` against a **`Project.is_system`** project.

## Hard rules

- **Never** create or reuse a Workspace/Console `User` (e.g. `shared@unify.ai`,
  personal engineer accounts) as the principal for fleet/infra audit auth.
  `ApiKey.user_id` CASCADE-deletes with the user — a rational account purge
  will silently break desktop connect / liveview.
- **Never** mount `ORCHESTRA_ADMIN_KEY` on Unity assistant Job pods. Pods write
  through ownership-scoped `/infra/assistant-jobs/*` with their own `UNIFY_KEY`.
- **Never** reintroduce `SHARED_UNIFY_KEY` for AssistantJobs. That secret is
  retired; scripts and Console hosted reads use `ORCHESTRA_ADMIN_KEY`.

## When purging staging/prod accounts

- Delete unused human users freely.
- Do **not** delete or rotate keys that look “shared” without checking whether
  they back a system project (they must not — if they do, migrate to
  `__system__` first).
- Prefer verifying AssistantJobs with
  `deploy/scripts/dev/verify_assistant_jobs_system.py` after Orchestra or
  secret changes.

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

# Local Stack Logs: Where To Look First

When the user says something like *"we just did a local deployment and X happened,
check the logs to investigate"*, the logs almost always already exist on disk. Do
**not** re-explore the filesystem from scratch — go straight to the locations below.

## 1. Central source of truth: `$UNIFY_REPO_PATH/logs/`

Default `~/unify/logs/`. Stack scripts may still export the legacy alias
`UNITY_REPO_PATH`; both refer to the same checkout. A local deployment aggregates
**every** repo's logs here — including Orchestra, which runs as a separate process.
The exact paths are set in `unify-deploy/selfhost/self_host_env.sh` (search
`*_LOG_DIR`); confirm the live values with `stack.sh status`.

| Dir | Env var | Contents |
|---|---|---|
| `logs/unillm/` | `UNILLM_LOG_DIR` | Raw LLM request/response, one `.txt` per call — system/user prompts, tool args, `reasoning_content`, model. This is **"what the model actually produced"**. |
| `logs/unisdk/` | `UNISDK_LOG_DIR` | UniSDK ↔ Orchestra HTTP traces (JSON per request). |
| `logs/orchestra/` | `ORCHESTRA_LOG_DIR` | Orchestra server-side per-request traces. |
| `logs/unify/` | `UNITY_LOG_DIR` | Unify runtime file logs (env var name is legacy). |
| `logs/all/` | `*_OTEL_LOG_DIR` | **Combined cross-repo OTel traces** — one `{trace_id}.jsonl` per request, with unify + unisdk + unillm (+ orchestra) spans stacked together. Use this for the end-to-end story of a single request. |
| `logs/pytest/`, `logs/ci/` | — | Test runs / downloaded-CI logs. |

Deep reference (formats, env vars, examples): `<unify>/logs/README.md` (also present
in `unisdk/logs/README.md` and `unillm/logs/README.md`).

## 2. CRITICAL: these dirs are gitignored AND cursorignored

`unify/.gitignore` has `logs/*`; `unify/.cursorignore` has `logs/` and `logs/**`.
Consequence — this is the usual reason an agent "can't find the logs":

- The built-in **Read / Grep / Glob tools return nothing**, "permission denied", or
  "filtered out by .cursorignore" for anything under `logs/`.
- Plain `rg` / `grep` also **skip** these dirs (they respect `.gitignore`).

Always inspect log dirs via the **Shell tool with ignore-bypass**, and read
individual files through the shell (not the Read tool):

```bash
rg -uu -n "pattern" ~/unify/logs/unillm   # -uu = --no-ignore --hidden
rg -uu -n . ~/unify/logs/all/<trace_id>.jsonl
```

## 3. Operational logs that live OUTSIDE the `logs/` tree

- `~/.unity/service.log` — the self-host **stack supervisor**: startup, Orchestra
  boot, gateway restarts, and the CM's own log path. Location is printed by
  `stack.sh status`. (Note: may contain a one-off DB dump near a reset.)
- `/tmp/unity-local.log` — the **ConversationManager event "story"**: notifications,
  guide/speak decisions, tool calls — the human-readable narrative of a live
  conversation. Best first read for "what happened in this chat/call".
- `~/.unity/comms-bridge.log` — inbound email / SMS / WhatsApp polling.
- `~/.unity/call-tunnel.log` — cloudflared tunnel used for local phone/WhatsApp
  call webhooks. LiveKit media itself is in LiveKit Cloud for source-stack runs.

## 4. Ground truth that is NOT a file: Orchestra `Transcripts` context

What was actually **spoken / sent / received** on calls and channels lives in
Orchestra's Postgres, not in a file log. When a file log shows the *intended* text
but you need the *downstream reality* (e.g. the TTS rendering vs. the LLM text),
query the `Transcripts` context (and `Contacts`, `Tasks`, …) via the UniSDK logs API
or Console:

```bash
curl -s --get "http://127.0.0.1:8000/v0/logs" \
  --data-urlencode "project_name=Assistants" \
  --data-urlencode "context=<userId>/<assistantId>/Transcripts" \
  --data-urlencode "limit=200" \
  -H "Authorization: Bearer $KEY"
```

Local keys: the coordinator/owner API key is in `~/.unity/coordinator-runtime.json`;
`userId` is in `~/.unity/self-host-owner.json`. `unify_meet` rows are call
utterances (`sender_id` identifies the speaker).

## Quick start

1. `bash ~/unify-deploy/selfhost/stack.sh status` — running services + log paths.
2. `rg -uu` into `~/unify/logs/{all,unillm,unisdk,orchestra,unify}` for the request.
3. For one end-to-end request, open the matching `logs/all/{trace_id}.jsonl`.
4. For the conversation narrative, read `/tmp/unity-local.log`.
5. For what was truly spoken/received, query the Orchestra `Transcripts` context.

# Orchestra Admin vs User API Access

Orchestra (`api.unify.ai/v0` prod, `api.staging.internal.saas.unify.ai/v0` staging) has **two distinct auth paths** (`orchestra/web/api/dependencies.py`). Confusing them wastes hours.

## The two dependencies

- **`auth_api_key`** — looks the Bearer token up as a **user API key** and sets `request.state.user_id`. All **data** endpoints use it (`/logs` get/update/`atomic_field_update`, contexts, dashboards, etc.). Results are **scoped to that key's owner**. There is **no admin bypass** here.
- **`auth_admin_key`** — matches the Bearer against the server's `ORCHESTRA_ADMIN_KEY` (`secrets.compare_digest`), a Cloud Scheduler OIDC token, or an `AdminUser`'s key. Only the **`/admin/*`** routers (registered with `ADMIN_AUTH`) use it. It **gates operations; it does not grant a data scope.**

### Consequences (do not relearn these the hard way)
- `ORCHESTRA_ADMIN_KEY` on a data endpoint → **`401 {"detail":"Invalid API key"}`** (because `/logs` only does user-key lookup). This is expected, not a broken key.
- Even an **admin user's own** `UNIFY_KEY` is data-scoped: it returns `0` for another tenant's contexts. Admin status does not widen `/logs` results.
- The live `ORCHESTRA_ADMIN_KEY` is the **GCP secret** in `saas-368716` (prod) — repo `.env` copies may be stale. Staging uses a different value. Fetch with `gcloud secrets versions access latest --secret=ORCHESTRA_ADMIN_KEY --project=saas-368716`.

## How to read/write a specific tenant's data smoothly

Use the admin API to fetch the target's **own** API key, then use that key on the normal data endpoints:

1. **Enumerate + get keys** (admin key): `GET /admin/assistant` returns every assistant including its `api_key`, `agent_id`, `user_id` (also `GET /admin/assistant/{id}`, `/admin/assistant/user/{user_id}`).
   ```bash
   curl -s --get "$ORCHESTRA_URL/admin/assistant" -H "Authorization: Bearer $ORCHESTRA_ADMIN_KEY"
   ```
2. **Use the assistant's `api_key`** as the Bearer on the data API — now scoped to that tenant:
   ```python
   import unify
   logs = unify.get_logs(project="Assistants", filter="'x' in content", api_key=assistant_key)
   unify.update_logs(logs=log_id, entries={"content": new}, context=ctx, api_key=assistant_key)
   ```

A cross-tenant migration = loop assistants from `/admin/assistant`, then operate per-assistant with each key (no superuser data key exists). `gcloud` Cloud SQL (`prod-ssd`, `saas-368716`) is the direct-DB fallback for bulk passes.

# OAuth Scopes: Mirrored Between Communication and Orchestra

## Context
OAuth scope catalogs (Google and Microsoft provider scopes, feature bundles, and the `build_scope_string` resolver) are intentionally duplicated in two places:

- **Communication**: `common/scopes.py`
- **Orchestra**: `web/api/assistant/scopes.py`

Both services need this data at runtime (Communication when initiating OAuth flows and talking to providers; Orchestra when storing assistant scope grants and serving them to Console). Because the contents are small, static, and change rarely, we deliberately avoid adding a cross-service HTTP round-trip and instead keep two copies in sync.

## Critical Rules

### 1. Any Scope Change Must Be Mirrored
When modifying **any** of the following in either repo, the identical change MUST be made in the sibling file in the other repo in the same changeset:

- `GOOGLE_SCOPE_BUNDLES` / `MICROSOFT_SCOPE_BUNDLES`
- `GOOGLE_BASE_SCOPES` / `MICROSOFT_BASE_SCOPES`
- The `build_scope_string` function signature or behavior
- Any new provider added to `_BUNDLES` / `_BASE`

This applies to additions, removals, renames, and reorderings.

### 2. Do Not "Fix" the Duplication
Do not attempt to eliminate the duplication by:
- Having Communication fetch scopes from Orchestra over HTTP
- Having Orchestra fetch scopes from Communication
- Extracting the file into a shared package

The duplication is a conscious trade-off. If you believe the trade-off should be revisited, raise it with the user first.

### 3. Verification Workflow
When asked to add or modify a scope in one repo:
1. Make the change in the current repo.
2. Locate the sibling file in the other repo (paths above).
3. Apply the matching change there.
4. If the other repo is not checked out locally, surface this clearly to the user and list the exact edits required so they can apply them.

### 4. Keep the Cross-Reference Comment Accurate
The docstring at the top of each `scopes.py` points at its sibling. If either file moves, update both docstrings.

# TaskScheduler surgery (Tasks rows)

Agents frequently break recurring jobs by hand-editing `Teams/*/Tasks`
(or assistant-scoped `…/Tasks`) via DataManager / UniSDK. Follow this rule for
**any** TaskScheduler ops across brain, unify, and orchestra.

## Identity model

- **`Tasks`** is definition-only: **one row per `task_id`**, the whole series.
  `unique_keys={"task_id": "int"}`, `auto_counting={"task_id": None}`
  (`unify/task_scheduler/task_scheduler.py`).
- **`Tasks/Executions`** holds the runs: one row per wake/attempt, keyed by
  `run_key` (the idempotency key). Occurrence and attempt are the same row.
  Recurrence creates the *next* Execution when the current one **starts** — it
  does **not** clone the Tasks row.
- **`instance_id` is vestigial.** It is a legacy occurrence counter kept only so
  pre-migration rows still read back. It is not unique, not auto-counted, and
  not part of identity; new rows get `0`. Treat any non-zero `instance_id` as a
  pre-migration artefact, not as a thing to allocate, increment, or reason about.
- Concurrency is normal now: several Executions can be in flight against one
  definition, so a definition sitting in `active` is not a zombie by itself.

## Hard refuse

- Do **not** set or change `task_id` on an existing row (Orchestra rejects
  writes to auto-counted unique identity fields).
- Do **not** resurrect `cancelled` / `failed` / `completed` rows by flipping
  them back to `scheduled` (or rewriting their `schedule`). Same for terminal
  Executions.
- Do **not** invent a Tasks row by hand with an explicit `task_id` — go through
  TaskScheduler APIs and let Orchestra allocate it.
- Do **not** write `instance_id` at all. It buys nothing on the current model,
  and a non-zero value pushes reads down the legacy compat path (see below).

## Allowed ops

| Goal | How |
|---|---|
| Arm a planted custom task | Set **`enabled=True`** on the definition row (the single `task_id` row, `custom_key` set). TaskScheduler schedules the next Execution. |
| Pause | `enabled=False` on the definition row; optionally cancel open Executions. |
| One-off catch-up / run now | `POST /v0/tasks/{task_id}/trigger` (`trigger_task(task_id=…)` in `typed_tasks_client`). It takes no `instance_id`. |
| Change cadence | Edit `tasks.jsonl` + deploy reconcile, or TaskScheduler APIs that own the schedule — not ad-hoc DM patches. |
| Stuck `active` zombie | `POST /admin/task-source/release-active` with the source task log id. |

## Legacy compat path

`_get_task_row(task_id, instance_id)` addresses by `task_id` alone when
`instance_id == 0`, and only falls back to the old
`task_id AND instance_id` filter when it is non-zero
(`unify/task_scheduler/task_scheduler.py`, the `if instance_id != 0:` branch).
That fallback exists to read surviving pre-migration rows. Do not lean on it
for new work, and do not pass a non-zero `instance_id` to make a lookup
"more specific" — on a post-migration task it just fails to match.

If a `task_id` genuinely resolves to more than one Tasks row, that is a
pre-migration remnant (or a bad hand-write), not a counter desync. Delete the
stale duplicate, or leave it terminal and do not re-trigger until the health
check is clean.

## Break-glass

Only with an explicit operator rationale: fail an `active` zombie via
`POST /admin/task-source/release-active`, then clean up **extra** open
Executions so one next wake remains.

Ops detail: brain `docs/operations/scheduled-jobs.md` (re-arm / disable /
catch-up). Health check: `python3 -m scripts.tasks_health_check`.

This rule standardizes how we add temporary debug logging during failing tests and how we clean it up afterwards. ALWAYS use this process in agent sessions WHENEVER A TEST FAILS. This is the ONLY permitted way to address failing tests.

1) Always start with hardcoded, unconditional debug logs
- Add logs immediately, without flags or guards. Do not gate behind environment variables or configuration.
- Use **only** the `CURSOR_DEBUG_LOG` function. No other logging method is permitted.
- **Finding the function**: Search for it with `rg "CURSOR_DEBUG_LOG"` to locate the utility in your project, then import and use it.
  - **Python**: `from <module> import CURSOR_DEBUG_LOG` then `CURSOR_DEBUG_LOG("message", variable)`
  - **JavaScript/TypeScript**: `import { CURSOR_DEBUG_LOG } from "<module>"` then `CURSOR_DEBUG_LOG("message", { variable })`
- Behavior: Prints an entry to stderr/stdout, making it easy to correlate with test runs.

2) Python-specific import discipline
- **Self-contained imports**: Each debug snippet must include ALL its own imports inline (e.g., `import json as _json; import os as _os;`). Never rely on the file's existing imports.
- **Prefixed names**: Use underscore-prefixed aliases (`_json`, `_os`, `_pid`) to avoid shadowing.
- **Region markers**: Wrap in `# #region agent log` / `# #endregion` for easy identification and removal.
- This prevents `NameError` crashes when debug snippets reference modules that aren't imported at that location.

3) Investigation workflow
- Step A: Add targeted debug calls around suspected code paths.
- Step B: Re-run the failing test(s) and inspect the new logs.
- Step C: If you are not 100% certain of the root cause, add more debug entries and repeat.
- Step D: Only when you are 100% confident of the cause, implement a direct fix (with or without keeping some logs briefly for confirmation).
- Step E: The user may repeatedly re-run tests and paste logs; continue iterating until the issue is definitively fixed.

4) Cleanup policy
- After the fix is confirmed, remove all temporary logging.
- Grep to find every occurrence:
  - ripgrep: `rg -n "CURSOR_DEBUG_LOG" -S`
  - grep:    `grep -Rin "CURSOR_DEBUG_LOG" .`
- Delete each call site (and any now-unused imports) before finalizing the fix.

5) Alignment with workspace rules
- No fast paths or heuristics: Logging should not add conditional shortcuts; it merely reports state unconditionally.
- No exception-handling shields: Do not add defensive exception handling (try/catch, try/except) around the logs. Keep failures visible.
- No test details in production prompts: Temporary logs must not leak test-specific information into production prompts or docstrings.
- Rapid evolution: This logging is temporary by design; remove it once the issue is resolved—do not preserve backward compatibility.

6) Intent and scope
- This logging exists solely for interactive debugging in agent sessions.
- The function name `CURSOR_DEBUG_LOG` is intentionally unique and grep-friendly to ensure quick cleanup on request.
