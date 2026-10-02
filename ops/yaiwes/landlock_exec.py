"""Ejecuta un proceso con escrituras limitadas al workspace privado (Linux ABI >= 3)."""

from __future__ import annotations

import ctypes
import os
import platform
import sys
from pathlib import Path

CREATE_RULESET = 444
ADD_RULE = 445
RESTRICT_SELF = 446
CREATE_RULESET_VERSION = 1
RULE_PATH_BENEATH = 1
PR_SET_NO_NEW_PRIVS = 38
WRITE_FILE = 1 << 1
REMOVE_DIR = 1 << 4
REMOVE_FILE = 1 << 5
CREATE_BITS = sum(1 << bit for bit in range(6, 13))
REFER = 1 << 13
TRUNCATE = 1 << 14
WRITE_ACCESS = WRITE_FILE | REMOVE_DIR | REMOVE_FILE | CREATE_BITS | REFER | TRUNCATE


class RulesetAttr(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]


class PathBeneath(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


def restrict_writes(workspace: Path) -> None:
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "aarch64"):
        raise RuntimeError("LANDLOCK_PLATFORM_UNSUPPORTED")
    workspace = workspace.resolve(strict=True)
    if not workspace.is_dir() or workspace.is_symlink():
        raise RuntimeError("WORKSPACE_NOT_DIRECTORY")
    libc = ctypes.CDLL(None, use_errno=True)
    abi = libc.syscall(CREATE_RULESET, None, 0, CREATE_RULESET_VERSION)
    if abi < 3:
        raise RuntimeError("LANDLOCK_ABI_TOO_OLD_OR_UNAVAILABLE")
    ruleset = RulesetAttr(WRITE_ACCESS)
    ruleset_fd = libc.syscall(CREATE_RULESET, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
    if ruleset_fd < 0:
        raise OSError(ctypes.get_errno(), "LANDLOCK_CREATE_FAILED")
    try:
        for path, access in ((workspace, WRITE_ACCESS), (Path("/dev/null"), WRITE_FILE)):
            fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                rule = PathBeneath(access, fd)
                if libc.syscall(ADD_RULE, ruleset_fd, RULE_PATH_BENEATH, ctypes.byref(rule), 0) != 0:
                    raise OSError(ctypes.get_errno(), "LANDLOCK_ADD_RULE_FAILED")
            finally:
                os.close(fd)
        if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "NO_NEW_PRIVS_FAILED")
        if libc.syscall(RESTRICT_SELF, ruleset_fd, 0) != 0:
            raise OSError(ctypes.get_errno(), "LANDLOCK_RESTRICT_FAILED")
    finally:
        os.close(ruleset_fd)


def main(argv: list[str]) -> int:
    if len(argv) < 4 or argv[2] != "--":
        raise SystemExit("usage: landlock_exec.py <workspace> -- <sdk-command> [args...]")
    workspace = Path(argv[1]).resolve(strict=True)
    os.chdir(workspace / "project" if (workspace / "project").is_dir() else workspace)
    runtime = workspace / ".runtime"
    if runtime.is_dir():
        os.environ["HOME"] = str(runtime)
        os.environ["TMPDIR"] = str(runtime)
        os.environ["XDG_CACHE_HOME"] = str(runtime)
    else:
        os.environ["HOME"] = str(workspace)
        os.environ["TMPDIR"] = str(workspace)
        os.environ["XDG_CACHE_HOME"] = str(workspace / ".cache")
    restrict_writes(workspace)
    os.execvpe(argv[3], argv[3:], os.environ)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
