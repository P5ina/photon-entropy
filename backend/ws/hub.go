package ws

import (
	"encoding/json"
	"sync"
	"time"
)

type MessageType string

const (
	// Game events
	MessageTypeGameCreated  MessageType = "game_created"
	MessageTypePlayerJoined MessageType = "player_joined"
	MessageTypeGameStarted  MessageType = "game_started"
	MessageTypeTimerTick    MessageType = "timer_tick"
	MessageTypeModuleAction MessageType = "module_action"
	MessageTypeModuleSolved MessageType = "module_solved"
	MessageTypeStrike       MessageType = "strike"
	MessageTypeGameWon      MessageType = "game_won"
	MessageTypeGameLost     MessageType = "game_lost"
	MessageTypeGameState    MessageType = "game_state"
	MessageTypeMagnetState  MessageType = "magnet_state"

	// Device events
	MessageTypeDeviceUpdate MessageType = "device_update"
)

type Message struct {
	Type      MessageType `json:"type"`
	Data      any         `json:"data"`
	Timestamp time.Time   `json:"timestamp"`
}

type DeviceUpdateData struct {
	DeviceID    string    `json:"device_id"`
	IsOnline    bool      `json:"is_online"`
	LastSeen    time.Time `json:"last_seen"`
	IsTooBright bool      `json:"is_too_bright"`
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

func (h *Hub) BroadcastDeviceUpdate(deviceID string, isOnline bool, lastSeen time.Time, isTooBright bool) {
	h.Broadcast(Message{
		Type: MessageTypeDeviceUpdate,
		Data: DeviceUpdateData{
			DeviceID:    deviceID,
			IsOnline:    isOnline,
			LastSeen:    lastSeen,
			IsTooBright: isTooBright,
		},
	})
}

func (h *Hub) ClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}

// Game-related broadcast methods

// BroadcastGameEvent sends a game event to all connected clients
func (h *Hub) BroadcastGameEvent(eventType MessageType, data any) {
	h.Broadcast(Message{
		Type: eventType,
		Data: data,
	})
}

// GameStateData represents game state for WebSocket broadcast
type GameStateData struct {
	GameID     string `json:"game_id"`
	State      string `json:"state"`
	TimeLeft   int    `json:"time_left"`
	Strikes    int    `json:"strikes"`
	MaxStrikes int    `json:"max_strikes"`
}

// GameEventData represents a generic game event
type GameEventData struct {
	GameID   string `json:"game_id"`
	ModuleID string `json:"module_id,omitempty"`
	Data     any    `json:"data,omitempty"`
}

// BroadcastGameState sends current game state
func (h *Hub) BroadcastGameState(gameID, state string, timeLeft, strikes, maxStrikes int) {
	h.Broadcast(Message{
		Type: MessageTypeGameState,
		Data: GameStateData{
			GameID:     gameID,
			State:      state,
			TimeLeft:   timeLeft,
			Strikes:    strikes,
			MaxStrikes: maxStrikes,
		},
	})
}

// BroadcastTimerTick sends timer update
func (h *Hub) BroadcastTimerTick(gameID string, timeLeft int) {
	h.Broadcast(Message{
		Type: MessageTypeTimerTick,
		Data: map[string]any{
			"game_id":   gameID,
			"time_left": timeLeft,
		},
	})
}

// BroadcastStrike sends strike notification
func (h *Hub) BroadcastStrike(gameID, moduleID, reason string, strikes, maxStrikes int) {
	h.Broadcast(Message{
		Type: MessageTypeStrike,
		Data: map[string]any{
			"game_id":     gameID,
			"module_id":   moduleID,
			"reason":      reason,
			"strikes":     strikes,
			"max_strikes": maxStrikes,
		},
	})
}

// BroadcastModuleSolved sends module solved notification
func (h *Hub) BroadcastModuleSolved(gameID, moduleID, nextModuleID string, activeModuleIndex int) {
	h.Broadcast(Message{
		Type: MessageTypeModuleSolved,
		Data: map[string]any{
			"game_id":             gameID,
			"module_id":           moduleID,
			"next_module_id":      nextModuleID,
			"active_module_index": activeModuleIndex,
		},
	})
}

// BroadcastGameEnd sends game over notification
func (h *Hub) BroadcastGameEnd(gameID string, won bool, reason string, timeRemaining int) {
	msgType := MessageTypeGameLost
	if won {
		msgType = MessageTypeGameWon
	}
	h.Broadcast(Message{
		Type: msgType,
		Data: map[string]any{
			"game_id":        gameID,
			"won":            won,
			"reason":         reason,
			"time_remaining": timeRemaining,
		},
	})
}
