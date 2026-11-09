from __future__ import annotations
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from plugins.ssh_bridge import plugin as sb  # noqa: E402

HOST = {"host": "10.0.0.5", "user": "deploy", "allowed_commands": ["uptime", "df"], "sftp_root": "/srv/riu"}


class Chan:
    def __init__(self, code=0):
        self.code = code
    def exit_status_ready(self):
        return True
    def recv_exit_status(self):
        return self.code


class Stream:
    def __init__(self, data, code=0):
        self.data, self.channel = data, Chan(code)
    def read(self, n):
        chunk, self.data = self.data[:n], self.data[n:]
        return chunk


class FakeFile:
    def __init__(self, store, path, mode):
        self.store, self.path, self.mode = store, path, mode
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def write(self, d):
        self.store[self.path] = d
    def read(self, n):
        return self.store[self.path][:n]


class FakeSftp:
    def __init__(self, store):
        self.store = store
    def file(self, path, mode):
        return FakeFile(self.store, path, mode)
    def stat(self, path):
        class S:
            st_size = len(self.store[path])
        return S()


class FakeClient:
    def __init__(self, out=b"up 1 day", code=0):
        self.out, self.code, self.store, self.closed, self.cmds = out, code, {}, False, []
    def exec_command(self, cmd, timeout=None):
        self.cmds.append(cmd)
        return None, Stream(self.out, self.code), Stream(b"")
    def open_sftp(self):
        return FakeSftp(self.store)
    def close(self):
        self.closed = True


def setup(monkeypatch, client=None, hosts=None, extra=None):
    cfg = {"hosts": {"h1": HOST} if hosts is None else hosts, "timeout_s": 5, "max_output_bytes": 10, "max_file_bytes": 8}
    cfg.update(extra or {})
    monkeypatch.setattr(sb, "_config", lambda: cfg)
    client = client or FakeClient()
    monkeypatch.setattr(sb, "_connect", lambda name, c: (client, None))
    return client


def test_status_off_without_hosts(monkeypatch):
    monkeypatch.setattr(sb, "_config", lambda: {"hosts": {}})
    assert sb.handle("status", {})["status"] == "off"


def test_status_degraded_without_paramiko(monkeypatch):
    monkeypatch.setattr(sb, "_config", lambda: {"hosts": {"h1": HOST}})
    monkeypatch.setattr(sb, "_paramiko", lambda: (None, "paramiko no disponible"))
    r = sb.handle("status", {})
    assert r["status"] == "degraded" and "paramiko" in r["reason"]


def test_status_needs_env_credential(monkeypatch):
    monkeypatch.setattr(sb, "_config", lambda: {"hosts": {"h1": HOST}})
    monkeypatch.setattr(sb, "_paramiko", lambda: (object(), None))
    monkeypatch.delenv("SSH_BRIDGE_KEY_H1", raising=False)
    monkeypatch.delenv("SSH_BRIDGE_PASSWORD_H1", raising=False)
    assert sb.handle("status", {})["status"] == "degraded"
    monkeypatch.setenv("SSH_BRIDGE_PASSWORD_H1", "x")
    r = sb.handle("status", {})
    assert r["status"] == "ok" and "x" not in json.dumps(r).replace("hosts", "").replace("sftp", "")


def test_connect_degraded_without_paramiko_or_credential(monkeypatch):
    monkeypatch.setattr(sb, "_paramiko", lambda: (None, "paramiko no disponible"))
    c, err = sb._connect("h1", HOST)
    assert c is None and "paramiko" in err
    monkeypatch.setattr(sb, "_paramiko", lambda: (object(), None))
    monkeypatch.delenv("SSH_BRIDGE_KEY_H1", raising=False)
    monkeypatch.delenv("SSH_BRIDGE_PASSWORD_H1", raising=False)
    c, err = sb._connect("h1", HOST)
    assert c is None and "SSH_BRIDGE_KEY_H1" in err


def test_run_ok_and_closes(monkeypatch):
    cl = setup(monkeypatch)
    r = sb.handle("run", {"host": "h1", "command": "uptime -p"})
    assert r["status"] == "ok" and r["stdout"] == "up 1 day" and r["exit_code"] == 0 and cl.closed


def test_run_unknown_host_denied(monkeypatch):
    setup(monkeypatch)
    assert sb.handle("run", {"host": "evil", "command": "uptime"})["status"] == "denied"


def test_run_command_not_in_list_denied(monkeypatch):
    cl = setup(monkeypatch)
    assert sb.handle("run", {"host": "h1", "command": "rm -rf /"})["status"] == "denied"
    assert cl.cmds == []


def test_run_metachars_denied(monkeypatch):
    setup(monkeypatch)
    for bad in ("uptime; rm x", "uptime | sh", "df $(id)", "df `id`", "uptime > f"):
        assert sb.handle("run", {"host": "h1", "command": bad})["status"] == "denied", bad


def test_run_allow_any_needs_config_and_flag(monkeypatch):
    setup(monkeypatch)
    assert sb.handle("run", {"host": "h1", "command": "ls", "allow_any": True})["status"] == "denied"
    both = dict(HOST, allow_any_command=True)
    setup(monkeypatch, hosts={"h1": both})
    assert sb.handle("run", {"host": "h1", "command": "ls"})["status"] == "denied"
    assert sb.handle("run", {"host": "h1", "command": "ls", "allow_any": True})["status"] == "ok"


def test_run_output_limit_and_exit_code(monkeypatch):
    setup(monkeypatch, client=FakeClient(out=b"x" * 100, code=3))
    r = sb.handle("run", {"host": "h1", "command": "df"})
    assert len(r["stdout"]) == 10 and r["truncated"] is True and r["status"] == "degraded" and r["exit_code"] == 3


def test_run_connect_error_degraded(monkeypatch):
    setup(monkeypatch)
    monkeypatch.setattr(sb, "_connect", lambda n, c: (None, "conexion fallida: timeout"))
    r = sb.handle("run", {"host": "h1", "command": "df"})
    assert r["status"] == "degraded" and "conexion" in r["reason"]


def test_put_get_roundtrip_and_limits(monkeypatch):
    cl = setup(monkeypatch)
    data = b"hola"
    r = sb.handle("put", {"host": "h1", "path": "a.txt", "content_b64": base64.b64encode(data).decode()})
    assert r["status"] == "ok" and cl.store["/srv/riu/a.txt"] == data
    g = sb.handle("get", {"host": "h1", "path": "a.txt"})
    assert g["status"] == "ok" and base64.b64decode(g["content_b64"]) == data
    big = base64.b64encode(b"z" * 9).decode()
    assert sb.handle("put", {"host": "h1", "path": "b", "content_b64": big})["status"] == "denied"
    cl.store["/srv/riu/big"] = b"z" * 9
    assert sb.handle("get", {"host": "h1", "path": "big"})["status"] == "denied"


def test_path_traversal_denied(monkeypatch):
    setup(monkeypatch)
    for p in ("../etc/passwd", "/etc/passwd", "a/../../x"):
        assert sb.handle("get", {"host": "h1", "path": p})["status"] == "denied", p


def test_no_sftp_root_disables_transfer(monkeypatch):
    setup(monkeypatch, hosts={"h1": {k: v for k, v in HOST.items() if k != "sftp_root"}})
    assert sb.handle("get", {"host": "h1", "path": "a"})["status"] == "denied"


def test_unknown_action_and_no_secrets_in_repo_config():
    assert sb.handle("zzz", {})["status"] == "degraded"
    raw = (Path(sb.__file__).parent / "config.json").read_text()
    for needle in ("BEGIN", "password\": \"", "ghp_", "hf_"):
        assert needle not in raw
    assert json.loads(raw)["hosts"] == {}
