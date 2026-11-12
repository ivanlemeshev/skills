# Skills

Reusable skills in the [Agent Skills format](https://agentskills.io/specification). Each skill has one source package for compatible agents.

## Skill packages

Browse [skills/](skills/) for the available packages. Each package has a `README.md` with its purpose, requirements, installation commands, and usage. Its `SKILL.md` contains the agent instructions.

## Install

Use GitHub CLI with `gh skill` support. Replace `SKILL_NAME` with a package name from `skills/`.

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
    README.md
    SKILL.md
    references/
      guide.md
```

Add each new skill under `skills/lem-<name>/`. Use the same name in the folder and the `SKILL.md` frontmatter. The frontmatter requires `name` and `description`. Keep instructions and resources portable. Add references, scripts, or assets only when the skill needs them. Keep skill-specific documentation in the package's `README.md`. Keep the root README limited to repository-wide guidance.

## Validate

Run the helper tests and skill validation with `make check`. The tests use temporary directories. They do not write Git state.

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

This repository uses a `VERSION` file as a versioning convention. The Agent Skills standard does not require this file. Its value matches the release tag: `1.0.0` produces `v1.0.0`.

Update the skills and their documentation. Run this command from `main` with Make, Git, GitHub CLI, and a POSIX shell. Replace `1.0.1` with the new version:

```sh
make release VERSION=1.0.1
```

The command checks the skills, updates `VERSION`, commits all repository changes, pushes `main`, and publishes the release. If you already update `VERSION`, run:

```sh
make release
```

## License

[MIT](LICENSE).
