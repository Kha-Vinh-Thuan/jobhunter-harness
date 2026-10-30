"""Resolve repository bindings and inspect capabilities without running app code."""

import json
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest(root: Path) -> dict:
    data = read_json(root / "harness.json")
    local = root / "harness.local.json"
    if local.exists():
        overrides = read_json(local)
        if set(overrides) != {"repositories"}:
            raise ValueError("harness.local.json permits only repositories path overrides")
        for name, item in overrides["repositories"].items():
            if name not in data["repositories"] or set(item) != {"path"}:
                raise ValueError("Local overrides permit only known repository paths")
            data["repositories"][name]["path"] = item["path"]
    return data


def repositories(root: Path) -> dict[str, Path]:
    return {name: (root / item["path"]).resolve()
            for name, item in manifest(root)["repositories"].items()}


def repository_checks(root: Path) -> list[dict]:
    data = manifest(root)
    checks = []
    for name, path in repositories(root).items():
        missing = [item for item in data["repositories"][name]["required_paths"]
                   if not (path / item).exists()]
        checks.append({"id": name, "path": str(path), "status": "missing" if missing else "available",
                       "missing": missing})
    return checks


def revision(path: Path) -> str | None:
    result = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                            capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        return None
    head = result.stdout.strip()
    diff = subprocess.run(["git", "-C", str(path), "diff", "--binary", "HEAD"],
                          capture_output=True, timeout=10, check=True).stdout
    untracked = subprocess.run(["git", "-C", str(path), "ls-files", "--others", "--exclude-standard", "-z"],
                               capture_output=True, timeout=10, check=True).stdout
    if not diff and not untracked:
        return head
    digest = hashlib.sha256(b"tracked-diff\0" + len(diff).to_bytes(8, "big") + diff)
    for item in sorted(filter(None, untracked.split(b"\0"))):
        file = path / item.decode("utf-8", errors="surrogateescape")
        digest.update(len(item).to_bytes(8, "big") + item)
        if file.is_symlink():
            digest.update(b"symlink\0" + hashlib.sha256(str(file.readlink()).encode()).digest())
        elif file.is_file():
            content = hashlib.sha256()
            with file.open("rb") as stream:
                for block in iter(lambda: stream.read(65536), b""):
                    content.update(block)
            digest.update(b"file\0" + str(file.stat().st_mode & 0o777).encode() + b"\0" + content.digest())
    return head + "+worktree:" + digest.hexdigest()


def doctor(root: Path) -> dict:
    observations = list((root / ".state" / "hooks").glob("*.json"))
    return {"python": sys.version.split()[0], "python_supported": sys.version_info >= (3, 12),
            "executables": {name: shutil.which(name) for name in ("codex", "git", "docker", "aws")},
            "repositories": repository_checks(root),
            "native_hooks": {"trust": "review_required_in_codex", "observed_invocations": len(observations),
                             "note": "Payload tests do not establish native hook activation or trust."},
            "application_checks": "not_run", "deployment": "not_configured"}
