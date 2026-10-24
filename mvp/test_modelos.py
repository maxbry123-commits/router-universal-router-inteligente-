import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from mvp import modelos as m

d = m.cargar()
assert len(d['texto']) == 19 and len(d['imagen']) == 5 and len(d['audio']) == 3 and len(d['video']) == 4
todos = d['texto'] + d['imagen'] + d['audio'] + d['video']
assert sum(x['p'] for x in todos) == 22, 'Personal debe sumar 22 (sin auto)'
assert sum(x['t'] for x in todos) == 31, 'Team debe sumar 31'
assert len(m.permitidos('personal')) == 12 and len(m.permitidos('team')) == 19
assert m.validar('') == 'qwen3.8-max'
assert m.validar('qwen3.6-plus', 'team') == 'qwen3.6-plus'
for malo, plan in (('qwen3.6-plus', 'personal'), ('wan3.0-video', 'team'), ('no-existe', 'team')):
    try:
        m.validar(malo, plan)
        raise SystemExit('debia fallar: ' + malo)
    except ValueError:
        pass
assert m.extra_body('qwen3.8-max', 'personal') == {'enable_thinking': True}
assert m.extra_body('deepseek-v4-pro', 'personal') == {}
assert m.extra_body('glm-5.3', 'personal') == {}
assert m.extra_body('glm-5.3', 'team') == {'enable_thinking': True}
assert m.extra_body('qwen3.8-max', 'personal', {'reasoning_effort': 'low'})['reasoning_effort'] == 'low'
assert m.base_url() == 'https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1'
cfg = m.qwen_code_config('personal')
assert len(cfg['modelProviders']['openai']) == 12 and cfg['model']['name'] == 'qwen3.8-max'
e = cfg['modelProviders']['openai'][0]
assert e['id'] == 'qwen3.8-max' and e['envKey'] == 'BAILIAN_TOKEN_PLAN_API_KEY' and e['generationConfig'] == {'extra_body': {'enable_thinking': True}}
assert len(m.qwen_code_config('team')['modelProviders']['openai']) == 19
print('test_modelos OK')
