import click

from ..utils.salida import emitir
from .runtime import Orquestador


@click.group('motores')
def motores_group():
    '''Estado del pool de motores de memoria y almacenamiento.'''


@motores_group.command('estado')
@click.pass_context
def estado(ctx):
    '''CONNECTED o GAP de cada motor, con el motivo.'''
    emitir(ctx, {'motores': Orquestador().estado()})
