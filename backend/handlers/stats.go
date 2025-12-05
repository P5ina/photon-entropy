package handlers

import (
	"net/http"

	"github.com/P5ina/photon-entropy/db/sqlc"
	"github.com/P5ina/photon-entropy/entropy"
	"github.com/gin-gonic/gin"
)

type StatsHandler struct {
	queries *sqlc.Queries
	pool    *entropy.Pool
}

func NewStatsHandler(q *sqlc.Queries, p *entropy.Pool) *StatsHandler {
	return &StatsHandler{
		queries: q,
		pool:    p,
	}
}

type StatsResponse struct {
	TotalDevices     int64 `json:"total_devices"`
	TotalCommits     int64 `json:"total_commits"`
	TotalSamples     int64 `json:"total_samples"`
	EntropyPoolSize  int   `json:"entropy_pool_size"`
}

func (h *StatsHandler) Stats(c *gin.Context) {
	totalDevices, _ := h.queries.CountDevices(c)
	totalCommits, _ := h.queries.CountTotalCommits(c)
	totalSamples, _ := h.queries.GetTotalSamplesCount(c)

	c.JSON(http.StatusOK, StatsResponse{
		TotalDevices:    totalDevices,
		TotalCommits:    totalCommits,
		TotalSamples:    totalSamples,
		EntropyPoolSize: h.pool.Size(),
	})
}
