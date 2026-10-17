'''CLI-Anything harness de memoria y almacenamiento YAIWES: Click CLI + REPL. Determinista, sin LLM.'''
import shlex

import click

from .core.memoria import memoria_group
from .core.motores import motores_group


@click.group(invoke_without_command=True)
@click.option('--json', 'use_json', is_flag=True, default=False, help='Salida en JSON')
@click.pass_context
def cli(ctx, use_json):
    '''Orquestador de memoria y almacenamiento (graphiti, agentdb, graphify, memanto, falkordb, postgresql).'''
    ctx.ensure_object(dict)
    ctx.obj['json'] = use_json
    if ctx.invoked_subcommand is None:
        _repl(ctx)


cli.add_command(memoria_group)
cli.add_command(motores_group)


def _repl(ctx):
    click.echo('memoria> escribe un comando (ej: motores estado); exit para salir')
    while True:
        try:
            linea = input('memoria> ').strip()
        except EOFError:
            break
        if linea in ('exit', 'quit'):
            break
        if linea:
            try:
                cli.main(args=shlex.split(linea), prog_name='memoria', standalone_mode=False, obj=ctx.obj)
            except SystemExit:
                pass
            except Exception as exc:  # noqa: BLE001
                click.echo('error: ' + str(exc))


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
