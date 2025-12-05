-- name: CreateDevice :one
INSERT INTO devices (id)
VALUES (?)
RETURNING *;

-- name: GetDevice :one
SELECT * FROM devices
WHERE id = ? LIMIT 1;

-- name: UpdateDeviceStats :exec
UPDATE devices
SET last_seen = ?,
    total_commits = ?,
    average_quality = ?
WHERE id = ?;

-- name: UpsertDevice :one
INSERT INTO devices (id, last_seen, total_commits, average_quality, is_too_bright)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    last_seen = excluded.last_seen,
    total_commits = excluded.total_commits,
    average_quality = excluded.average_quality,
    is_too_bright = excluded.is_too_bright
RETURNING *;

-- name: GetAllDevices :many
SELECT * FROM devices
ORDER BY last_seen DESC;

-- name: GetOnlineDevices :many
SELECT * FROM devices
WHERE last_seen > datetime('now', '-2 minutes')
ORDER BY last_seen DESC;

-- name: CountDevices :one
SELECT COUNT(*) FROM devices;
