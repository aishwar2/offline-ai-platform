-- Optional seed script for development environments only.
-- Do NOT use default credentials in production.
-- Password hash below corresponds to: Admin@12345 (generate fresh via backend CLI in prod).

INSERT INTO users (email, username, full_name, hashed_password, role, is_active, preferred_model)
VALUES (
    'admin@offline-ai.local',
    'admin',
    'Platform Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIwz3j8q2K',
    'admin',
    TRUE,
    'tinyllama'
)
ON CONFLICT (email) DO NOTHING;
