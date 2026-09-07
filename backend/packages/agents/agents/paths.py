"""Path resolution for reading docs/*.json live (single source of truth,
per docs/context/03-validation-rules.md and docs/context/07-decisions.md).

Local dev: the default derives docs/ from this file's position in the repo
tree. Docker: the container's filesystem layout differs (docs/ is mounted
at /docs, not alongside packages/), so every default here is overridable via
an env var -- see docker-compose.yml.
"""

import os
from pathlib import Path


def resolve_path(env_var: str, default: Path) -> Path:
    override = os.environ.get(env_var)
    return Path(override) if override else default
