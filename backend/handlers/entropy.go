package handlers

import (
	"database/sql"
	"encoding/binary"
	"encoding/hex"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/P5ina/photon-entropy/config"
	"github.com/P5ina/photon-entropy/db/sqlc"
	"github.com/P5ina/photon-entropy/entropy"
	"github.com/P5ina/photon-entropy/verifier"
	"github.com/P5ina/photon-entropy/ws"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type EntropyHandler struct {
	queries  *sqlc.Queries
	pool     *entropy.Pool
	verifier *verifier.Verifier
	config   *config.Config
	hub      *ws.Hub
}

func NewEntropyHandler(q *sqlc.Queries, p *entropy.Pool, v *verifier.Verifier, cfg *config.Config, hub *ws.Hub) *EntropyHandler {
	return &EntropyHandler{
		queries:  q,
		pool:     p,
		verifier: v,
		config:   cfg,
		hub:      hub,
	}
}

type SubmitRequest struct {
	DeviceID    string  `json:"device_id" binding:"required"`
	RawSamples  []int   `json:"raw_samples" binding:"required"`
	Timestamps  []int64 `json:"timestamps"`
	IsTooBright bool    `json:"is_too_bright"`
}

type SubmitResponse struct {
	ID       string                `json:"id"`
	Quality  float64               `json:"quality"`
	Tests    verifier.Tests        `json:"tests"`
	Accepted bool                  `json:"accepted"`
}

func (h *EntropyHandler) Submit(c *gin.Context) {
	var req SubmitRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if len(req.RawSamples) < h.config.Entropy.MinSamples {
		c.JSON(http.StatusBadRequest, gin.H{"error": "insufficient samples"})
		return
	}

	result := h.verifier.Verify(req.RawSamples)

	commitID := uuid.New().String()

	rawBytes := encodeIntSlice(req.RawSamples)
	timestampBytes := encodeInt64Slice(req.Timestamps)

	_, err := h.queries.CreateCommit(c, sqlc.CreateCommitParams{
		ID:                    commitID,
		DeviceID:              req.DeviceID,
		RawSamples:            rawBytes,
		Timestamps:            timestampBytes,
		Quality:               result.Quality,
		TestFrequencyPassed:   boolToInt64(result.Tests.Frequency.Passed),
		TestFrequencyRatio:    sql.NullFloat64{Float64: result.Tests.Frequency.Value, Valid: true},
		TestRunsPassed:        boolToInt64(result.Tests.Runs.Passed),
		TestRunsMaxLength:     sql.NullInt64{Int64: int64(result.Tests.Runs.Value), Valid: true},
		TestChiPassed:         boolToInt64(result.Tests.ChiSquare.Passed),
		TestChiValue:          sql.NullFloat64{Float64: result.Tests.ChiSquare.Value, Valid: true},
		TestVariancePassed:    boolToInt64(result.Tests.Variance.Passed),
		TestVarianceValue:     sql.NullFloat64{Float64: result.Tests.Variance.Value, Valid: true},
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to save commit"})
		return
	}

	count, _ := h.queries.CountCommitsByDevice(c, req.DeviceID)
	avgQuality, _ := h.queries.GetAverageQualityByDevice(c, req.DeviceID)

	h.queries.UpsertDevice(c, sqlc.UpsertDeviceParams{
		ID:             req.DeviceID,
		LastSeen:       sql.NullTime{Time: time.Now(), Valid: true},
		TotalCommits:   sql.NullInt64{Int64: count, Valid: true},
		AverageQuality: sql.NullFloat64{Float64: avgQuality, Valid: true},
		IsTooBright:    sql.NullInt64{Int64: boolToInt64(req.IsTooBright), Valid: true},
	})

	accepted := result.Quality >= h.config.Entropy.MinQuality
	if accepted {
		h.pool.Add(req.RawSamples)
	}

	// Broadcast WebSocket events
	if h.hub != nil {
		h.hub.BroadcastNewCommit(commitID, req.DeviceID, result.Quality, len(req.RawSamples), accepted, time.Now().UTC())
		h.hub.BroadcastDeviceUpdate(req.DeviceID, true, time.Now().UTC(), count, avgQuality, req.IsTooBright)
		h.hub.BroadcastPoolUpdate(h.pool.Size(), h.pool.MaxSize())
	}

	c.JSON(http.StatusOK, SubmitResponse{
		ID:       commitID,
		Quality:  result.Quality,
		Tests:    result.Tests,
		Accepted: accepted,
	})
}

type RandomResponse struct {
	Value       int64     `json:"value"`
	GeneratedAt time.Time `json:"generated_at"`
}

func (h *EntropyHandler) Random(c *gin.Context) {
	minVal, _ := strconv.ParseInt(c.DefaultQuery("min", "0"), 10, 64)
	maxVal, _ := strconv.ParseInt(c.DefaultQuery("max", "100"), 10, 64)

	if minVal >= maxVal {
		c.JSON(http.StatusBadRequest, gin.H{"error": "min must be less than max"})
		return
	}

	value, ok := h.pool.GetInt(minVal, maxVal)
	if !ok {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "insufficient entropy"})
		return
	}

	c.JSON(http.StatusOK, RandomResponse{
		Value:       value,
		GeneratedAt: time.Now().UTC(),
	})
}

type PasswordResponse struct {
	Password    string    `json:"password"`
	Length      int       `json:"length"`
	GeneratedAt time.Time `json:"generated_at"`
}

func (h *EntropyHandler) Password(c *gin.Context) {
	length, _ := strconv.Atoi(c.DefaultQuery("length", "16"))
	if length < 8 || length > 128 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "length must be between 8 and 128"})
		return
	}

	charset := "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
	bytes := h.pool.GetBytes(length)
	if bytes == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "insufficient entropy"})
		return
	}

	var password strings.Builder
	for _, b := range bytes {
		password.WriteByte(charset[int(b)%len(charset)])
	}

	c.JSON(http.StatusOK, PasswordResponse{
		Password:    password.String(),
		Length:      length,
		GeneratedAt: time.Now().UTC(),
	})
}

type UUIDResponse struct {
	UUID        string    `json:"uuid"`
	GeneratedAt time.Time `json:"generated_at"`
}

func (h *EntropyHandler) UUID(c *gin.Context) {
	bytes := h.pool.GetBytes(16)
	if bytes == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "insufficient entropy"})
		return
	}

	// Set version (4) and variant bits
	bytes[6] = (bytes[6] & 0x0f) | 0x40
	bytes[8] = (bytes[8] & 0x3f) | 0x80

	uuidStr := hex.EncodeToString(bytes[:4]) + "-" +
		hex.EncodeToString(bytes[4:6]) + "-" +
		hex.EncodeToString(bytes[6:8]) + "-" +
		hex.EncodeToString(bytes[8:10]) + "-" +
		hex.EncodeToString(bytes[10:16])

	c.JSON(http.StatusOK, UUIDResponse{
		UUID:        uuidStr,
		GeneratedAt: time.Now().UTC(),
	})
}

func encodeIntSlice(ints []int) []byte {
	buf := make([]byte, len(ints)*4)
	for i, v := range ints {
		binary.LittleEndian.PutUint32(buf[i*4:], uint32(v))
	}
	return buf
}

func encodeInt64Slice(ints []int64) []byte {
	if len(ints) == 0 {
		return nil
	}
	buf := make([]byte, len(ints)*8)
	for i, v := range ints {
		binary.LittleEndian.PutUint64(buf[i*8:], uint64(v))
	}
	return buf
}

func boolToInt64(b bool) int64 {
	if b {
		return 1
	}
	return 0
}
