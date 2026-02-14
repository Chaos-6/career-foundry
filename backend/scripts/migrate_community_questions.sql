-- Migration: Add community question submission and moderation fields
-- Run once against existing databases (create_all won't ALTER existing tables)

-- Question moderation fields
ALTER TABLE questions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved';
ALTER TABLE questions ADD COLUMN IF NOT EXISTS submitted_by_user_id UUID REFERENCES users(id);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS moderation_notes TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS moderated_at TIMESTAMPTZ;

-- Set all existing curated questions to 'approved' (should already be via default)
UPDATE questions SET status = 'approved' WHERE status IS NULL;

-- User moderator flag
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_moderator BOOLEAN DEFAULT FALSE;

-- Index for efficient moderation queue queries
CREATE INDEX IF NOT EXISTS idx_questions_status ON questions(status);
CREATE INDEX IF NOT EXISTS idx_questions_submitted_by ON questions(submitted_by_user_id);
