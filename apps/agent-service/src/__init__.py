from .utils import types
from .utils.state import TrialState
from .utils.types import RunTrialRequest, RunTrialResponse

__all__ = [
    "types",
    "llm",
    "TrialState",
    "RunTrialRequest",
    "RunTrialResponse",
    "run_trial",
    "invoke",
]


def __getattr__(name: str):
    if name == "llm":
        from .utils import llm

        return llm
    if name == "run_trial":
        from .service import run_trial

        return run_trial
    if name == "invoke":
        from .utils.llm import invoke_structured

        return invoke_structured
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
