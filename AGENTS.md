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
