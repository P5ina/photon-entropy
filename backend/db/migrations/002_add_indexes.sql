-- +goose Up
CREATE INDEX idx_commits_device_id ON commits(device_id);
CREATE INDEX idx_commits_created_at ON commits(created_at);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);

-- +goose Down
DROP INDEX idx_commits_device_id;
DROP INDEX idx_commits_created_at;
DROP INDEX idx_devices_last_seen;
