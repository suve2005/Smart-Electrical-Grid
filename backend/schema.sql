
-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Application roles
CREATE TABLE IF NOT EXISTS roles (
    id SMALLINT PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE
);

INSERT INTO roles (id, name)
VALUES
    (1, 'admin'),
    (2, 'engineer')
ON CONFLICT (name) DO NOTHING;


-- Application user profiles
CREATE TABLE IF NOT EXISTS app_users (
    firebase_uid VARCHAR(128) PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    nic_hash CHAR(64) NOT NULL UNIQUE,
    role_id SMALLINT NOT NULL DEFAULT 2
        REFERENCES roles(id),
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
