"""Perfil unico de esfuerzo por modelo (YAIWES) para llamadas SIN tools.
Fuente comun: Team 5 (mvp.py), Fichas 1-4 (plugin.py) y la ruta llm de Ficha 4
leen de aqui. Con Function Calling la regla es otra: Qwen va con
enable_thinking=false y SIN reasoning_effort en esa llamada."""
ESFUERZO_FICHA = {  # por id de ficha del selector (Team 5 y nodos de Fichas 1-4)
    'ficha-qwen38max': 'medium', 'ficha-qwen38flash': 'low', 'ficha-qwen37max': 'medium',
    'ficha-qwen37plus': 'medium', 'ficha-qwen36flash': 'low', 'ficha-qwen37flash': 'low',
    'ficha-dsv4pro': 'high', 'ficha-dsv4pro0813': 'high', 'ficha-dsv4flash': 'high',
    'ficha-glm52': 'high',
}
ESFUERZO_MODELO = {  # por nombre real del endpoint (ruta llm de Ficha 4 / llamadas directas)
    'qwen3.8-max': 'medium', 'qwen3.8-flash': 'low', 'qwen3.7-max': 'medium',
    'qwen3.7-plus': 'medium', 'qwen3.6-flash': 'low', 'qwen3.7-flash': 'low',
    'deepseek-v4-pro': 'high', 'deepseek-v4-pro-0813': 'high',
    'deepseek-v4-flash-0731': 'high', 'glm-5.2': 'high',
}
