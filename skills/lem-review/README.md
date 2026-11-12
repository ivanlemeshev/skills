# Review changes

`lem-review` reviews pull requests, branches, staged changes, or local changes. It returns findings supported by code evidence. The review stays read-only. The report appears in the agent conversation.

## Requirements

Use Git. GitHub pull request reviews also require an authenticated GitHub CLI. Use a compatible agent, such as Codex or Claude Code. The installation commands below require GitHub CLI with `gh skill` support.

## Install

Run the command for your agent:

```sh
gh skill install ivanlemeshev/skills lem-review --agent codex --scope user
gh skill install ivanlemeshev/skills lem-review --agent claude-code --scope user
```

For a local checkout, run the command for your agent from the repository root:

```sh
gh skill install . lem-review --from-local --agent codex --scope user
gh skill install . lem-review --from-local --agent claude-code --scope user
```

## Use

Invoke the skill with the target to review:

```text
Codex:       $lem-review Review local changes.
Claude Code: /lem-review Review local changes.
```

You can also select a pull request number or URL, a branch comparison, a revision range, or staged changes. For example, ask to review `PR 42`, `feature/auth against release`, or `HEAD~3..HEAD`.

Without a target, the skill reviews local changes when they exist. Otherwise, it uses a confidently detected default branch or upstream. It asks when the target or base is unclear. It does not fetch, switch branches, modify source, or publish a GitHub review.

The report identifies the target, verdict, findings, validation, coverage limitations, and decision. Each finding gives its severity, file location, triggering condition, impact, and one repair. Read [the review method](references/review-method.md) and [examples](references/examples.md) for details.

## Validate

Run `gh skill publish --dry-run` from the repository root to validate the skill format without publishing.

## License

[MIT](LICENSE).
