import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from mvp import modelos as m

d = m.cargar()
assert len(d['texto']) == 20 and len(d['imagen']) == 5 and len(d['audio']) == 3 and len(d['video']) == 4
todos = d['texto'] + d['imagen'] + d['audio'] + d['video']
assert sum(x['p'] for x in todos) == 23, 'Personal debe sumar 23'
assert sum(x['t'] for x in todos) == 32, 'Team debe sumar 32'
assert len(m.permitidos('personal')) == 13 and len(m.permitidos('team')) == 20
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
assert len(cfg['modelProviders']['openai']) == 13 and cfg['model']['name'] == 'qwen3.8-max'
e = cfg['modelProviders']['openai'][1]
assert e['id'] == 'qwen3.8-max' and e['envKey'] == 'BAILIAN_TOKEN_PLAN_API_KEY' and e['generationConfig'] == {'extra_body': {'enable_thinking': True}}
assert len(m.qwen_code_config('team')['modelProviders']['openai']) == 20
print('test_modelos OK')
