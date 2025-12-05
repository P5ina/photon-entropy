-- +goose Up
ALTER TABLE devices ADD COLUMN is_too_bright INTEGER DEFAULT 0;

-- +goose Down
ALTER TABLE devices DROP COLUMN is_too_bright;
