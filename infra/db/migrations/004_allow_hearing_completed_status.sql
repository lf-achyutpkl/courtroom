ALTER TABLE simulation_runs
    DROP CONSTRAINT IF EXISTS chk_simulation_runs_status;

ALTER TABLE simulation_runs
    ADD CONSTRAINT chk_simulation_runs_status CHECK (
        status IN (
            'pending',
            'running',
            'hearing_completed',
            'generating_audio',
            'completed',
            'failed'
        )
    );
