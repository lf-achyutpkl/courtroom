ALTER TABLE interactive_trial_runs
ADD COLUMN human_witness_plan JSONB NOT NULL DEFAULT '[]'::jsonb;
