-- +goose Up
CREATE TABLE devices (
    id TEXT PRIMARY KEY,
    last_seen DATETIME,
    total_commits INTEGER DEFAULT 0,
    average_quality REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE commits (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    raw_samples BLOB NOT NULL,
    timestamps BLOB,
    quality REAL NOT NULL,
    test_frequency_passed INTEGER NOT NULL,
    test_frequency_ratio REAL,
    test_runs_passed INTEGER NOT NULL,
    test_runs_total INTEGER,
    test_runs_max_length INTEGER,
    test_chi_passed INTEGER NOT NULL,
    test_chi_value REAL,
    test_variance_passed INTEGER NOT NULL,
    test_variance_value REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- +goose Down
DROP TABLE commits;
DROP TABLE devices;
