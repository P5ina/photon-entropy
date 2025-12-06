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
    case won = "win"
    case lost = "lose"
}

enum PlayerRole: String, Codable {
    case defuser
    case expert
}

struct Game: Codable, Identifiable {
    let id: String
    let code: String
    let state: GameState
    let timeLimit: Int
    let timeRemaining: Int
    let maxStrikes: Int
    let strikes: Int
    let modules: [Module]
    let activeModuleIndex: Int
    let bombConnected: Bool
    let expertConnected: Bool

    enum CodingKeys: String, CodingKey {
        case id = "game_id"
        case code, state
        case timeLimit = "time_limit"
        case timeRemaining = "time_left"
        case maxStrikes = "max_strikes"
        case strikes, modules
        case activeModuleIndex = "active_module_index"
        case bombConnected = "bomb_connected"
        case expertConnected = "expert_connected"
    }
}

struct Module: Codable, Identifiable {
    let id: String
    let type: String
    let state: String
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

// MARK: - Manual (Instructions for Expert)

struct ManualResponse: Codable {
    let gameId: String
    let seed: Int64
    let activeModules: [String]
    let manual: GameManual

    enum CodingKeys: String, CodingKey {
        case gameId = "game_id"
        case seed
        case activeModules = "active_modules"
        case manual
    }
}

struct GameManual: Codable {
    let wires: [String]
    let keypad: [String]
    let simon: [String]
    let magnet: [String]
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
    let gameId: String
    let code: String
    let state: GameState
    let timeLimit: Int
    let modulesCount: Int
    let bombConnected: Bool
    let expertConnected: Bool

    enum CodingKeys: String, CodingKey {
        case gameId = "game_id"
        case code, state
        case timeLimit = "time_limit"
        case modulesCount = "modules_count"
        case bombConnected = "bomb_connected"
        case expertConnected = "expert_connected"
    }
}

struct ActionResponse: Codable {
    let result: ActionResult
    let gameState: String
    let strikes: Int
    let modules: [Module]

    enum CodingKeys: String, CodingKey {
        case result
        case gameState = "game_state"
        case strikes, modules
    }
}

struct ActionResult: Codable {
    let success: Bool
    let strike: Bool
    let solved: Bool
    let message: String
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
