"""YAIWES Secret Bank: cifrado en reposo, sesión única y broker de credenciales (S2)."""
from .vault import (  # noqa: F401
    InvalidPassphrase,
    NotFound,
    PermissionDenied,
    SessionExpired,
    UnlockedVault,
    Vault,
    VaultCorrupt,
    VaultError,
)
from .session import SessionManager  # noqa: F401
from .broker import SecretBroker  # noqa: F401
