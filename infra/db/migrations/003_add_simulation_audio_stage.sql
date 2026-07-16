ALTER TABLE simulation_runs
    ADD COLUMN IF NOT EXISTS audio_manifest JSONB,
    ADD COLUMN IF NOT EXISTS audio_storage JSONB;

ALTER TABLE simulation_runs
    DROP CONSTRAINT IF EXISTS chk_simulation_runs_status;

ALTER TABLE simulation_runs
    ADD CONSTRAINT chk_simulation_runs_status CHECK (
        status IN ('pending', 'running', 'generating_audio', 'completed', 'failed')
    );
