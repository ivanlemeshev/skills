# Software factory

`lem-factory` completes a software task from chat in a separate Git worktree. It plans, implements, checks, reviews, and repairs the task. It leaves all changes uncommitted for your review. The same package works in Codex, Claude Code, and other compatible agents.

## Requirements

Use Git and Python 3.10 or later. The check runner requires a POSIX environment, such as Linux, macOS, or WSL. The helper uses only the Python standard library. The workflow requires no GitHub queue, GitHub CLI, or provider API. GitHub CLI with `gh skill` support is used for the installation commands below.

## Install

Run the command for your agent:

```sh
gh skill install ivanlemeshev/skills lem-factory --agent codex --scope user
gh skill install ivanlemeshev/skills lem-factory --agent claude-code --scope user
```

To try the skill from a local checkout before publishing, run the command for your agent from the repository root:

```sh
gh skill install . lem-factory --from-local --agent codex --scope user
gh skill install . lem-factory --from-local --agent claude-code --scope user
```

## Use

Start the skill with a task from chat:

```text
Codex:       $lem-factory Add input validation to the import command.
Claude Code: /lem-factory Add input validation to the import command.
```

The factory asks you to confirm a new branch name and base branch before it creates a separate worktree. Branch and worktree creation are its only permitted Git writes. It does not stage, commit, push, merge, or create PRs. The restrictions are workflow instructions. The skill does not install host permission rules.

The factory runs the project's checks before implementation. If the baseline fails, it stops and asks you to resolve the failure first. With a passing baseline, it shows a short plan and proceeds when the request is clear. It asks about decisions that materially affect the result.

The factory uses separate reviewers when the host supports them. Otherwise, it records sequential review passes. Code review is required. Security and UI reviews are added when relevant. The factory allows at most three repair cycles after the initial build. A remaining blocker produces an incomplete handoff.

## Resume and review

Job state and evidence stay in a sibling `<worktree>.factory/` directory. To resume, invoke the skill with that job path:

```text
Codex:       $lem-factory Resume /path/to/example.factory.
Claude Code: /lem-factory Resume /path/to/example.factory.
```

The new session can use either agent. It checks the saved state and current files before continuing. Changed source files invalidate earlier check and review evidence. Keep the worktree and job directory until you finish your review. You decide what to commit or publish.

Read [the workflow](references/workflow.md), [role contracts](references/roles.md), and [helper commands](references/commands.md) for details.

## Validate

Run the helper tests from the repository root:

```sh
python3 -B -m unittest discover -s skills/lem-factory/tests -v
```

The tests use temporary directories and mocked Git operations. They do not write Git state. Run `gh skill publish --dry-run` from the repository root to validate the skill format without publishing.

## License

[MIT](LICENSE).
