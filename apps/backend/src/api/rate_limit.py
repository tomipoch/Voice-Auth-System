"""Shared rate limiter for FastAPI endpoints.

Kept in a dedicated module so controllers can import it without creating
a circular dependency with ``src.main`` (where the app is created).
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def _default_limit() -> list:
    return [os.getenv("RATE_LIMIT", "100/minute")]


limiter = Limiter(key_func=get_remote_address, default_limits=_default_limit())


# Common per-endpoint limits (override default if RATE_LIMIT_<ENDPOINT> is set)
def _limit_for(env_var: str, default: str) -> str:
    return os.getenv(env_var, default)


def login_limit() -> str:
    return _limit_for("RATE_LIMIT_LOGIN", "5/minute")


def refresh_limit() -> str:
    return _limit_for("RATE_LIMIT_REFRESH", "10/minute")


def enrollment_limit() -> str:
    return _limit_for("RATE_LIMIT_ENROLLMENT", "10/minute")


def verification_limit() -> str:
    return _limit_for("RATE_LIMIT_VERIFICATION", "15/minute")
