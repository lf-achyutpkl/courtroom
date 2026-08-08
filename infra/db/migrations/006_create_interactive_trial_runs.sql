CREATE TABLE interactive_trial_runs (
    id UUID PRIMARY KEY,
    case_file_id UUID NOT NULL REFERENCES case_files(id),
    human_attorney_side VARCHAR NOT NULL CHECK (human_attorney_side IN ('prosecution', 'defense')),
    langgraph_thread_id VARCHAR NOT NULL UNIQUE,
    status VARCHAR NOT NULL CHECK (status IN ('queued', 'running', 'awaiting_human', 'completed', 'failed')),
    state_snapshot JSONB,
    transcript_snapshot JSONB,
    result_snapshot JSONB,
    pending_turn_id UUID,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_interactive_trial_runs_case_file_id ON interactive_trial_runs(case_file_id);
CREATE INDEX idx_interactive_trial_runs_status ON interactive_trial_runs(status);

CREATE TABLE participant_turns (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES interactive_trial_runs(id),
    turn_number INTEGER NOT NULL,
    scene VARCHAR NOT NULL,
    attorney_side VARCHAR NOT NULL CHECK (attorney_side IN ('prosecution', 'defense')),
    status VARCHAR NOT NULL CHECK (status IN ('pending_upload', 'submitted', 'resuming', 'consumed')),
    object_bucket VARCHAR,
    object_key VARCHAR,
    content_type VARCHAR,
    size_bytes INTEGER,
    checksum VARCHAR,
    submitted_at TIMESTAMPTZ,
    resumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(run_id, turn_number)
);
CREATE INDEX idx_participant_turns_run_id ON participant_turns(run_id);
