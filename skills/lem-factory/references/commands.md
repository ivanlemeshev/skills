# Helper commands

Use `python3 /absolute/path/to/lem-factory/scripts/factory.py`. The examples use `FACTORY` for that absolute script path and `JOB` for the absolute job directory. These shell variables are examples. Use the host's native argument passing when a shell is unavailable.

## Create

After the user confirms the branch and base, save the request to a UTF-8 file outside the source tree. Then run:

```sh
python3 "$FACTORY" create --repo /path/to/repo --branch feat/example --base main --worktree /path/to/example --request-file /tmp/request.md --confirmed
```

`--confirmed` records an approval already received in chat. It does not grant approval. The helper accepts an existing local branch or remote-tracking branch as the base. It records the resolved commit and creates the new branch from that commit. It never fetches or updates an existing branch. A repeated identical command can recover setup after an interruption. Unexpected existing directories or branches cause a refusal.

The job directory is `/path/to/example.factory/`. The helper disables checkout hooks for worktree creation. Git configuration is passed only to that process. It is not saved to the repository.

## Check configuration

Write `checks.json` in the job directory before the baseline. Use a nonempty JSON array:

```json
[
  {"name": "tests", "argv": ["python3", "-m", "unittest", "discover", "-s", "tests"], "timeout": 600},
  {"name": "build", "argv": ["npm", "run", "build"], "timeout": 600}
]
```

Choose commands from the actual repository. Each command runs in the worktree. Arguments are passed directly without shell interpolation. A timeout is measured in seconds. Output goes to a numbered log under the job's `checks/` directory. The runner uses POSIX process groups. It stops the group on a timeout or interruption. It fails checks that leave background children running. Check commands must not detach into another session. Uncertain process cleanup blocks the job. The commands are repository code. Inspect them for prohibited side effects. The helper is not a sandbox.

```sh
python3 "$FACTORY" check "$JOB"
```

During `baseline` this runs the baseline. If it fails, the job becomes `baseline-blocked`. Stop and ask the user to resolve the failure first. Only after the user confirms resolution:

```sh
python3 "$FACTORY" check "$JOB" --resolved
```

A passing baseline leads to `plan`. The configuration is then frozen. A check exit code of 1 means checks failed. An exit code of 2 means the command was refused or a prerequisite failed. Both require attention.

## Build

Write a nonempty `plan.md` in the job directory. Show its short form in chat. Select `code` and any relevant additional reviewers:

```sh
python3 "$FACTORY" start-build "$JOB" --reviewers code security
```

Supported reviewers are `code`, `security`, and `ui`. `code` is mandatory. Implement the task, then run `check` again. A passing build check leads to `review` and returns its check ID and snapshot ID. A failure leads to `repair` or `blocked` when the repair budget is exhausted.

## Record a review

Reviewers write reports outside the source tree. The orchestrator records them:

```sh
python3 "$FACTORY" review "$JOB" --role code --result pass --mode separate --check-id 2 --snapshot SNAPSHOT_ID --report-file /path/to/code-report.md
```

Use the check ID and snapshot ID from the passing check. The helper refuses stale evidence. It copies the report into the current check run's review directory. Repeat for every required reviewer. The helper waits for all roles before choosing `ready`, `repair`, or `blocked`. A required `incomplete` report blocks the job.

Use `--mode sequential` when the same agent performed the review pass. A source edit, plan edit, changed reviewer selection, edited report, or new check run invalidates previous review evidence. Each repair requires full checks and a fresh set of reviews.

## Status and blockers

```sh
python3 "$FACTORY" status "$JOB"
python3 "$FACTORY" block "$JOB" --reason "Required UI preview is unavailable."
```

`status` is read-only. It returns the recorded stage, current snapshot, saved evidence, and `can_handoff`. A successful handoff requires `can_handoff: true`. `stage: ready` alone is insufficient when files or reports have changed. Use `check` to refresh stale evidence unless a blocker requires the user's intervention.

If a helper command is refused, inspect the cause and stop when it requires user input. Never edit `job.json` to force progress. A blocked repair budget cannot be reset by resuming in another session.

After the user confirms that a missing prerequisite or another resolvable blocker is fixed:

```sh
python3 "$FACTORY" resume "$JOB" --resolved
```

This command preserves the repair count. It requires fresh checks and reviews after a build or review blocker. It cannot reopen an exhausted repair budget. Baseline failures use `check --resolved` instead.

## Files and recovery

```text
example/                         source worktree; changes stay uncommitted
example.factory/
  job.json                       helper-owned state
  request.md                     saved chat request
  checks.json                    baseline check commands
  plan.md                        scope and acceptance criteria
  checks/run-0001/                command logs and result.json
  reviews/run-0002/               recorded role reports
  handoff.md                     final or incomplete report
```

State writes use atomic replacement and a local directory lock. Checks record their start before execution. A new session can rerun an interrupted check. The helper verifies that the expected branch is still checked out, HEAD is still at the base commit, and no staged changes exist. It never repairs Git state.

Snapshots include tracked and non-ignored untracked files. Ignored generated files are outside this evidence. If ignored files are part of the requested implementation, stop and ask how to include and validate them. The helper hashes initialized submodule contents as well. It does not initialize submodules or modify their Git state.

The helper records evidence and legal workflow transitions. Agents still decide whether checks cover the task and whether a review is sound. This package does not install host policies or provide technical enforcement for arbitrary shell commands.
