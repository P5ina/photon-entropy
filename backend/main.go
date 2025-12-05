package main

import (
	"database/sql"
	"embed"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/P5ina/photon-entropy/config"
	"github.com/P5ina/photon-entropy/db/sqlc"
	"github.com/P5ina/photon-entropy/entropy"
	"github.com/P5ina/photon-entropy/handlers"
	"github.com/P5ina/photon-entropy/verifier"
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
		log.Fatalf("Failed to load config: %v", err)
	}

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

	queries := sqlc.New(db)

	pool := entropy.NewPool(cfg.Entropy.PoolSize)
	v := verifier.New()

	entropyHandler := handlers.NewEntropyHandler(queries, pool, v, cfg)
	deviceHandler := handlers.NewDeviceHandler(queries, cfg)
	statsHandler := handlers.NewStatsHandler(queries, pool)

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

	api := r.Group("/api/v1")
	{
		// Entropy endpoints
		api.POST("/entropy/submit", entropyHandler.Submit)
		api.GET("/entropy/random", entropyHandler.Random)
		api.GET("/entropy/password", entropyHandler.Password)
		api.GET("/entropy/uuid", entropyHandler.UUID)

		// Device endpoints
		api.GET("/device/status", deviceHandler.Status)
		api.GET("/device/history", deviceHandler.History)

		// Stats endpoint
		api.GET("/stats", statsHandler.Stats)
	}

	log.Printf("Starting server on %s", env.ServerAddress())
	if err := r.Run(env.ServerAddress()); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
