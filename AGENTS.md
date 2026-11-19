# AGENTS.md

- Always use ASD-STE100 Simplified Technical English in all comments and documentation.
- Keep each Markdown prose paragraph on one source line. Preserve structural line breaks in lists, tables, and code blocks.
- Format Markdown tables with aligned columns, consistent cell padding, and a header separator row.
- Use `git` and `gh` only for read-only operations. Apply this rule to aliases, scripts, and `gh api` requests.
- Update `README.md` when you add or change a skill.
- After edits, run `mise run format`. Then run `mise run check`.
- When the work is complete and the required checks pass, run `git diff HEAD`. Also inspect untracked files from `git status --short`. Include one commit title that covers all changes in the final response.
