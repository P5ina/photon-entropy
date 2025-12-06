package main

import (
	"database/sql"
	"embed"
	"log"
	"os"
	"path/filepath"
	"time"

	"photon-entropy/config"
	"photon-entropy/db/sqlc"
	"photon-entropy/game"
	"photon-entropy/handlers"
	"photon-entropy/ws"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/pressly/goose/v3"
	_ "modernc.org/sqlite"
)

//go:embed db/migrations/*.sql
var embedMigrations embed.FS

func main() {
	godotenv.Load()

	env := config.LoadEnv()
	cfg, err := config.Load("config.yaml")
	if err != nil {
		log.Printf("Warning: Failed to load config.yaml, using defaults: %v", err)
		cfg = config.DefaultConfig()
	}
	_ = cfg // Config available for future use

	if err := os.MkdirAll(filepath.Dir(env.DatabasePath), 0755); err != nil {
		log.Fatalf("Failed to create data directory: %v", err)
	}

	db, err := sql.Open("sqlite", env.DatabasePath)
	if err != nil {
		log.Fatalf("Failed to open database: %v", err)
	}
	defer db.Close()

	goose.SetBaseFS(embedMigrations)
	if err := goose.SetDialect("sqlite3"); err != nil {
		log.Fatalf("Failed to set goose dialect: %v", err)
	}
	if err := goose.Up(db, "db/migrations"); err != nil {
		log.Fatalf("Failed to run migrations: %v", err)
	}

	_ = sqlc.New(db) // Keep for potential future DB usage

	// Initialize WebSocket hub
	hub := ws.NewHub()
	go hub.Run()

	// Initialize game engine
	gameEngine := game.NewEngine()

	// Connect game events to WebSocket broadcasts
	gameEngine.OnGameEvent = func(event game.GameEvent) {
		switch event.Type {
		case game.EventGameCreated:
			hub.BroadcastGameEvent(ws.MessageTypeGameCreated, map[string]any{
				"game_id": event.GameID,
				"data":    event.Data,
			})
		case game.EventPlayerJoined:
			hub.BroadcastGameEvent(ws.MessageTypePlayerJoined, map[string]any{
				"game_id": event.GameID,
				"data":    event.Data,
			})
		case game.EventGameStarted:
			hub.BroadcastGameEvent(ws.MessageTypeGameStarted, map[string]any{
				"game_id": event.GameID,
				"data":    event.Data,
			})
		case game.EventTimerTick:
			if timeLeft, ok := event.Data["time_left"].(int); ok {
				hub.BroadcastTimerTick(event.GameID, timeLeft)
			}
		case game.EventModuleAction:
			hub.BroadcastGameEvent(ws.MessageTypeModuleAction, map[string]any{
				"game_id":   event.GameID,
				"module_id": event.ModuleID,
				"data":      event.Data,
			})
		case game.EventModuleSolved:
			hub.BroadcastModuleSolved(event.GameID, event.ModuleID)
		case game.EventStrike:
			strikes, _ := event.Data["strikes"].(int)
			maxStrikes, _ := event.Data["max_strikes"].(int)
			reason, _ := event.Data["reason"].(string)
			hub.BroadcastStrike(event.GameID, event.ModuleID, reason, strikes, maxStrikes)
		case game.EventGameWon:
			timeRemaining, _ := event.Data["time_remaining"].(int)
			hub.BroadcastGameEnd(event.GameID, true, "all_modules_solved", timeRemaining)
		case game.EventGameLost:
			reason, _ := event.Data["reason"].(string)
			hub.BroadcastGameEnd(event.GameID, false, reason, 0)
		}
	}

	// Initialize handlers
	gameHandler := handlers.NewGameHandler(gameEngine)
	wsHandler := handlers.NewWebSocketHandler(hub)

	if env.GinMode == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	r := gin.Default()

	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status":    "ok",
			"timestamp": time.Now().UTC().Format(time.RFC3339),
		})
	})

	// WebSocket endpoint
	r.GET("/ws", wsHandler.Handle)

	api := r.Group("/api/v1")
	{
		// Game endpoints
		api.POST("/game/create", gameHandler.CreateGame)
		api.POST("/game/join", gameHandler.JoinGame)
		api.POST("/game/start", gameHandler.StartGame)
		api.GET("/game/state", gameHandler.GetGameState)
		api.GET("/game/manual", gameHandler.GetManual)
		api.POST("/game/action", gameHandler.ProcessAction)
	}

	log.Printf("Starting Bomb Defusal server on %s", env.ServerAddress())
	if err := r.Run(env.ServerAddress()); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
