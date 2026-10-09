import json
import os
import threading


class ProveedorMock:
    """SOLO PARA PRUEBAS. Imita el contrato de los adaptadores de memoria_yaiwes: save(scope, key, data) / load(scope, key) / search."""

    def __init__(self, carpeta):
        os.makedirs(carpeta, exist_ok=True)
        self.ruta = os.path.join(carpeta, 'mock_memoria.json')
        self.lock = threading.Lock()

    def _leer(self):
        try:
            return json.load(open(self.ruta))
        except Exception:
            return {}

    def save(self, scope, key, data):
        with self.lock:
            d = self._leer()
            d.setdefault(scope, {}).setdefault(key, []).append(data)
            json.dump(d, open(self.ruta, 'w'))
        return {'ok': True}

    def load(self, scope, key):
        with self.lock:
            return self._leer().get(scope, {}).get(key, [])


def conectar_harness():
    # GAP: falta la direccion exacta de memoria_yaiwes (chat router/04-MEMORIA). Cuando se conozca se cablea aqui y SOLO aqui.
    raise NotImplementedError('GAP: conectar el proveedor harness (save/load/search de memoria_yaiwes)')


class Memoria:
    """La ficha solo dice a que cajon pertenece (namespace) y que puede leer/escribir. El almacen real es el del harness."""

    def __init__(self, proveedor, task_id, proyecto='YAIWES', leer_proyecto=True, escribir_tarea=True, escribir_proyecto=False):
        self.p, self.task, self.proyecto = proveedor, task_id, proyecto
        self.leer_proyecto, self.escribir_tarea, self.escribir_proyecto = leer_proyecto, escribir_tarea, escribir_proyecto

    def _scope(self, tipo):
        return 'tasks/' + self.task + '/' + tipo

    def guardar(self, tipo, clave, dato):
        if not self.escribir_tarea:
            raise PermissionError('la ficha no puede escribir en su memoria')
        return self.p.save(self._scope(tipo), clave, dato)

    def cargar(self, tipo, clave):
        return self.p.load(self._scope(tipo), clave)

    def leer_del_proyecto(self, clave):
        if not self.leer_proyecto:
            raise PermissionError('la ficha no puede leer la memoria del proyecto')
        return self.p.load('project/' + self.proyecto, clave)

    def escribir_en_proyecto(self, clave, dato):
        if not self.escribir_proyecto:
            raise PermissionError('escritura directa en la memoria del proyecto prohibida: solo se promueve con PASS')
        return self.p.save('project/' + self.proyecto, clave, dato)

    def promover(self, clave, dato, pass_verificador):
        """Unico camino a la memoria del proyecto: la tarea termino y el verificador dio PASS."""
        if not pass_verificador:
            raise PermissionError('sin PASS del verificador no se promueve nada')
        return self.p.save('project/' + self.proyecto, clave, dato)
