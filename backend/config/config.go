package config

import (
	"os"
	"strconv"
	"time"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Entropy EntropyConfig `yaml:"entropy"`
	Device  DeviceConfig  `yaml:"device"`
}

type EntropyConfig struct {
	MinSamples int     `yaml:"min_samples"`
	MinQuality float64 `yaml:"min_quality"`
	PoolSize   int     `yaml:"pool_size"`
}

type DeviceConfig struct {
	OfflineTimeout int `yaml:"offline_timeout"`
}

type Env struct {
	DatabasePath string
	ServerHost   string
	ServerPort   int
	GinMode      string
}

func Load(path string) (*Config, error) {
	cfg := &Config{
		Entropy: EntropyConfig{
			MinSamples: 100,
			MinQuality: 0.5,
			PoolSize:   4096,
		},
		Device: DeviceConfig{
			OfflineTimeout: 120,
		},
	}

	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return cfg, nil
		}
		return nil, err
	}

	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, err
	}

	return cfg, nil
}

func LoadEnv() *Env {
	port := 8080
	if v := os.Getenv("SERVER_PORT"); v != "" {
		if p, err := strconv.Atoi(v); err == nil {
			port = p
		}
	}

	return &Env{
		DatabasePath: getEnvOrDefault("DATABASE_PATH", "./data/photon.db"),
		ServerHost:   getEnvOrDefault("SERVER_HOST", "0.0.0.0"),
		ServerPort:   port,
		GinMode:      getEnvOrDefault("GIN_MODE", "debug"),
	}
}

func (e *Env) ServerAddress() string {
	return e.ServerHost + ":" + strconv.Itoa(e.ServerPort)
}

func (c *Config) GetOfflineTimeout() time.Duration {
	return time.Duration(c.Device.OfflineTimeout) * time.Second
}

func getEnvOrDefault(key, defaultValue string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return defaultValue
}
