"""Check the harness contracts and layout without claiming application readiness."""

import hashlib
import json
import re
import shlex
import tomllib
from pathlib import Path

from .progress import validate_progress
from .workspace import manifest, read_json, repository_checks


def validate(root: Path) -> dict:
    failures = []
    checks = []
    required = ["AGENTS.md", "README.md", "prompts/system.md", "context/project.md",
                "context/product-contract.md", "context/decisions.md", "context/capabilities.json",
                "context/sources.json", ".codex/config.toml", ".codex/hooks.json", "progress.json"]
    for name in required:
        if not (root / name).is_file():
            failures.append(f"Missing {name}")
    try:
        data = manifest(root)
        if data["harness_version"] != "1.0.0":
            raise ValueError("Unsupported harness version")
        for item in repository_checks(root):
            if item["status"] != "available":
                failures.append(f"Repository {item['id']} missing {item['missing']}")
        validate_progress(root, read_json(root / "progress.json"))
        checks.append("progress schema, transitions, evidence, and repository bindings")
    except (OSError, ValueError, KeyError) as error:
        failures.append(str(error))
    try:
        config = tomllib.loads((root / ".codex/config.toml").read_text())
        if any(key in config for key in ("model", "model_provider", "model_instructions_file", "approval_policy", "sandbox_mode")):
            raise ValueError("Project config must inherit model/provider/permissions and built-in system instructions")
        agents = list((root / ".codex/agents").glob("*.toml"))
        if {path.stem for path in agents} != {"explorer", "implementer", "reviewer"}:
            raise ValueError("Expected explorer, implementer, reviewer agent definitions")
        for path in agents:
            agent = tomllib.loads(path.read_text())
            if set(agent) != {"name", "description", "developer_instructions"} or not all(agent.values()):
                raise ValueError(f"{path.name}: invalid or overriding custom-agent config")
        hooks = read_json(root / ".codex/hooks.json")["hooks"]
        if set(hooks) != {"SessionStart", "PreCompact", "Interrupt", "Stop"}:
            raise ValueError("Unexpected lifecycle hook events")
        for event, groups in hooks.items():
            handlers = [handler for group in groups for handler in group["hooks"]]
            if len(handlers) != 1:
                raise ValueError(f"{event}: expected one bounded command handler")
            handler = handlers[0]
            expected = ["$(git rev-parse --show-toplevel)/.venv/bin/python", "$(git rev-parse --show-toplevel)/scripts/harness.py", "hook", event, "--native"]
            if handler.get("type") != "command" or shlex.split(handler["command"]) != expected:
                raise ValueError(f"{event}: use the portable Git-root hook paths and review trust again")
            if not (root / ".venv/bin/python").is_file() or not 0 < handler.get("timeout", 0) <= (3 if event == "Interrupt" else 10):
                raise ValueError(f"{event}: missing virtual environment or invalid timeout")
        checks.append("Codex configuration and development agent definitions")
    except (OSError, ValueError, KeyError) as error:
        failures.append(str(error))
    try:
        skills = list((root / ".agents/skills").glob("*/SKILL.md"))
        if len(skills) != 5:
            raise ValueError("Expected five focused skills")
        for path in skills:
            text = path.read_text()
            if not text.startswith("---\n"):
                raise ValueError(f"{path}: missing frontmatter")
            front = text.split("---", 2)[1]
            if not re.search(r"^name: " + re.escape(path.parent.name) + r"$", front, re.M) or not re.search(r"^description: .+", front, re.M):
                raise ValueError(f"{path}: invalid skill identity/description")
        checks.append("skill metadata and discovery layout")
        sources = read_json(root / "context/sources.json")
        for source in sources["notion"]:
            path = root / source["snapshot"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
                raise ValueError(f"Changed source snapshot: {path}")
        checks.append("Notion source snapshot hashes")
        registry = read_json(root / "context/capabilities.json")
        if not isinstance(registry["capabilities"], list):
            raise ValueError("Invalid capabilities registry")
    except (OSError, ValueError, KeyError) as error:
        failures.append(str(error))
    # This boundary is a layout check, not a sandbox or comprehensive secret scanner.
    for path in (root / "backend", root / "frontend", root / "addons", root / "Dockerfile", root / "docker-compose.yml"):
        if path.exists():
            failures.append(f"Application code/deployment artifact outside harness scope: {path.name}")
    for path in root.rglob(".env*"):
        if not any(part in {".venv", ".state", ".git"} for part in path.relative_to(root).parts):
            failures.append(f"Credentials must remain in the owning application: {path.name}")
    return {"status": "failed" if failures else "passed", "checks": checks, "failures": failures,
            "native_activation": "not_verified", "application_checks": "not_run"}
