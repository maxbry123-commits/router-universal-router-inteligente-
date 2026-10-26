#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prototipo educativo local de registro de cuentas y permisos.
Python 3 estandar: solo re, hashlib, secrets, json, datetime y functools.
Sin red, sin servidores, sin conexiones externas y sin claves en claro:
la contrasena se deriva con PBKDF2-HMAC-SHA256 y una sal aleatoria por usuario.
Todos los datos viven en memoria al ejecutar el modulo (volatiles, didactico).
"""

import re
import json
import secrets
import hashlib
import datetime
from functools import wraps

# --- Reglas de validacion --------------------------------------------------
USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$')
PASSWORD_MIN = 8
PASSWORD_MAX = 64
ITERACIONES = 120_000
FORMATO_FECHA = '%Y-%m-%d %H:%M:%S'
MAX_INTENTOS = 5

# --- Errores de dominio ----------------------------------------------------
class ErrorCuenta(Exception):
    """Cualquier error del registro de cuentas."""

class ErrorValidacion(ErrorCuenta):
    """Una entrada no cumple las reglas de formato o longitud."""

class ErrorDuplicado(ErrorCuenta):
    """El nombre de usuario o correo ya esta registrado."""

class ErrorAutenticacion(ErrorCuenta):
    """Nombre de usuario o contrasena incorrectos."""

class ErrorPermiso(ErrorCuenta):
    """La operacion requiere un permiso que el usuario no tiene."""

# --- Matriz de permisos por rol ---------------------------------------------
PERMISOS_POR_ROL = {
    'admin': {'leer', 'crear', 'editar', 'borrar', 'gestionar_usuarios'},
    'editor': {'leer', 'crear', 'editar'},
    'viewer': {'leer'},
}
ROLES_VALIDOS = frozenset(PERMISOS_POR_ROL)

# --- Validaciones ------------------------------------------------------------
def validar_usuario(nombre):
    if not isinstance(nombre, str):
        raise ErrorValidacion('El nombre de usuario debe ser texto.')
    if not USERNAME_RE.fullmatch(nombre):
        raise ErrorValidacion('El usuario debe tener de 3 a 20 caracteres: letras, digitos o _.')

def validar_email(correo):
    if not isinstance(correo, str) or not EMAIL_RE.fullmatch(correo):
        raise ErrorValidacion('Formato de correo invalido.')

def validar_password(clave):
    if not isinstance(clave, str):
        raise ErrorValidacion('La contrasena debe ser texto.')
    if not (PASSWORD_MIN <= len(clave) <= PASSWORD_MAX):
        raise ErrorValidacion('La contrasena debe tener entre %d y %d caracteres.' % (PASSWORD_MIN, PASSWORD_MAX))
    if clave.isdigit() or clave.isalpha():
        raise ErrorValidacion('La contrasena debe mezclar letras y numeros.')

def validar_rol(rol):
    if rol not in ROLES_VALIDOS:
        raise ErrorValidacion('Rol desconocido: %r (validos: %s).' % (rol, ', '.join(sorted(ROLES_VALIDOS))))

# --- Derivacion de clave (PBKDF2; nunca se guarda la contrasena en claro) -----
def generar_sal():
    return secrets.token_bytes(16)

def derivar_clave(clave, sal):
    return hashlib.pbkdf2_hmac('sha256', clave.encode('utf-8'), sal, ITERACIONES)

def verificar_clave(clave, sal, esperado):
    nuevo = derivar_clave(clave, sal)
    return secrets.compare_digest(nuevo, esperado)

# --- Gestor de cuentas ---------------------------------------------------------
class GestorCuentas:
    def __init__(self):
        self._usuarios = {}
        self._sesiones = {}
        self._proxima_sesion = 1000

    def registrar(self, nombre, correo, clave, rol='viewer'):
        validar_usuario(nombre)
        validar_email(correo)
        validar_password(clave)
        validar_rol(rol)
        if nombre in self._usuarios:
            raise ErrorDuplicado('El usuario %r ya existe.' % nombre)
        for datos in self._usuarios.values():
            if datos['correo'] == correo:
                raise ErrorDuplicado('El correo %r ya esta registrado.' % correo)
        sal = generar_sal()
        usuario = {
            'nombre': nombre,
            'correo': correo,
            'sal': sal,
            'clave': derivar_clave(clave, sal),
            'rol': rol,
            'creado': datetime.datetime.now().strftime(FORMATO_FECHA),
            'intentos_fallidos': 0,
            'bloqueado': False,
        }
        self._usuarios[nombre] = usuario
        return usuario['creado']

    def iniciar_sesion(self, nombre, clave):
        validar_usuario(nombre)
        validar_password(clave)
        usuario = self._usuarios.get(nombre)
        if usuario is None:
            raise ErrorAutenticacion('Credenciales invalidas.')
        if usuario['bloqueado']:
            raise ErrorAutenticacion('Cuenta bloqueada por demasiados intentos.')
        if not verificar_clave(clave, usuario['sal'], usuario['clave']):
            usuario['intentos_fallidos'] += 1
            if usuario['intentos_fallidos'] >= MAX_INTENTOS:
                usuario['bloqueado'] = True
            raise ErrorAutenticacion('Credenciales invalidas.')
        usuario['intentos_fallidos'] = 0
        self._proxima_sesion += 1
        token = 'ses_%d_%s' % (self._proxima_sesion, secrets.token_hex(4))
        self._sesiones[token] = nombre
        return token

    def cerrar_sesion(self, token):
        if token in self._sesiones:
            del self._sesiones[token]

    def _usuario_por_token(self, token):
        nombre = self._sesiones.get(token)
        if nombre is None:
            raise ErrorAutenticacion('Sesion inexistente o caducada.')
        return self._usuarios[nombre]

    def tiene_permiso(self, token, permiso):
        usuario = self._usuario_por_token(token)
        return permiso in PERMISOS_POR_ROL[usuario['rol']]

    def verificar_permiso(self, token, permiso):
        if not self.tiene_permiso(token, permiso):
            rol = self._usuario_por_token(token)['rol']
            raise ErrorPermiso('Permiso %r requerido; tu rol es %r.' % (permiso, rol))

    def requerir_permiso(self, permiso):
        def deco(funcion):
            @wraps(funcion)
            def envuelta(self_, token, *args, **kwargs):
                self_.verificar_permiso(token, permiso)
                return funcion(self_, token, *args, **kwargs)
            return envuelta
        return deco

    @requerir_permiso('gestionar_usuarios')
    def cambiar_rol(self, token, nombre, nuevo_rol):
        validar_rol(nuevo_rol)
        usuario = self._usuarios.get(nombre)
        if usuario is None:
            raise ErrorCuenta('El usuario %r no existe.' % nombre)
        anterior = usuario['rol']
        usuario['rol'] = nuevo_rol
        return anterior, nuevo_rol

    def cambiar_contrasena(self, token, anterior, nueva):
        validar_password(nueva)
        usuario = self._usuario_por_token(token)
        if not verificar_clave(anterior, usuario['sal'], usuario['clave']):
            raise ErrorAutenticacion('La contrasena anterior no coincide.')
        sal = generar_sal()
        usuario['sal'] = sal
        usuario['clave'] = derivar_clave(nueva, sal)
        return True

    def listar_usuarios(self, token):
        self.verificar_permiso(token, 'leer')
        return [self.resumen(datos) for datos in self._usuarios.values()]

    @staticmethod
    def resumen(datos):
        return {'nombre': datos['nombre'], 'correo': datos['correo'], 'rol': datos['rol']}

    def buscar(self, token, nombre):
        self.verificar_permiso(token, 'leer')
        usuario = self._usuarios.get(nombre)
        if usuario is None:
            raise ErrorCuenta('El usuario %r no existe.' % nombre)
        return self.resumen(usuario)

    def exportar_anonimo(self):
        pendientes = {}
        for nombre, datos in self._usuarios.items():
            pendientes[nombre] = {'correo': datos['correo'], 'rol': datos['rol']}
        return json.dumps(pendientes, ensure_ascii=False, sort_keys=True)

# --- Demo autocontenida (solo pruebas en memoria) ------------------------------
def demo():
    gestion = GestorCuentas()
    gestion.registrar('admin1', 'admin@demo.local', 'Clave1_segura', 'admin')
    gestion.registrar('ed1', 'ed@demo.local', 'Clave1_segura', 'editor')
    gestion.registrar('leo', 'leo@demo.local', 'Clave1_segura')
    t_admin = gestion.iniciar_sesion('admin1', 'Clave1_segura')
    assert gestion.tiene_permiso(t_admin, 'crear')
    gestion.cambiar_rol(t_admin, 'leo', 'editor')
    gestion.cambiar_contrasena(t_admin, 'Clave1_segura', 'Clave2_nueva')
    assert not gestion.tiene_permiso(t_admin, 'borrar') is False
    gestion.cerrar_sesion(t_admin)
    print('OK: flujo de pruebas superado sin red ni claves en claro.')

if __name__ == '__main__':
    demo()