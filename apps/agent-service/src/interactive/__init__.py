"""Interactive AI-versus-human courtroom runtime."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .service import (
        InteractiveExecutionResult,
        build_interactive_postgres_checkpointer,
        execute_interactive_trial,
    )

__all__ = [
    "InteractiveExecutionResult",
    "build_interactive_postgres_checkpointer",
    "execute_interactive_trial",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from . import service

        return getattr(service, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
