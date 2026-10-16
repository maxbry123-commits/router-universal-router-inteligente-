import importlib.util, pathlib, sys, subprocess, pytest
R = pathlib.Path(__file__).resolve().parents[1]
P = R / 'router inteligente universal' / 'plugins' / 'puente_chat' / 'plugin.py'
sys.path.insert(0, str(R / 'router inteligente universal'))

@pytest.fixture
def pc(monkeypatch):
    spec = importlib.util.spec_from_file_location('pc_fixc', P)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    monkeypatch.setattr(m.time, 'sleep', lambda s: None)
    return m

POL = {'con_tools': {'reasoning_effort': {'code': 'low', 'sin_tools': 'medium'}}}
TOOLS = [{'type': 'function', 'function': {'name': 'x', 'parameters': {}}}]
OK = (200, {'choices': [{'message': {'content': 'hola'}}]})

def run(pc, monkeypatch, base, tools, respuestas=None, extra=None):
    env = []
    resp = list(respuestas or [OK])
    monkeypatch.setattr(pc, '_qwen_conf', lambda: ('sk-sp-x', base))
    monkeypatch.setattr(pc, '_politica', lambda mod: POL)
    def fake(met, url, tok, cuerpo, espera=60):
        env.append(dict(cuerpo)); return resp.pop(0) if resp else resp_last
    resp_last = (resp or [OK])[-1]
    monkeypatch.setattr(pc, '_http', fake)
    if extra is not None:
        pc._EXTRA_LLM.set(extra)
    r = pc._llamar_api('qwencloud', 'qwen3.8-max', [{'role': 'user', 'content': 'hola'}], 100, 30, tools)
    return r, env

TP = 'https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1'
DS = 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1'

def both(c): return 'enable_thinking' in c and 'reasoning_effort' in c

def test_tp_sin_tools(pc, monkeypatch):
    r, e = run(pc, monkeypatch, TP, None)
    assert r[0] == 200 and len(e) == 1
    assert 'enable_thinking' not in e[0] and e[0]['reasoning_effort'] == 'medium'

def test_tp_con_tools(pc, monkeypatch):
    r, e = run(pc, monkeypatch, TP, TOOLS)
    assert e[0].get('enable_thinking') is not False and not both(e[0])

def test_ds_con_tools(pc, monkeypatch):
    r, e = run(pc, monkeypatch, DS, TOOLS)
    assert e[0]['enable_thinking'] is False and 'reasoning_effort' not in e[0]

def test_ds_sin_tools(pc, monkeypatch):
    r, e = run(pc, monkeypatch, DS, None)
    assert 'enable_thinking' not in e[0] and e[0]['reasoning_effort'] == 'medium'

def test_tp_extra_llm_false_se_quita(pc, monkeypatch):
    r, e = run(pc, monkeypatch, TP, None, extra={'enable_thinking': False})
    assert 'enable_thinking' not in e[0] and not both(e[0])

def test_ds_extra_llm_nunca_ambos(pc, monkeypatch):
    r, e = run(pc, monkeypatch, DS, None, extra={'enable_thinking': True})
    assert not both(e[0])

def test_400_un_solo_reintento(pc, monkeypatch):
    bad = (400, {'error': {'message': 'enable_thinking restricted to True'}})
    r, e = run(pc, monkeypatch, DS, TOOLS, respuestas=[bad, bad, bad, bad, bad])
    assert r[0] == 400 and len(e) == 2
    assert 'enable_thinking' not in e[1] and 'reasoning_effort' not in e[1]

def test_panel_chat_js():
    js = R / 'chat router' / 'chat frontend' / 'panel-chat.js'
    assert subprocess.run(['node', '--check', str(js)]).returncode == 0
    s = js.read_text()
    assert s.count('ficha_qwen: fq, modelo: c.selectorQwen ? c.selectorQwen.label : "", task_type: "chat" }') == 2
    assert 'ficha_qwen: "5", modelo: c.selectorQwen ? c.selectorQwen.label : "", instrucciones_fijas' in s  # Team 5 intacto
