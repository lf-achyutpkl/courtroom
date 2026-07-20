ALTER TABLE case_files
    RENAME COLUMN case_file TO case_json;

ALTER TABLE case_files
    ADD COLUMN case_title TEXT NOT NULL DEFAULT '',
    ADD COLUMN status TEXT NOT NULL DEFAULT 'draft',
    ADD COLUMN revision INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

UPDATE case_files
SET
    case_title = COALESCE(case_json ->> 'case_title', charge_or_claim),
    case_json = jsonb_set(
        jsonb_set(
            case_json,
            '{case_title}',
            to_jsonb(COALESCE(case_json ->> 'case_title', charge_or_claim)),
            true
        ),
        '{disputed_facts}',
        COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'fact_id',
                        'F' || ordinality,
                        'text',
                        fact_text
                    )
                    ORDER BY ordinality
                )
                FROM jsonb_array_elements_text(
                    COALESCE(case_json -> 'disputed_facts', '[]'::jsonb)
                ) WITH ORDINALITY AS fact_values(fact_text, ordinality)
            ),
            '[]'::jsonb
        ),
        true
    ),
    updated_at = created_at
WHERE case_title = '';
