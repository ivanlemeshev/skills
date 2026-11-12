---
name: lem-factory
description: Complete a software task from chat in a confirmed Git worktree. Plan, implement, check, review, and repair the changes for the user's local review. Use when the user asks to run the software factory or resume a factory job.
license: MIT
---

# Software factory

Complete one chat request in a separate Git worktree. Leave the changes uncommitted for the user. The same package works in Codex, Claude Code, and other compatible agents. Use the current host's tools. Do not require another agent product or a particular model.

Read [references/workflow.md](references/workflow.md) for each job. Read [references/commands.md](references/commands.md) before using the helper. Read [references/roles.md](references/roles.md) before delegation or a review pass.

## Authority

Inspect the repository and its instructions before changes. Preserve unrelated work. Ask the user to confirm the new branch name and the base branch. Show the worktree path in that request. Wait for an answer before creation. Use a local base ref. A remote-tracking ref is acceptable when the user selects it. Record its current commit. Fetching is outside this workflow.

The only permitted Git writes are creation of the confirmed branch and worktree. All other Git and GitHub operations must be read-only. This includes commands invoked by scripts, dependencies, hooks, and delegated agents. Do not stage, commit, fetch, pull, push, merge, rebase, reset, stash, change Git configuration, create PRs, post comments, or remove worktrees. Inspect task commands for such effects before running them. Stop and ask when the task requires an exception. These are workflow instructions. They do not configure or replace host permission controls.

Keep implementation changes inside the confirmed worktree. Keep job state in its sibling `<worktree>.factory/` directory. The helper is the only writer of `job.json`. Never change that file to bypass a refused operation. Keep the branch, worktree, and evidence after the handoff.

Project-local dependency installation and checks are allowed. Ask before system installation or changes to external services. Do not replace the user's task with unrelated maintenance.

## Execution

Use Python 3.10 or later and Git. The check runner requires a POSIX environment, such as Linux, macOS, or WSL. Locate `scripts/factory.py` relative to this installed skill. Use absolute paths for the helper and job directory. If a required tool is missing, stop and ask. No GitHub CLI, provider SDK, or third-party Python package is required by this skill.

1. Capture the request and inspect the target repository. Confirm the branch and base with the user. Create the worktree through the helper.
2. Discover and record the project's real checks. Run them on the baseline before implementation. If any check fails or cannot run, stop and ask the user to resolve the problem first. Do not repair the baseline under the original request.
3. Write a short plan with acceptance criteria, intended changes, checks, and required reviewers. Show it to the user, then proceed when the request is clear. Ask about decisions that materially affect the result.
4. Implement the request. Run checks. A failing check goes to repair before review.
5. Review the exact checked file snapshot. Use a separate code reviewer when the host supports delegation. Add security or UI review when relevant. Otherwise, perform explicit sequential review passes and disclose the limitation. Wait for all required reviewers.
6. Repair findings and repeat checks and reviews. Allow at most three repair cycles after the initial build. Stop with an incomplete handoff if the budget is exhausted or a material blocker remains.
7. Verify current evidence and hand off the worktree. State what changed, what passed, any limitations, and where the user can inspect the files. Leave all Git publication actions to the user.

When resuming, read the saved request, plan, status, and evidence. Reconcile the real worktree before repeating a stage. Never treat an interrupted check or a review of older file contents as current evidence.
