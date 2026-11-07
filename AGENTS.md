# Agent instructions

Use Simplified Technical English in repository text and code comments. Use one idea per sentence. Use LF line endings.

Use the Agent Skills standard. Keep one source package per skill under `skills/`. Keep personal skill folders and names in the `lem-` namespace. Keep instructions and resources portable across compatible agents. Keep skill resources inside the skill package.

Inspect the worktree before changes. Preserve unrelated work. Check the final diff before a commit. Commit, push, and publish releases only when the user requests these actions.

Run `gh skill publish --dry-run` to validate the skills. Use temporary installation directories for verification.

## Markdown

Write prose in normal paragraphs. Keep each paragraph on one source line. Do not insert a line break after each sentence or wrap prose at a fixed column width. Separate paragraphs with a blank line.
