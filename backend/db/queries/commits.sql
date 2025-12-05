-- name: CreateCommit :one
INSERT INTO commits (
    id, device_id, raw_samples, timestamps, quality,
    test_frequency_passed, test_frequency_ratio,
    test_runs_passed, test_runs_total, test_runs_max_length,
    test_chi_passed, test_chi_value,
    test_variance_passed, test_variance_value
) VALUES (
    ?, ?, ?, ?, ?,
    ?, ?,
    ?, ?, ?,
    ?, ?,
    ?, ?
)
RETURNING *;

-- name: GetCommitByID :one
SELECT * FROM commits
WHERE id = ? LIMIT 1;

-- name: GetCommitsByDevice :many
SELECT * FROM commits
WHERE device_id = ?
ORDER BY created_at DESC
LIMIT ?;

-- name: GetRecentCommits :many
SELECT * FROM commits
ORDER BY created_at DESC
LIMIT ?;

-- name: CountCommitsByDevice :one
SELECT COUNT(*) FROM commits
WHERE device_id = ?;

-- name: GetAverageQualityByDevice :one
SELECT CAST(COALESCE(AVG(quality), 0) AS REAL) FROM commits
WHERE device_id = ?;

-- name: CountTotalCommits :one
SELECT COUNT(*) FROM commits;

-- name: GetTotalSamplesCount :one
SELECT CAST(COALESCE(SUM(LENGTH(raw_samples) / 4), 0) AS INTEGER) FROM commits;
