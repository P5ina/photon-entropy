package handlers

import (
	"net/http"

	"photon-entropy/game"

	"github.com/gin-gonic/gin"
)

// GameHandler handles game-related HTTP requests
type GameHandler struct {
	engine *game.Engine
}

// NewGameHandler creates a new game handler
func NewGameHandler(engine *game.Engine) *GameHandler {
	return &GameHandler{
		engine: engine,
	}
}

// CreateGameRequest represents a request to create a new game
type CreateGameRequest struct {
	TimeLimit    int `json:"time_limit"`
	ModulesCount int `json:"modules_count"`
	MaxStrikes   int `json:"max_strikes"`
}

// CreateGameResponse represents the response after creating a game
type CreateGameResponse struct {
	GameID string `json:"game_id"`
	Code   string `json:"code"`
}

// CreateGame handles POST /api/v1/game/create
func (h *GameHandler) CreateGame(c *gin.Context) {
	var req CreateGameRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		// Use defaults if no body provided
		req = CreateGameRequest{}
	}

	// Set defaults
	if req.TimeLimit <= 0 {
		req.TimeLimit = 300 // 5 minutes
	}
	if req.ModulesCount <= 0 {
		req.ModulesCount = 5
	}
	if req.MaxStrikes <= 0 {
		req.MaxStrikes = 3
	}

	// Validate
	if req.TimeLimit > 600 {
		req.TimeLimit = 600 // Max 10 minutes
	}
	if req.ModulesCount > 5 {
		req.ModulesCount = 5
	}

	g, err := h.engine.CreateGame(req.TimeLimit, req.ModulesCount, req.MaxStrikes)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, CreateGameResponse{
		GameID: g.ID,
		Code:   g.Code,
	})
}

// JoinGameRequest represents a request to join a game
type JoinGameRequest struct {
	Code string `json:"code" binding:"required"`
	Role string `json:"role" binding:"required"`
}

// JoinGame handles POST /api/v1/game/join
func (h *GameHandler) JoinGame(c *gin.Context) {
	var req JoinGameRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if req.Role != "bomb" && req.Role != "expert" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "role must be 'bomb' or 'expert'"})
		return
	}

	g, err := h.engine.JoinGame(req.Code, req.Role)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Return game state (without solutions)
	c.JSON(http.StatusOK, gin.H{
		"game_id":          g.ID,
		"code":             g.Code,
		"state":            g.State,
		"time_limit":       g.TimeLimit,
		"modules_count":    g.ModulesCount,
		"bomb_connected":   g.BombConnected,
		"expert_connected": g.ExpertConnected,
	})
}

// StartGame handles POST /api/v1/game/start
func (h *GameHandler) StartGame(c *gin.Context) {
	gameID := c.Query("game_id")
	if gameID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "game_id required"})
		return
	}

	if err := h.engine.StartGame(gameID); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	g, _ := h.engine.GetGame(gameID)

	c.JSON(http.StatusOK, gin.H{
		"status":     "started",
		"time_limit": g.TimeLimit,
		"modules":    h.sanitizeModules(g.Modules),
	})
}

// GetGameState handles GET /api/v1/game/state
func (h *GameHandler) GetGameState(c *gin.Context) {
	gameID := c.Query("game_id")
	code := c.Query("code")

	var g *game.Game
	var ok bool

	if gameID != "" {
		g, ok = h.engine.GetGame(gameID)
	} else if code != "" {
		g, ok = h.engine.GetGameByCode(code)
	} else {
		c.JSON(http.StatusBadRequest, gin.H{"error": "game_id or code required"})
		return
	}

	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "game not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"game_id":          g.ID,
		"code":             g.Code,
		"state":            g.State,
		"time_limit":       g.TimeLimit,
		"time_left":        g.TimeLeft,
		"strikes":          g.Strikes,
		"max_strikes":      g.MaxStrikes,
		"modules":          h.sanitizeModules(g.Modules),
		"bomb_connected":   g.BombConnected,
		"expert_connected": g.ExpertConnected,
		"created_at":       g.CreatedAt,
		"started_at":       g.StartedAt,
		"ended_at":         g.EndedAt,
	})
}

// GetManual handles GET /api/v1/game/manual
func (h *GameHandler) GetManual(c *gin.Context) {
	gameID := c.Query("game_id")
	code := c.Query("code")

	var g *game.Game
	var ok bool

	if gameID != "" {
		g, ok = h.engine.GetGame(gameID)
	} else if code != "" {
		g, ok = h.engine.GetGameByCode(code)
	} else {
		c.JSON(http.StatusBadRequest, gin.H{"error": "game_id or code required"})
		return
	}

	if !ok {
		c.JSON(http.StatusNotFound, gin.H{"error": "game not found"})
		return
	}

	manual, err := h.engine.GetManual(g.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Return manual with module types that are in this game
	activeModules := make([]string, 0)
	for _, m := range g.Modules {
		activeModules = append(activeModules, string(m.Type))
	}

	c.JSON(http.StatusOK, gin.H{
		"game_id":        g.ID,
		"seed":           g.Seed,
		"active_modules": activeModules,
		"manual":         manual,
	})
}

// ActionRequest represents a player action on a module
type ActionRequest struct {
	GameID   string      `json:"game_id" binding:"required"`
	ModuleID string      `json:"module_id" binding:"required"`
	Action   string      `json:"action" binding:"required"`
	Value    interface{} `json:"value"`
}

// ProcessAction handles POST /api/v1/game/action
func (h *GameHandler) ProcessAction(c *gin.Context) {
	var req ActionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	result, err := h.engine.ProcessAction(req.GameID, req.ModuleID, req.Action, req.Value)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get updated game state
	g, _ := h.engine.GetGame(req.GameID)

	c.JSON(http.StatusOK, gin.H{
		"result":    result,
		"game_state": g.State,
		"strikes":    g.Strikes,
		"time_left":  g.TimeLeft,
		"modules":    h.sanitizeModules(g.Modules),
	})
}

// sanitizeModules removes solutions from modules before sending to clients
func (h *GameHandler) sanitizeModules(modules []game.Module) []game.Module {
	sanitized := make([]game.Module, len(modules))
	for i, m := range modules {
		sanitized[i] = game.Module{
			ID:     m.ID,
			Type:   m.Type,
			State:  m.State,
			Config: m.Config,
			// Solution is intentionally omitted
		}
	}
	return sanitized
}
