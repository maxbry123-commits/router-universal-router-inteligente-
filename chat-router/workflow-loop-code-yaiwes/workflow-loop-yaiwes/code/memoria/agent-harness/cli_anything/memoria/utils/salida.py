import json

import click


def emitir(ctx, data) -> None:
    if ctx.obj.get('json'):
        click.echo(json.dumps(data, ensure_ascii=False, sort_keys=True))
    else:
        click.echo(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
