from tools import esquemas, nombres


def test_registro_tiene_todas_las_tools():
    esperadas = {"buscar_web", "buscar_componentes", "descargar_componente", "agente_llamar",
                 "dividir_tarea", "entregar_parte", "checkpoint_guardar", "recuperar_checkpoint", "continuar_cola"}
    assert nombres() == esperadas
    assert all(e["type"] == "function" and "parameters" in e["function"] for e in esquemas())
