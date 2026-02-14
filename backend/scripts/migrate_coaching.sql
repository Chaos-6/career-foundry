-- Migration: Add coaching relationships and coach notes
-- Run against the existing PostgreSQL database.
-- Safe to re-run: all statements use IF NOT EXISTS.

-- 1. Coaching relationships table
CREATE TABLE IF NOT EXISTS coaching_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',
    invited_email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    CONSTRAINT uq_coaching_pair UNIQUE (coach_id, student_id)
);

-- 2. Indexes for fast lookups
CREATE INDEX IF NOT EXISTS ix_coaching_coach_id
    ON coaching_relationships(coach_id);
CREATE INDEX IF NOT EXISTS ix_coaching_student_id
    ON coaching_relationships(student_id);
CREATE INDEX IF NOT EXISTS ix_coaching_status
    ON coaching_relationships(status);
CREATE INDEX IF NOT EXISTS ix_coaching_invited_email
    ON coaching_relationships(invited_email);

-- 3. Coach notes on evaluations (JSONB for flexible structure)
ALTER TABLE evaluations
    ADD COLUMN IF NOT EXISTS coach_notes JSONB;
