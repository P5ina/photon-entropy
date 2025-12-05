package handlers

import (
	"database/sql"
	"net/http"
	"strconv"
	"time"

	"github.com/P5ina/photon-entropy/config"
	"github.com/P5ina/photon-entropy/db/sqlc"
	"github.com/P5ina/photon-entropy/ws"
	"github.com/gin-gonic/gin"
)

type DeviceHandler struct {
	queries *sqlc.Queries
	config  *config.Config
	hub     *ws.Hub
}

func NewDeviceHandler(q *sqlc.Queries, cfg *config.Config, hub *ws.Hub) *DeviceHandler {
	return &DeviceHandler{
		queries: q,
		config:  cfg,
		hub:     hub,
	}
}

type DeviceStatusResponse struct {
	DeviceID       string    `json:"device_id"`
	IsOnline       bool      `json:"is_online"`
	LastSeen       time.Time `json:"last_seen"`
	TotalCommits   int64     `json:"total_commits"`
	AverageQuality float64   `json:"average_quality"`
	EntropyPool    int       `json:"entropy_pool_size"`
	IsTooBright    bool      `json:"is_too_bright"`
}

func (h *DeviceHandler) Status(c *gin.Context) {
	deviceID := c.Query("device_id")
	if deviceID == "" {
		devices, err := h.queries.GetAllDevices(c)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get devices"})
			return
		}

		if len(devices) == 0 {
			c.JSON(http.StatusNotFound, gin.H{"error": "no devices found"})
			return
		}

		responses := make([]DeviceStatusResponse, len(devices))
		for i, d := range devices {
			isOnline := false
			if d.LastSeen.Valid {
				isOnline = time.Since(d.LastSeen.Time) < h.config.GetOfflineTimeout()
			}

			responses[i] = DeviceStatusResponse{
				DeviceID:       d.ID,
				IsOnline:       isOnline,
				LastSeen:       d.LastSeen.Time,
				TotalCommits:   d.TotalCommits.Int64,
				AverageQuality: d.AverageQuality.Float64,
				IsTooBright:    d.IsTooBright.Int64 == 1,
			}
		}

		c.JSON(http.StatusOK, responses)
		return
	}

	device, err := h.queries.GetDevice(c, deviceID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "device not found"})
		return
	}

	isOnline := false
	if device.LastSeen.Valid {
		isOnline = time.Since(device.LastSeen.Time) < h.config.GetOfflineTimeout()
	}

	c.JSON(http.StatusOK, DeviceStatusResponse{
		DeviceID:       device.ID,
		IsOnline:       isOnline,
		LastSeen:       device.LastSeen.Time,
		TotalCommits:   device.TotalCommits.Int64,
		AverageQuality: device.AverageQuality.Float64,
		IsTooBright:    device.IsTooBright.Int64 == 1,
	})
}

type CommitHistoryItem struct {
	ID        string    `json:"id"`
	DeviceID  string    `json:"device_id"`
	Quality   float64   `json:"quality"`
	Samples   int       `json:"samples"`
	CreatedAt time.Time `json:"created_at"`
	Tests     struct {
		FrequencyPassed bool `json:"frequency_passed"`
		RunsPassed      bool `json:"runs_passed"`
		ChiPassed       bool `json:"chi_passed"`
		VariancePassed  bool `json:"variance_passed"`
	} `json:"tests"`
}

func (h *DeviceHandler) History(c *gin.Context) {
	deviceID := c.Query("device_id")
	limitStr := c.DefaultQuery("limit", "20")
	limit, _ := strconv.ParseInt(limitStr, 10, 32)
	if limit <= 0 || limit > 100 {
		limit = 20
	}

	var commits []sqlc.Commit
	var err error

	if deviceID != "" {
		commits, err = h.queries.GetCommitsByDevice(c, sqlc.GetCommitsByDeviceParams{
			DeviceID: deviceID,
			Limit:    int64(limit),
		})
	} else {
		commits, err = h.queries.GetRecentCommits(c, int64(limit))
	}

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get history"})
		return
	}

	items := make([]CommitHistoryItem, len(commits))
	for i, commit := range commits {
		item := CommitHistoryItem{
			ID:        commit.ID,
			DeviceID:  commit.DeviceID,
			Quality:   commit.Quality,
			Samples:   len(commit.RawSamples) / 4,
			CreatedAt: commit.CreatedAt.Time,
		}
		item.Tests.FrequencyPassed = commit.TestFrequencyPassed == 1
		item.Tests.RunsPassed = commit.TestRunsPassed == 1
		item.Tests.ChiPassed = commit.TestChiPassed == 1
		item.Tests.VariancePassed = commit.TestVariancePassed == 1
		items[i] = item
	}

	c.JSON(http.StatusOK, items)
}

type UpdateStatusRequest struct {
	DeviceID    string `json:"device_id" binding:"required"`
	IsTooBright bool   `json:"is_too_bright"`
}

func (h *DeviceHandler) UpdateStatus(c *gin.Context) {
	var req UpdateStatusRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	device, err := h.queries.GetDevice(c, req.DeviceID)
	if err != nil {
		// Device doesn't exist, create it
		device, err = h.queries.UpsertDevice(c, sqlc.UpsertDeviceParams{
			ID:          req.DeviceID,
			LastSeen:    sql.NullTime{Time: time.Now(), Valid: true},
			IsTooBright: sql.NullInt64{Int64: boolToInt(req.IsTooBright), Valid: true},
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create device"})
			return
		}
	} else {
		// Update existing device
		device, err = h.queries.UpsertDevice(c, sqlc.UpsertDeviceParams{
			ID:             req.DeviceID,
			LastSeen:       sql.NullTime{Time: time.Now(), Valid: true},
			TotalCommits:   device.TotalCommits,
			AverageQuality: device.AverageQuality,
			IsTooBright:    sql.NullInt64{Int64: boolToInt(req.IsTooBright), Valid: true},
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to update device"})
			return
		}
	}

	// Broadcast via WebSocket
	if h.hub != nil {
		h.hub.BroadcastDeviceUpdate(
			device.ID,
			true,
			time.Now().UTC(),
			device.TotalCommits.Int64,
			device.AverageQuality.Float64,
			req.IsTooBright,
		)
	}

	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func boolToInt(b bool) int64 {
	if b {
		return 1
	}
	return 0
}
