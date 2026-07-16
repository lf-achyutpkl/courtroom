from __future__ import annotations

from ..core.config import get_database_url
from ..models.completions import SimulationCompletion
from ..repositories.simulation_runs import PostgresSimulationRunWriter


def apply_completion_message(payload: dict[str, object]) -> None:
    apply_completion(
        SimulationCompletion.model_validate(payload),
        runs=PostgresSimulationRunWriter(get_database_url()),
    )


def apply_completion(
    completion: SimulationCompletion,
    runs: PostgresSimulationRunWriter,
) -> None:
    if completion.status == "completed":
        if completion.result is None:
            raise ValueError("Completed simulation messages must include a result.")
        runs.mark_completed(completion.simulation_run_id, completion.result)
        return

    runs.mark_failed(
        completion.simulation_run_id,
        completion.error_message or "Simulation failed without an error message.",
    )
