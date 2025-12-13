ALTER TABLE subscriptions
    ADD COLUMN IF NOT EXISTS is_trial BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMP;

-- Backfill existing rows
UPDATE subscriptions
SET is_trial = COALESCE(is_trial, FALSE)
WHERE is_trial IS NULL;
