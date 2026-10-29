import json
import sys

import click

from ..utils.salida import emitir
from .runtime import Orquestador


@click.group('memoria')
def memoria_group():
    '''Guardar, cargar y buscar memoria en el pool de motores.'''


@memoria_group.command('guardar')
@click.argument('scope')
@click.argument('key')
@click.argument('data_json')
@click.pass_context
def guardar(ctx, scope, key, data_json):
    '''Guarda DATA_JSON en todos los motores conectados que permiten escribir.'''
    r = Orquestador().guardar(scope, key, json.loads(data_json))
    emitir(ctx, r)
    if not r['ok']:
        sys.exit(1)


@memoria_group.command('cargar')
@click.argument('scope')
@click.argument('key')
@click.pass_context
def cargar(ctx, scope, key):
    '''Lee (scope, key) del primer motor, por orden de prioridad, que lo tenga.'''
    emitir(ctx, Orquestador().cargar(scope, key))


@memoria_group.command('buscar')
@click.argument('scope')
@click.argument('query')
@click.option('--k', default=10, show_default=True)
@click.pass_context
def buscar(ctx, scope, query, k):
    '''Busca en todos los motores y fusiona el resultado sin repetidos.'''
    emitir(ctx, Orquestador().buscar(scope, query, k))
