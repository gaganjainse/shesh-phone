"""Subprocess wrapper for adb (isolated for tests)."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class Result:
    stdout: str | bytes
    stderr: str
    returncode: int

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def text(self) -> str:
        out = self.stdout.decode() if isinstance(self.stdout, bytes) else self.stdout
        return (out + self.stderr).strip()


def run(cmd: list[str], *, timeout: int = 60, binary: bool = False) -> Result:
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)
        out = p.stdout if binary else p.stdout.decode(errors="replace")
        return Result(out, p.stderr.decode(errors="replace"), p.returncode)
    except FileNotFoundError:
        return Result(b"" if binary else "", "adb not installed", 127)
    except subprocess.TimeoutExpired:
        return Result(b"" if binary else "", "timeout", 124)
