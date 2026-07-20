CREATE TABLE case_file_messages (
    id UUID PRIMARY KEY,
    case_file_id UUID NOT NULL REFERENCES case_files(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('human', 'ai')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_case_file_messages_case_file_id
    ON case_file_messages(case_file_id);

CREATE INDEX idx_case_file_messages_created_at
    ON case_file_messages(created_at);
