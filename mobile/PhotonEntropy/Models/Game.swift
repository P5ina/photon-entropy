//
//  Game.swift
//  PhotonEntropy
//
//  Game models for Bomb Defusal
//

import Foundation

// MARK: - Game State

enum GameState: String, Codable {
    case lobby
    case playing
    case won
    case lost
}

enum PlayerRole: String, Codable {
    case defuser
    case expert
}

struct Game: Codable, Identifiable {
    let id: String
    let seed: Int
    let state: GameState
    let timeLimit: Int
    let timeRemaining: Int
    let maxStrikes: Int
    let strikes: Int
    let modules: [String: ModuleState]
    let players: [Player]
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, seed, state
        case timeLimit = "time_limit"
        case timeRemaining = "time_remaining"
        case maxStrikes = "max_strikes"
        case strikes, modules, players
        case createdAt = "created_at"
    }
}

struct Player: Codable, Identifiable {
    let id: String
    let role: PlayerRole
    let joinedAt: Date

    enum CodingKeys: String, CodingKey {
        case id, role
        case joinedAt = "joined_at"
    }
}

struct ModuleState: Codable {
    let solved: Bool
    let config: [String: AnyCodableValue]?
}

// MARK: - Module Configs

struct WiresConfig: Codable {
    let wireOrder: [Int]

    enum CodingKeys: String, CodingKey {
        case wireOrder = "wire_order"
    }
}

struct KeypadConfig: Codable {
    let code: [Int]
}

struct SimonConfig: Codable {
    let sequence: [String]
    let rounds: Int
}

struct MagnetConfig: Codable {
    let safeZones: [[Int]]
    let required: Int

    enum CodingKeys: String, CodingKey {
        case safeZones = "safe_zones"
        case required
    }
}

struct StabilityConfig: Codable {
    let maxTilts: Int
    let stableDuration: Int

    enum CodingKeys: String, CodingKey {
        case maxTilts = "max_tilts"
        case stableDuration = "stable_duration"
    }
}

// MARK: - Manual (Instructions for Expert)

struct GameManual: Codable {
    let wires: WiresManual
    let keypad: KeypadManual
    let simon: SimonManual
    let magnet: MagnetManual
    let stability: StabilityManual
}

struct WiresManual: Codable {
    let colors: [String]
    let cutOrder: [Int]
    let rules: [String]

    enum CodingKeys: String, CodingKey {
        case colors
        case cutOrder = "cut_order"
        case rules
    }
}

struct KeypadManual: Codable {
    let codeLength: Int
    let hints: [String]

    enum CodingKeys: String, CodingKey {
        case codeLength = "code_length"
        case hints
    }
}

struct SimonManual: Codable {
    let rounds: Int
    let colorMapping: [String: String]
    let rules: [String]

    enum CodingKeys: String, CodingKey {
        case rounds
        case colorMapping = "color_mapping"
        case rules
    }
}

struct MagnetManual: Codable {
    let safeZones: [[Int]]
    let required: Int
    let hints: [String]

    enum CodingKeys: String, CodingKey {
        case safeZones = "safe_zones"
        case required, hints
    }
}

struct StabilityManual: Codable {
    let maxTilts: Int
    let duration: Int
    let tips: [String]

    enum CodingKeys: String, CodingKey {
        case maxTilts = "max_tilts"
        case duration, tips
    }
}

// MARK: - API Responses

struct CreateGameResponse: Codable {
    let gameId: String
    let seed: Int

    enum CodingKeys: String, CodingKey {
        case gameId = "game_id"
        case seed
    }
}

struct JoinGameResponse: Codable {
    let success: Bool
    let role: PlayerRole
}

// MARK: - Helper for dynamic JSON

enum AnyCodableValue: Codable {
    case string(String)
    case int(Int)
    case double(Double)
    case bool(Bool)
    case array([AnyCodableValue])
    case dictionary([String: AnyCodableValue])
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode(Int.self) {
            self = .int(value)
        } else if let value = try? container.decode(Double.self) {
            self = .double(value)
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else if let value = try? container.decode([AnyCodableValue].self) {
            self = .array(value)
        } else if let value = try? container.decode([String: AnyCodableValue].self) {
            self = .dictionary(value)
        } else {
            self = .null
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value): try container.encode(value)
        case .int(let value): try container.encode(value)
        case .double(let value): try container.encode(value)
        case .bool(let value): try container.encode(value)
        case .array(let value): try container.encode(value)
        case .dictionary(let value): try container.encode(value)
        case .null: try container.encodeNil()
        }
    }
}
