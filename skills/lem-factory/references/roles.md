# Role contracts

## Shared context

Give every worker the request, plan, repository instructions, absolute worktree and job paths, saved base commit, role, and current stage. Give reviewers the passing check ID and snapshot ID. Give a repair worker the failing logs and all review reports from that round. Use host-native worker tools. Do not prescribe model names, tool names, hooks, private transcript formats, or another product's CLI.

Repeat these authority limits in every delegation: edit source only in the designated worktree; preserve unrelated work; use Git and GitHub only for read operations; leave changes uncommitted; perform no branch or worktree creation; install dependencies only within the project; ask before system installation or external service changes. Workers must not edit `job.json`, `checks.json`, or another role's report. Only the orchestrator runs the state helper.

Role instructions are shared references. They do not require host-specific agent files. Workers may use an applicable installed skill if it is available and respects this contract. The factory must also work without that skill.

## Planner

Inspect relevant code and repository instructions. Turn the request into acceptance criteria and a small implementation plan. Identify project checks and the review surfaces. Ask about missing decisions that materially affect behavior. Keep unrelated improvements outside the plan. The orchestrator writes `plan.md` and shows its short form in chat.

## Builder

Implement the acceptance criteria in the worktree. Read complete affected files and relevant interfaces before changes. Follow repository conventions. Add meaningful test coverage for changed behavior when needed. Keep existing checks intact. Return changed paths, validation performed, and blockers. During repair, address every actionable finding and rerun the helper's full checks through the orchestrator.

## Code reviewer

Remain read-only except for the assigned report. Inspect tracked changes against the saved base commit with `git diff --no-ext-diff --no-textconv <base-commit> --`. Inspect untracked files with `git ls-files --others --exclude-standard` and read their contents. Never use `git add`, including intent-to-add, to construct the review target.

Check acceptance criteria, correctness, error handling, compatibility, and test coverage. Trace relevant callers and edge cases. Report defects with a concrete trigger, impact, file location, and fix. Do not turn style preferences or unrelated baseline defects into blockers. Check that tests and check configuration were not weakened to obtain a pass.

## Security reviewer

Inspect changed trust boundaries, authorization checks, input handling, secrets, filesystem access, and process invocation. Trace a concrete misuse path before reporting a defect. Inspect dependencies when their changed behavior affects the task. Do not invoke an external scanning service or change external state without authorization.

## UI reviewer

Check affected user flows, interaction states, accessibility, and visual behavior. Inspect the implementation and use available preview or browser tools when the change requires them. Record what was exercised. Do not invent visual evidence. Return `incomplete` if a material required flow cannot be checked.

## Report

Write the report to a unique Markdown file in the job directory. Include the role, check ID, snapshot ID, and review mode (`separate` or `sequential`). Use `pass`, `changes`, or `incomplete` as the result. Give each finding a severity, path and line, triggering condition, impact, and one repair. Include coverage limitations. A pass requires no remaining actionable defect and no material review limitation.

Return a short result and the report path to the orchestrator. Do not advance state or repair code from the review role. The orchestrator records each report with the helper and waits for all required reviewers.
