'''Errores con los mismos nombres que moorcheh_sdk. Cualquier nombre pedido se crea como subclase de MoorchehError.'''


class MoorchehError(Exception):
    pass


class NamespaceNotFound(MoorchehError):
    pass


class ConflictError(MoorchehError):
    pass


class AuthenticationError(MoorchehError):
    pass


def __getattr__(name):
    if name[:1].isupper():
        cls = type(name, (MoorchehError,), {})
        globals()[name] = cls
        return cls
    raise AttributeError(name)
