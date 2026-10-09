"""Los 12 Goals del Director (Documento 26) para la Puerta de Evidencia T07.

Cada goal tiene: nombre, pregunta de entrada, comprobacion de salida y
plantillas de consulta para el compilador de busquedas.
"""

GOALS = {
    "G01": {
        "nombre": "Objetivo",
        "entrada": "Que pidio exactamente?",
        "salida": "Se consiguio exactamente?",
        "plantillas": ["{task} objetivo", "que pide exactamente {task}"],
    },
    "G02": {
        "nombre": "Entidades",
        "entrada": "Que proyecto/version/ruta?",
        "salida": "Se trabajo sobre esas mismas?",
        "plantillas": ["{target} repositorio oficial", "{target} documentacion"],
    },
    "G03": {
        "nombre": "Restricciones",
        "entrada": "Que esta prohibido?",
        "salida": "Se respeto todo?",
        "plantillas": ["{target} restricciones prohibido", "{task} limitaciones"],
    },
    "G04": {
        "nombre": "Dependencias",
        "entrada": "Que necesita funcionar?",
        "salida": "Funcionan realmente?",
        "plantillas": ["{target} dependencias requirements", "{target} instalacion dependencias"],
    },
    "G05": {
        "nombre": "Fuente oficial",
        "entrada": "Existe documentacion oficial?",
        "salida": "Resultado coincide con ella?",
        "plantillas": ["{target} official documentation", "{target} docs oficiales"],
    },
    "G06": {
        "nombre": "Version",
        "entrada": "Cual es la version vigente?",
        "salida": "Se uso la correcta?",
        "plantillas": [
            "{target} latest release",
            "site:github.com {target} releases",
            "{target} changelog",
        ],
    },
    "G07": {
        "nombre": "Configuracion",
        "entrada": "Que configuracion necesita?",
        "salida": "Esta configurada asi?",
        "plantillas": ["{target} configuracion", "{target} setup configuration"],
    },
    "G08": {
        "nombre": "Integracion",
        "entrada": "Con que debe conectarse?",
        "salida": "Esta realmente conectado?",
        "plantillas": ["{target} integracion", "{target} integration guide"],
    },
    "G09": {
        "nombre": "Ejecucion",
        "entrada": "Que debe ejecutar?",
        "salida": "Se ejecuto?",
        "plantillas": ["{target} como ejecutar", "{target} run usage"],
    },
    "G10": {
        "nombre": "Tests",
        "entrada": "Como demostramos PASS?",
        "salida": "Pasaron las pruebas?",
        "plantillas": ["{target} tests pytest", "{target} como probar tests"],
    },
    "G11": {
        "nombre": "Contradicciones",
        "entrada": "Las fuentes discrepan?",
        "salida": "Aparecieron contradicciones?",
        "plantillas": ["{target} breaking changes", "{target} deprecated incompatibilidad"],
    },
    "G12": {
        "nombre": "Evidencia",
        "entrada": "Tenemos evidencia suficiente?",
        "salida": "Podemos demostrar el cierre?",
        "plantillas": ["{target} evidencia verificacion", "{task} prueba de cierre"],
    },
}

GOAL_IDS = [f"G{i:02d}" for i in range(1, 13)]


def get_goal(goal_id):
    return GOALS[goal_id]


def preguntas_entrada():
    return {gid: GOALS[gid]["entrada"] for gid in GOAL_IDS}


def comprobaciones_salida():
    return {gid: GOALS[gid]["salida"] for gid in GOAL_IDS}


def plantillas(goal_id):
    return list(GOALS[goal_id]["plantillas"])
