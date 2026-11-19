# Skills

Reusable skills in the [Agent Skills format](https://agentskills.io/specification). Each skill has one source package for compatible agents.

## Available skills

| Skill        | Purpose                                                           | Requirements                                     |
| ------------ | ----------------------------------------------------------------- | ------------------------------------------------ |
| `lem-review` | Review pull requests, branches, staged changes, or local changes. | Git. GitHub CLI for GitHub pull request reviews. |

## Install

Use GitHub CLI with `gh skill` support. Replace `SKILL_NAME` with a name from the table above.

For Codex:

```sh
gh skill install ivanlemeshev/skills SKILL_NAME --agent codex --scope user
```

For Claude Code:

```sh
gh skill install ivanlemeshev/skills SKILL_NAME --agent claude-code --scope user
```

Both commands install the selected skill package. They work in Bash and PowerShell. GitHub CLI selects the latest release, or the default branch when no release exists. Add `--pin <tag-or-commit>` to select a specific version. Use the appropriate `--agent` value to install for another supported agent.

Invoke the installed skill by its name. Codex uses `$SKILL_NAME`. Claude Code uses `/SKILL_NAME`. Replace `SKILL_NAME` with the installed skill name. Pass the input that the selected skill needs. Invocation settings depend on the agent.

## Add a skill

```text
skills/
  lem-example/
    SKILL.md
    references/
      guide.md
```

Add each new skill under `skills/lem-<name>/`. Use the same name in the folder and the `SKILL.md` frontmatter. The frontmatter requires `name` and `description`. Keep instructions and resources portable. Add references, scripts, or assets only when the skill needs them. Add the skill to the table above.

## Validate

This command checks the skill format without publishing a release.

```sh
gh skill publish --dry-run
```

Use an empty temporary directory for a local installation check:

```sh
gh skill install . SKILL_NAME --from-local --agent codex --dir /tmp/skills-check
```

Repeat with `--agent claude-code` and a different temporary directory.

## Release

Release versions come from Git tags. The latest `vX.Y.Z` tag is the base for the next release.

Update the skills and README. Run the release task from `main`:

```sh
mise run release -- patch
```

Use `minor` or `major` instead of `patch` when needed. The task commits and pushes `main`, then creates and pushes the next version tag. GitHub Actions validates the tag with mise and publishes the GitHub release. Run the local check before pushing:

```sh
mise run check
```

## License

[MIT](LICENSE).
