# Buckets/utils/env.py
from __future__ import annotations

import getpass
import socket


def get_user_host_string() -> str:
    try:
        username = getpass.getuser()
        hostname = socket.gethostname()
        return f"{username}@{hostname}"
    except Exception:
        return "unknown@unknown"
