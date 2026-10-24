#!/usr/bin/env python3
"""
Sistema de cola de tareas con prioridad, dependencias e idempotencia.
Prototipo aislado para auditoría X-Ray.
"""

import uuid
import hashlib
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field


class Prioridad(Enum):
    """Niveles de prioridad para tareas."""
    BAJA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4


class EstadoTarea(Enum):
    """Estados posibles de una tarea."""
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"
    FALLIDA = "fallida"
    BLOQUEADA = "bloqueada"


@dataclass
class Tarea:
    """Representa una tarea en el sistema."""
    id: str
    nombre: str
    descripcion: str
    prioridad: Prioridad
    estado: EstadoTarea = EstadoTarea.PENDIENTE
    dependencias: Set[str] = field(default_factory=set)
    resultado: Optional[Any] = None
    error: Optional[str] = None
    creado_en: str = field(default_factory=lambda: datetime.now().isoformat())
    actualizado_en: str = field(default_factory=lambda: datetime.now().isoformat())
    intentos: int = 0
    max_intentos: int = 3

    def to_dict(self) -> Dict:
        """Convierte la tarea a diccionario."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "prioridad": self.prioridad.name,
            "estado": self.estado.value,
            "dependencias": list(self.dependencias),
            "resultado": self.resultado,
            "error": self.error,
            "creado_en": self.creado_en,
            "actualizado_en": self.actualizado_en,
            "intentos": self.intentos,
            "max_intentos": self.max_intentos
        }

    def puede_ejecutarse(self, tareas_completadas: Set[str]) -> bool:
        """Verifica si todas las dependencias están completadas."""
        if self.estado != EstadoTarea.PENDIENTE:
            return False
        return self.dependencias.issubset(tareas_completadas)


class ColaTareas:
    """Sistema de cola de tareas con prioridad y dependencias."""

    def __init__(self):
        """Inicializa la cola de tareas."""
        self.tareas: Dict[str, Tarea] = {}
        self.hash_idempotencia: Dict[str, str] = {}

    def _validar_nombre(self, nombre: str) -> bool:
        """Valida que el nombre sea válido."""
        if not nombre or not isinstance(nombre, str):
            raise ValueError("El nombre debe ser una cadena no vacía")
        if len(nombre) < 3 or len(nombre) > 100:
            raise ValueError("El nombre debe tener entre 3 y 100 caracteres")
        return True

    def _validar_descripcion(self, descripcion: str) -> bool:
        """Valida que la descripción sea válida."""
        if not descripcion or not isinstance(descripcion, str):
            raise ValueError("La descripción debe ser una cadena no vacía")
        if len(descripcion) < 5:
            raise ValueError("La descripción debe tener al menos 5 caracteres")
        return True

    def _calcular_hash(self, nombre: str, descripcion: str) -> str:
        """Calcula hash para idempotencia."""
        contenido = f"{nombre}:{descripcion}"
        return hashlib.sha256(contenido.encode()).hexdigest()

    def crear_tarea(
        self,
        nombre: str,
        descripcion: str,
        prioridad: Prioridad = Prioridad.MEDIA,
        dependencias: Optional[List[str]] = None
    ) -> str:
        """Crea una nueva tarea con validación e idempotencia."""
        self._validar_nombre(nombre)
        self._validar_descripcion(descripcion)

        if not isinstance(prioridad, Prioridad):
            raise ValueError("Prioridad inválida")

        hash_tarea = self._calcular_hash(nombre, descripcion)

        if hash_tarea in self.hash_idempotencia:
            return self.hash_idempotencia[hash_tarea]

        if dependencias:
            for dep_id in dependencias:
                if dep_id not in self.tareas:
                    raise ValueError(f"Dependencia {dep_id} no existe")

        tarea_id = str(uuid.uuid4())
        tarea = Tarea(
            id=tarea_id,
            nombre=nombre,
            descripcion=descripcion,
            prioridad=prioridad,
            dependencias=set(dependencias) if dependencias else set()
        )

        self.tareas[tarea_id] = tarea
        self.hash_idempotencia[hash_tarea] = tarea_id

        return tarea_id

    def obtener_tarea(self, tarea_id: str) -> Optional[Tarea]:
        """Obtiene una tarea por su ID."""
        if not tarea_id or not isinstance(tarea_id, str):
            raise ValueError("ID de tarea inválido")
        return self.tareas.get(tarea_id)

    def completar_tarea(self, tarea_id: str, resultado: Any = None) -> bool:
        """Marca una tarea como completada."""
        tarea = self.obtener_tarea(tarea_id)
        if not tarea:
            raise ValueError(f"Tarea {tarea_id} no encontrada")

        if tarea.estado == EstadoTarea.COMPLETADA:
            return True

        tarea.estado = EstadoTarea.COMPLETADA
        tarea.resultado = resultado
        tarea.actualizado_en = datetime.now().isoformat()
        return True

    def fallar_tarea(self, tarea_id: str, error: str) -> bool:
        """Marca una tarea como fallida."""
        tarea = self.obtener_tarea(tarea_id)
        if not tarea:
            raise ValueError(f"Tarea {tarea_id} no encontrada")

        tarea.intentos += 1
        tarea.error = error
        tarea.actualizado_en = datetime.now().isoformat()

        if tarea.intentos >= tarea.max_intentos:
            tarea.estado = EstadoTarea.FALLIDA
            return False

        tarea.estado = EstadoTarea.PENDIENTE
        return True

    def obtener_siguientes_tareas(self) -> List[Tarea]:
        """Obtiene las siguientes tareas ejecutables ordenadas por prioridad."""
        tareas_completadas = {
            tid for tid, t in self.tareas.items()
            if t.estado == EstadoTarea.COMPLETADA
        }

        tareas_ejecutables = [
            tarea for tarea in self.tareas.values()
            if tarea.puede_ejecutarse(tareas_completadas)
        ]

        tareas_ejecutables.sort(
            key=lambda t: t.prioridad.value,
            reverse=True
        )

        return tareas_ejecutables

    def listar_tareas(self, estado: Optional[EstadoTarea] = None) -> List[Dict]:
        """Lista todas las tareas, opcionalmente filtradas por estado."""
        tareas = self.tareas.values()

        if estado:
            tareas = [t for t in tareas if t.estado == estado]

        return [t.to_dict() for t in tareas]

    def eliminar_tarea(self, tarea_id: str) -> bool:
        """Elimina una tarea del sistema."""
        if tarea_id not in self.tareas:
            raise ValueError(f"Tarea {tarea_id} no encontrada")

        for tarea in self.tareas.values():
            if tarea_id in tarea.dependencias:
                raise ValueError(
                    f"No se puede eliminar: {tarea_id} es dependencia de {tarea.id}"
                )

        del self.tareas[tarea_id]
        hashes_a_eliminar = [
            h for h, tid in self.hash_idempotencia.items()
            if tid == tarea_id
        ]
        for h in hashes_a_eliminar:
            del self.hash_idempotencia[h]

        return True


def demostrar_sistema():
    """Demuestra el funcionamiento del sistema de cola de tareas."""
    print("=== Demostración del Sistema de Cola de Tareas ===\n")

    cola = ColaTareas()

    print("1. Creando tareas básicas...")
    tarea1_id = cola.crear_tarea(
        "Tarea Inicial",
        "Configurar entorno de desarrollo",
        Prioridad.ALTA
    )
    print(f"   Creada: {tarea1_id}")

    tarea2_id = cola.crear_tarea(
        "Tarea Dependiente",
        "Implementar funcionalidad principal",
        Prioridad.MEDIA,
        dependencias=[tarea1_id]
    )
    print(f"   Creada: {tarea2_id}")

    tarea3_id = cola.crear_tarea(
        "Tarea Final",
        "Desplegar aplicación",
        Prioridad.CRITICA,
        dependencias=[tarea2_id]
    )
    print(f"   Creada: {tarea3_id}")

    print("\n2. Probando idempotencia...")
    tarea1_id_repetida = cola.crear_tarea(
        "Tarea Inicial",
        "Configurar entorno de desarrollo",
        Prioridad.ALTA
    )
    print(f"   Mismo ID: {tarea1_id == tarea1_id_repetida}")

    print("\n3. Obteniendo tareas ejecutables...")
    ejecutables = cola.obtener_siguientes_tareas()
    print(f"   Tareas listas: {len(ejecutables)}")
    for tarea in ejecutables:
        print(f"   - {tarea.nombre} (Prioridad: {tarea.prioridad.name})")

    print("\n4. Completando primera tarea...")
    cola.completar_tarea(tarea1_id, "Entorno configurado")
    print("   Tarea 1 completada")

    print("\n5. Verificando nuevas tareas ejecutables...")
    ejecutables = cola.obtener_siguientes_tareas()
    print(f"   Tareas listas: {len(ejecutables)}")
    for tarea in ejecutables:
        print(f"   - {tarea.nombre}")

    print("\n6. Probando manejo de errores...")
    try:
        cola.crear_tarea("X", "Desc", Prioridad.MEDIA)
    except ValueError as e:
        print(f"   Error capturado: {e}")

    print("\n7. Listando todas las tareas...")
    todas = cola.listar_tareas()
    print(f"   Total: {len(todas)} tareas")

    print("\n=== Demostración completada ===")


if __name__ == "__main__":
    demostrar_sistema()
