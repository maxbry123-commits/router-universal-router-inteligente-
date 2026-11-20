import io
import tarfile
import zipfile
import httpx
import pytest
import motor_descarga as md


def test_host_no_permitido(tmp_path):
    assert md.descargar_repo("https://evil.example.com/x/y", "skills")["status"] == "failed"


def test_nombre_y_raices(monkeypatch, tmp_path):
    monkeypatch.setenv("SKILLS_DIR", str(tmp_path / "s"))
    assert md._nombre("https://github.com/cline/cline.git") == "cline__cline"
    assert md._raiz("skills") == tmp_path / "s"
    with pytest.raises(ValueError):
        md._raiz("otro")


def test_buscar_github_ordena_y_limita():
    def handler(req):
        items = [{"html_url": f"https://github.com/a/r{i}", "stargazers_count": i, "description": ""} for i in range(15)]
        return httpx.Response(200, json={"items": items})
    c = httpx.Client(transport=httpx.MockTransport(handler))
    r = md.buscar_github("cline", n=10, client=c)
    assert len(r) == 10 and r[0]["url"].endswith("r0")


def test_fusionar_quita_duplicados():
    cand = [{"url": "https://github.com/a/x", "stars": 1}, {"url": "https://GitHub.com/a/x/", "stars": 5}, {"url": "https://github.com/a/y", "stars": 3}]
    out = md.fusionar(cand)
    assert [c["stars"] for c in out] == [5, 3]


def test_extraer_zip_con_ruta_insegura(tmp_path):
    p = tmp_path / "bad.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("../../escape.txt", "x")
    assert md.extraer(str(p), str(tmp_path / "out"))["status"] == "failed"


def test_extraer_tar_ok(tmp_path):
    p = tmp_path / "ok.tar.gz"
    with tarfile.open(p, "w:gz") as t:
        data = b"hola"
        info = tarfile.TarInfo("dir/a.txt"); info.size = len(data)
        t.addfile(info, io.BytesIO(data))
    assert md.extraer(str(p), str(tmp_path / "out"))["status"] == "ok"
    assert (tmp_path / "out" / "dir" / "a.txt").read_text() == "hola"


def test_descargar_archivo_limita_tamano(monkeypatch, tmp_path):
    monkeypatch.setenv("SKILLS_DIR", str(tmp_path))
    monkeypatch.setattr(md, "MAX_BYTES", 3)
    c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"abcdef")))
    assert md.descargar_archivo("https://github.com/a/b/archive.zip", "skills", client=c)["status"] == "failed"
