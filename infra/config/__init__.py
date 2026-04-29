"""Environment configuration for the FME Training Automation CDK app.

Each module under :mod:`infra.config` exposes a single ``CONFIG`` dictionary
describing the resource sizing, retention windows, and alarm thresholds for
that environment.

The CDK app entrypoint (``infra/app.py``) selects between configurations via
the ``-c env=<name>`` context flag (``staging`` by default).
"""

from __future__ import annotations

from typing import Any, Dict

from .production import CONFIG as PRODUCTION
from .staging import CONFIG as STAGING

CONFIGS: Dict[str, Dict[str, Any]] = {
    "staging": STAGING,
    "production": PRODUCTION,
}


def get_config(env_name: str) -> Dict[str, Any]:
    """Return the configuration dict for ``env_name``.

    Raises ``KeyError`` if the environment is unknown so the CDK synth fails
    loudly rather than silently deploying with the wrong sizing.
    """

    if env_name not in CONFIGS:
        raise KeyError(
            f"Unknown environment '{env_name}'. "
            f"Available: {sorted(CONFIGS)}"
        )
    return CONFIGS[env_name]


__all__ = ["CONFIGS", "get_config", "PRODUCTION", "STAGING"]
