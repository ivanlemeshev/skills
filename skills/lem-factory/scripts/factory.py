#!/usr/bin/env python3
"""Keep local factory state and evidence without publishing changes."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


SCHEMA = 1
MAX_REPAIRS = 3
ROLES = {"code", "security", "ui"}
READ_COMMANDS = {"rev-parse", "symbolic-ref", "diff", "ls-files", "check-ref-format"}


class Refusal(Exception):
    """An operation needs correction or user intervention."""


class CleanupFailure(Refusal):
    """A check process needs manual cleanup before work can continue."""


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def git_env():
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def read_git(repo, *args):
    if not args or args[0] not in READ_COMMANDS:
        raise Refusal("The helper only permits declared read-only Git queries.")
    result = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-C", str(repo), *args],
        env=git_env(), capture_output=True, text=True, encoding="utf-8",
        errors="surrogateescape", check=False,
    )
    if result.returncode:
        raise Refusal(result.stderr.strip() or "A read-only Git query failed.")
    return result.stdout


def atomic_json(path, value):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix=".state-", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2, ensure_ascii=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


@contextmanager
def locked(job):
    lock = job / ".lock"
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise Refusal("The job is locked. Check for an active or interrupted helper.") from error
    try:
        yield
    finally:
        lock.rmdir()


def save(job, state):
    state["updated_at"] = now()
    atomic_json(job / "job.json", state)


def load(job):
    state = json.loads((job / "job.json").read_text(encoding="utf-8"))
    if state.get("schema") != SCHEMA:
        raise Refusal("Unsupported state version. Do not rewrite the saved job.")
    if job != Path(state["worktree"] + ".factory").resolve():
        raise Refusal("The job directory does not match the saved worktree.")
    return state


def workspace(state):
    root = Path(state["worktree"])
    actual = Path(read_git(root, "rev-parse", "--show-toplevel").strip()).resolve()
    if actual != root:
        raise Refusal("The expected worktree is missing or was replaced.")
    common = read_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    original = read_git(Path(state["repo"]), "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    if Path(common).resolve() != Path(original).resolve():
        raise Refusal("The worktree belongs to a different repository.")
    branch = read_git(root, "symbolic-ref", "--quiet", "--short", "HEAD").strip()
    if branch != state["branch"]:
        raise Refusal("The checked-out branch changed. Ask the user to resolve Git state.")
    if read_git(root, "rev-parse", "HEAD").strip() != state["base_commit"]:
        raise Refusal("HEAD changed. Ask the user to resolve Git state.")
    staged = read_git(root, "diff", "--no-ext-diff", "--no-textconv", "--cached", "--name-only")
    if staged:
        raise Refusal("Staged changes exist. Ask the user to resolve Git state.")
    return root


def tree_digest(root):
    names = read_git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    entries = []
    for name in sorted(set(names.split("\0")) - {""}):
        path = root / name
        if not path.parent.resolve().is_relative_to(root):
            raise Refusal("A source path leaves the worktree. Ask the user to resolve it.")
        try:
            info = path.lstat()
        except FileNotFoundError:
            entries.append([name, "missing"])
            continue
        if stat.S_ISLNK(info.st_mode):
            entries.append([name, "symlink", os.readlink(path)])
        elif stat.S_ISREG(info.st_mode):
            entries.append([name, "file", bool(info.st_mode & 0o111), file_digest(path)])
        elif stat.S_ISDIR(info.st_mode):
            if (path / ".git").exists():
                head = read_git(path, "rev-parse", "HEAD").strip()
                entries.append([name, "submodule", head, tree_digest(path)])
            else:
                entries.append([name, "uninitialized-submodule"])
        else:
            raise Refusal("A source file has an unsupported type: " + name)
    return digest(json.dumps(entries, ensure_ascii=True).encode("utf-8"))


def snapshot(job, state):
    root = workspace(state)
    inputs = {}
    for name in ("request.md", "plan.md", "checks.json"):
        path = job / name
        inputs[name] = file_digest(path) if path.exists() else None
    inputs["tree"] = tree_digest(root)
    inputs["reviewers"] = state["reviewers"]
    return digest(json.dumps(inputs, sort_keys=True).encode("utf-8"))


def nonempty_file(path):
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        raise Refusal("A nonempty UTF-8 file is required: " + str(path))


def checks_config(job):
    checks = json.loads((job / "checks.json").read_text(encoding="utf-8"))
    if not isinstance(checks, list) or not checks:
        raise Refusal("Establish the project's required checks before implementation.")
    names = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) - {"name", "argv", "timeout"}:
            raise Refusal("Each check must contain name, argv, and an optional timeout.")
        name, argv, timeout = check.get("name"), check.get("argv"), check.get("timeout", 600)
        if not isinstance(name, str) or not name.strip() or name in names:
            raise Refusal("Check names must be nonempty and unique.")
        names.add(name)
        if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) for arg in argv):
            raise Refusal("Each check requires a nonempty list of string arguments.")
        if not argv[0] or any("\0" in arg for arg in argv):
            raise Refusal("Check arguments contain an invalid executable or NUL character.")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise Refusal("Each check timeout must be a positive finite number.")
    return checks


def local_base(repo, base):
    if base.startswith("refs/heads/") or base.startswith("refs/remotes/"):
        candidates = [base]
    elif base.startswith("refs/") or base.startswith("-"):
        raise Refusal("Select a local branch or remote-tracking branch as the base.")
    else:
        candidates = ["refs/heads/" + base, "refs/remotes/" + base]
    for ref in candidates:
        try:
            commit = read_git(repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").strip()
            return ref, commit
        except Refusal:
            continue
    raise Refusal("The selected base branch is unavailable locally. Do not fetch automatically.")


def create(args):
    if not args.confirmed:
        raise Refusal("Confirm the new branch and base branch with the user first.")
    requested_repo = Path(args.repo).resolve()
    repo = Path(read_git(requested_repo, "rev-parse", "--show-toplevel").strip()).resolve()
    branch = read_git(repo, "check-ref-format", "--branch", args.branch).strip()
    if branch != args.branch:
        raise Refusal("Use an explicit new branch name.")
    base_ref, base_commit = local_base(repo, args.base)
    root = Path(args.worktree).resolve()
    job = Path(str(root) + ".factory")
    request = Path(args.request_file).read_text(encoding="utf-8")
    if not request.strip():
        raise Refusal("The saved chat request is empty.")
    if root == repo or repo.is_relative_to(root):
        raise Refusal("The new worktree must be separate from the existing checkout.")
    expected = {"repo": str(repo), "worktree": str(root), "branch": branch,
                "base_ref": base_ref, "base_commit": base_commit}
    if not job.exists():
        if root.exists():
            raise Refusal("The worktree path already exists. Inspect it before proceeding.")
        job.mkdir(parents=True)
    with locked(job):
        state_path = job / "job.json"
        if state_path.exists():
            state = load(job)
            if any(state[key] != value for key, value in expected.items()):
                raise Refusal("Existing setup has different inputs. Inspect it before proceeding.")
            if (job / "request.md").read_text(encoding="utf-8") != request:
                raise Refusal("Existing setup has a different request.")
            if state["stage"] != "setup":
                raise Refusal("This job already started. Use status to resume it.")
        else:
            if any(path.name != ".lock" for path in job.iterdir()):
                raise Refusal("The job directory contains unknown files. Inspect it first.")
            state = {"schema": SCHEMA, **expected, "stage": "setup", "created_at": now(),
                     "repairs": 0, "check_count": 0, "reviewers": [], "reviews": {},
                     "last_check": None, "baseline_config": None, "baseline_tree": None,
                     "reason": None}
            (job / "request.md").write_text(request, encoding="utf-8", newline="\n")
            save(job, state)
        if not root.exists():
            empty_hooks = job / "empty-hooks"
            empty_hooks.mkdir(exist_ok=True)
            result = subprocess.run(
                ["git", "-c", "core.hooksPath=" + str(empty_hooks), "-C", str(repo),
                 "worktree", "add", "--no-track", "-b", branch, "--", str(root), base_commit],
                env=git_env(), capture_output=True, text=True, check=False,
            )
            if result.returncode:
                raise Refusal(result.stderr.strip() or "Worktree creation failed. Inspect partial setup.")
        workspace(state)
        state["stage"] = "baseline"
        save(job, state)
    return {"job": str(job), **state}


def start_build(job, args):
    with locked(job):
        state = load(job)
        workspace(state)
        if state["stage"] != "plan":
            raise Refusal("A passing baseline is required before planning and implementation.")
        nonempty_file(job / "plan.md")
        if file_digest(job / "checks.json") != state["baseline_config"]:
            raise Refusal("Checks changed after baseline. Ask how to establish a new baseline.")
        if tree_digest(Path(state["worktree"])) != state["baseline_tree"]:
            raise Refusal("Source changed after baseline. Ask how to establish a new baseline.")
        roles = sorted(set(args.reviewers))
        if "code" not in roles or set(roles) - ROLES:
            raise Refusal("Select code and any relevant security or ui reviewers.")
        state.update(stage="build", reviewers=roles, reviews={})
        save(job, state)
    return state


def repair_or_block(state, reason):
    state["reason"] = reason
    if state["repairs"] >= MAX_REPAIRS:
        state["stage"] = "blocked"
        state["block_kind"] = "budget"
        state["reason"] = "Repair budget exhausted. " + reason
    else:
        state["repairs"] += 1
        state["stage"] = "repair"


def group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def stop_group(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError as error:
        raise CleanupFailure("Check process cleanup failed. Resolve remaining processes first.") from error
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired as error:
        raise CleanupFailure("The check process did not stop. Resolve it before continuing.") from error


def execute_check(argv, root, output, timeout, on_start):
    process = subprocess.Popen(argv, cwd=root, env=git_env(), stdout=output,
                               stderr=subprocess.STDOUT, start_new_session=True)
    try:
        on_start(process.pid)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            stop_group(process)
            return None, "Timeout expired."
        if group_exists(process.pid):
            stop_group(process)
            return code, "The check left background processes running. They were stopped."
        return code, None
    except BaseException:
        stop_group(process)
        raise


def run_checks(job, args):
    with locked(job):
        state = load(job)
        stage = state["stage"]
        baseline = stage in {"baseline", "baseline-blocked"} or (
            stage == "checking" and state.get("checking_baseline")
        )
        if stage == "baseline-blocked" and not args.resolved:
            raise Refusal("Stop and ask the user to resolve baseline failures before retrying.")
        if stage not in {"baseline", "baseline-blocked", "build", "repair", "checking", "review", "ready"}:
            raise Refusal("Checks cannot run from stage " + stage + ".")
        if os.name != "posix":
            raise Refusal("The check runner requires POSIX process groups. Use Linux, macOS, or WSL.")
        active = state.get("active_check")
        if active and group_exists(active["pid"]):
            raise Refusal("A previous check process group still exists. Resolve it before retrying.")
        root = workspace(state)
        checks = checks_config(job)
        config_hash = file_digest(job / "checks.json")
        if not baseline and config_hash != state["baseline_config"]:
            raise Refusal("Checks changed after baseline. Ask how to establish a new baseline.")
        before = snapshot(job, state)
        check_id = state["check_count"] + 1
        run_dir = job / "checks" / ("run-%04d" % check_id)
        state.update(stage="checking", checking_baseline=baseline, check_count=check_id,
                     last_check=None, reviews={}, reason=None, active_check=None)
        save(job, state)
        run_dir.mkdir(parents=True)
        results = []
        cleanup_problem = None
        for index, check in enumerate(checks, 1):
            log = run_dir / ("%02d.log" % index)

            def started(pid):
                state["active_check"] = {"pid": pid, "argv": check["argv"], "started_at": now()}
                save(job, state)

            with log.open("wb") as output:
                try:
                    code, error = execute_check(check["argv"], root, output,
                                                check.get("timeout", 600), started)
                    state["active_check"] = None
                except CleanupFailure as failure:
                    code, error = None, str(failure)
                    cleanup_problem = error
                except OSError as failure:
                    code, error = None, str(failure)
            results.append({"name": check["name"], "argv": check["argv"],
                            "exit_code": code, "error": error, "log": str(log)})
            if cleanup_problem:
                break
        try:
            after, error = snapshot(job, state), None
        except (Refusal, OSError) as failure:
            after, error = None, str(failure)
        passed = (len(results) == len(checks) and cleanup_problem is None and before == after
                  and all(item["exit_code"] == 0 and item["error"] is None for item in results))
        evidence = {"id": check_id, "baseline": baseline, "passed": passed,
                    "snapshot": after, "before_snapshot": before, "error": error,
                    "source_unchanged": before == after, "results": results, "finished_at": now()}
        atomic_json(run_dir / "result.json", evidence)
        state["last_check"] = evidence
        if cleanup_problem:
            state.update(stage="blocked", reason=cleanup_problem, block_kind="process",
                         resume_stage="baseline" if baseline else "build")
        elif baseline:
            state["stage"] = "plan" if passed else "baseline-blocked"
            state["reason"] = None if passed else "Baseline failed. Ask the user to resolve it first."
            if passed:
                state["baseline_config"] = config_hash
                state["baseline_tree"] = tree_digest(root)
        elif passed:
            state["stage"] = "review"
        elif error is not None:
            state.update(stage="blocked", reason="Workspace verification failed. " + error,
                         block_kind="workspace", resume_stage="build")
        else:
            repair_or_block(state, "Checks failed or changed the source snapshot.")
        save(job, state)
    return state, 0 if passed else 1


def passing_check(job, state):
    evidence = state["last_check"]
    if not evidence or evidence["baseline"] or not evidence["passed"]:
        raise Refusal("A passing build check is required before review.")
    if file_digest(job / "checks.json") != state["baseline_config"]:
        raise Refusal("Checks changed after baseline. Ask how to establish a new baseline.")
    if snapshot(job, state) != evidence["snapshot"]:
        raise Refusal("The checked snapshot is stale. Run the full checks again.")
    saved = job / "checks" / ("run-%04d" % evidence["id"]) / "result.json"
    if json.loads(saved.read_text(encoding="utf-8")) != evidence:
        raise Refusal("Saved check evidence changed. Run the full checks again.")
    return evidence


def reviews_current(job, state):
    if set(state["reviews"]) != set(state["reviewers"]):
        return False
    evidence = state["last_check"]
    for report in state["reviews"].values():
        path = job / report["path"]
        if (report["result"] != "pass" or report["check_id"] != evidence["id"]
                or report["snapshot"] != evidence["snapshot"] or not path.is_file()
                or file_digest(path) != report["sha256"]):
            return False
    return True


def record_review(job, args):
    with locked(job):
        state = load(job)
        if state["stage"] != "review":
            raise Refusal("Reviews can only be recorded during the review stage.")
        if args.role not in state["reviewers"]:
            raise Refusal("This role is not required by the current plan.")
        evidence = passing_check(job, state)
        if args.check_id != evidence["id"] or args.snapshot != evidence["snapshot"]:
            raise Refusal("The reviewer used a different check run or snapshot.")
        source = Path(args.report_file)
        nonempty_file(source)
        directory = job / "reviews" / ("run-%04d" % evidence["id"])
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / (args.role + ".md")
        text = source.read_text(encoding="utf-8")
        target.write_text(text, encoding="utf-8", newline="\n")
        state["reviews"][args.role] = {
            "result": args.result, "mode": args.mode, "check_id": evidence["id"],
            "snapshot": evidence["snapshot"], "path": str(target.relative_to(job)),
            "sha256": file_digest(target),
        }
        if set(state["reviews"]) == set(state["reviewers"]):
            verdicts = {report["result"] for report in state["reviews"].values()}
            if "incomplete" in verdicts:
                state.update(stage="blocked", reason="A required review is incomplete.",
                             block_kind="review", resume_stage="build")
            elif "changes" in verdicts:
                repair_or_block(state, "Review findings require changes.")
            elif reviews_current(job, state):
                state.update(stage="ready", reason=None)
            else:
                raise Refusal("Review evidence changed. Repeat the affected reviews.")
        save(job, state)
    return state


def status(job):
    state = load(job)
    current = None
    try:
        current, error = snapshot(job, state), None
        passing_check(job, state)
        can_handoff = state["stage"] == "ready" and reviews_current(job, state)
    except (Refusal, OSError) as failure:
        error, can_handoff = str(failure), False
    return {**state, "job": str(job), "current_snapshot": current,
            "can_handoff": can_handoff, "evidence_problem": error}


def block(job, args):
    if not args.reason.strip():
        raise Refusal("State the blocker before stopping the job.")
    with locked(job):
        state = load(job)
        if state["stage"] != "blocked":
            state.update(resume_stage=state["stage"], block_kind="manual")
        state.update(stage="blocked", reason=args.reason)
        save(job, state)
    return state


def resume(job, args):
    if not args.resolved:
        raise Refusal("Ask the user to confirm the blocker is resolved before resuming.")
    with locked(job):
        state = load(job)
        if state["stage"] != "blocked" or state.get("block_kind") == "budget":
            raise Refusal("Only resolved prerequisites can resume. Repair budgets cannot be reset.")
        workspace(state)
        active = state.get("active_check")
        if active and group_exists(active["pid"]):
            raise Refusal("A previous check process group still exists. Resolve it before resuming.")
        target = state["resume_stage"]
        if target == "checking":
            target = "baseline" if state["checking_baseline"] else "build"
        if target in {"review", "ready", "repair"}:
            target = "build"
        state.update(stage=target, reason=None, active_check=None, reviews={})
        if target == "build":
            state["last_check"] = None
        save(job, state)
    return state


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    create_parser = commands.add_parser("create", help="Create the confirmed branch and worktree.")
    for name in ("repo", "branch", "base", "worktree", "request-file"):
        create_parser.add_argument("--" + name, required=True)
    create_parser.add_argument("--confirmed", action="store_true")
    for name in ("status", "start-build", "check", "review", "block", "resume"):
        command = commands.add_parser(name)
        command.add_argument("job", type=Path)
        if name == "start-build":
            command.add_argument("--reviewers", nargs="+", choices=sorted(ROLES), required=True)
        elif name in {"check", "resume"}:
            command.add_argument("--resolved", action="store_true")
        elif name == "review":
            command.add_argument("--role", choices=sorted(ROLES), required=True)
            command.add_argument("--result", choices=("pass", "changes", "incomplete"), required=True)
            command.add_argument("--mode", choices=("separate", "sequential"), required=True)
            command.add_argument("--check-id", type=int, required=True)
            command.add_argument("--snapshot", required=True)
            command.add_argument("--report-file", required=True)
        elif name == "block":
            command.add_argument("--reason", required=True)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        code = 0
        if args.command == "create":
            output = create(args)
        else:
            job = args.job.resolve()
            if args.command == "status":
                output = status(job)
            elif args.command == "start-build":
                output = start_build(job, args)
            elif args.command == "check":
                output, code = run_checks(job, args)
            elif args.command == "review":
                output = record_review(job, args)
            elif args.command == "resume":
                output = resume(job, args)
            else:
                output = block(job, args)
        print(json.dumps(output, indent=2, ensure_ascii=True))
        return code
    except (Refusal, OSError, ValueError, KeyError, TypeError) as error:
        print("REFUSED: " + str(error), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted. Inspect saved state before resuming.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
