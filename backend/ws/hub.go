package ws

import (
	"encoding/json"
	"sync"
	"time"
)

type MessageType string

const (
	MessageTypePoolUpdate   MessageType = "pool_update"
	MessageTypeDeviceUpdate MessageType = "device_update"
	MessageTypeNewCommit    MessageType = "new_commit"
	MessageTypeStats        MessageType = "stats_update"
)

type Message struct {
	Type      MessageType `json:"type"`
	Data      any         `json:"data"`
	Timestamp time.Time   `json:"timestamp"`
}

type PoolUpdateData struct {
	Size    int `json:"size"`
	MaxSize int `json:"max_size"`
}

type DeviceUpdateData struct {
	DeviceID       string    `json:"device_id"`
	IsOnline       bool      `json:"is_online"`
	LastSeen       time.Time `json:"last_seen"`
	TotalCommits   int64     `json:"total_commits"`
	AverageQuality float64   `json:"average_quality"`
	IsTooBright    bool      `json:"is_too_bright"`
}

type NewCommitData struct {
	ID        string    `json:"id"`
	DeviceID  string    `json:"device_id"`
	Quality   float64   `json:"quality"`
	Samples   int       `json:"samples"`
	Accepted  bool      `json:"accepted"`
	CreatedAt time.Time `json:"created_at"`
}

type StatsUpdateData struct {
	TotalDevices    int `json:"total_devices"`
	TotalCommits    int `json:"total_commits"`
	TotalSamples    int `json:"total_samples"`
	EntropyPoolSize int `json:"entropy_pool_size"`
}

type Hub struct {
	clients    map[*Client]bool
	broadcast  chan []byte
	register   chan *Client
	unregister chan *Client
	mu         sync.RWMutex
}

func NewHub() *Hub {
	return &Hub{
		clients:    make(map[*Client]bool),
		broadcast:  make(chan []byte, 256),
		register:   make(chan *Client),
		unregister: make(chan *Client),
	}
}

func (h *Hub) Run() {
	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			h.clients[client] = true
			h.mu.Unlock()

		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				close(client.send)
			}
			h.mu.Unlock()

		case message := <-h.broadcast:
			h.mu.RLock()
			for client := range h.clients {
				select {
				case client.send <- message:
				default:
					close(client.send)
					delete(h.clients, client)
				}
			}
			h.mu.RUnlock()
		}
	}
}

func (h *Hub) Register(client *Client) {
	h.register <- client
}

func (h *Hub) Unregister(client *Client) {
	h.unregister <- client
}

func (h *Hub) Broadcast(msg Message) {
	msg.Timestamp = time.Now().UTC()
	data, err := json.Marshal(msg)
	if err != nil {
		return
	}
	h.broadcast <- data
}

func (h *Hub) BroadcastPoolUpdate(size, maxSize int) {
	h.Broadcast(Message{
		Type: MessageTypePoolUpdate,
		Data: PoolUpdateData{
			Size:    size,
			MaxSize: maxSize,
		},
	})
}

func (h *Hub) BroadcastDeviceUpdate(deviceID string, isOnline bool, lastSeen time.Time, totalCommits int64, avgQuality float64, isTooBright bool) {
	h.Broadcast(Message{
		Type: MessageTypeDeviceUpdate,
		Data: DeviceUpdateData{
			DeviceID:       deviceID,
			IsOnline:       isOnline,
			LastSeen:       lastSeen,
			TotalCommits:   totalCommits,
			AverageQuality: avgQuality,
			IsTooBright:    isTooBright,
		},
	})
}

func (h *Hub) BroadcastNewCommit(id, deviceID string, quality float64, samples int, accepted bool, createdAt time.Time) {
	h.Broadcast(Message{
		Type: MessageTypeNewCommit,
		Data: NewCommitData{
			ID:        id,
			DeviceID:  deviceID,
			Quality:   quality,
			Samples:   samples,
			Accepted:  accepted,
			CreatedAt: createdAt,
		},
	})
}

func (h *Hub) BroadcastStats(totalDevices, totalCommits, totalSamples, poolSize int) {
	h.Broadcast(Message{
		Type: MessageTypeStats,
		Data: StatsUpdateData{
			TotalDevices:    totalDevices,
			TotalCommits:    totalCommits,
			TotalSamples:    totalSamples,
			EntropyPoolSize: poolSize,
		},
	})
}

func (h *Hub) ClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}
