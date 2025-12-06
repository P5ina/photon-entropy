//
//  GameService.swift
//  PhotonEntropy
//
//  Game API service for Bomb Defusal
//

import Foundation
import Combine

@MainActor
class GameService: ObservableObject {
    static let shared = GameService()

    @Published var currentGame: Game?
    @Published var manual: GameManual?
    @Published var isConnected = false
    @Published var connectionError: String?

    private var webSocketTask: URLSessionWebSocketTask?
    private var pingTask: Task<Void, Never>?
    private var cancellables = Set<AnyCancellable>()

    private lazy var session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        return URLSession(configuration: config)
    }()

    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    private init() {}

    var baseURL: String {
        APIService.shared.baseURL
    }

    // MARK: - Game API

    func createGame(timeLimit: Int = 300, maxStrikes: Int = 3) async throws -> CreateGameResponse {
        guard let url = URL(string: "\(baseURL)/api/v1/game/create") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["time_limit": timeLimit, "max_strikes": maxStrikes]
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError((response as? HTTPURLResponse)?.statusCode ?? 500)
        }

        return try decoder.decode(CreateGameResponse.self, from: data)
    }

    func joinGame(code: String, role: PlayerRole) async throws -> JoinGameResponse {
        guard let url = URL(string: "\(baseURL)/api/v1/game/join") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["code": code, "role": role.rawValue]
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            if let errorJson = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let errorMessage = errorJson["error"] as? String {
                throw APIError.message("Join failed: \(errorMessage)")
            }
            throw APIError.serverError((response as? HTTPURLResponse)?.statusCode ?? 500)
        }

        return try decoder.decode(JoinGameResponse.self, from: data)
    }

    func getGameState(gameId: String) async throws -> Game {
        guard let url = URL(string: "\(baseURL)/api/v1/game/state?game_id=\(gameId)") else {
            throw APIError.invalidURL
        }

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError((response as? HTTPURLResponse)?.statusCode ?? 500)
        }

        let game = try decoder.decode(Game.self, from: data)
        self.currentGame = game
        return game
    }

    func getManual(gameId: String) async throws -> GameManual {
        guard let url = URL(string: "\(baseURL)/api/v1/game/manual?game_id=\(gameId)") else {
            throw APIError.invalidURL
        }

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            if let errorJson = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let errorMessage = errorJson["error"] as? String {
                throw APIError.message("Manual failed: \(errorMessage)")
            }
            throw APIError.serverError((response as? HTTPURLResponse)?.statusCode ?? 500)
        }

        let manualResponse = try decoder.decode(ManualResponse.self, from: data)
        self.manual = manualResponse.manual
        return manualResponse.manual
    }

    func startGame(gameId: String) async throws {
        guard let url = URL(string: "\(baseURL)/api/v1/game/start?game_id=\(gameId)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            // Try to get error message from response
            if let errorJson = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let errorMessage = errorJson["error"] as? String {
                throw APIError.message(errorMessage)
            }
            throw APIError.serverError((response as? HTTPURLResponse)?.statusCode ?? 500)
        }
    }

    // MARK: - WebSocket

    func connectWebSocket(gameId: String) {
        let wsURL = baseURL
            .replacingOccurrences(of: "https://", with: "wss://")
            .replacingOccurrences(of: "http://", with: "ws://")

        guard let url = URL(string: "\(wsURL)/ws?game_id=\(gameId)") else {
            connectionError = "Invalid WebSocket URL"
            return
        }

        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        isConnected = true
        connectionError = nil

        receiveMessage()
        startPing()
    }

    func disconnectWebSocket() {
        pingTask?.cancel()
        pingTask = nil
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isConnected = false
    }

    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            Task { @MainActor in
                switch result {
                case .success(let message):
                    self?.handleMessage(message)
                    self?.receiveMessage()
                case .failure(let error):
                    print("[GameWS] Error: \(error)")
                    self?.isConnected = false
                    self?.connectionError = error.localizedDescription
                }
            }
        }
    }

    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        guard case .string(let text) = message,
              let data = text.data(using: .utf8) else { return }

        do {
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let type = json["type"] as? String {
                handleGameEvent(type: type, data: json["data"] as? [String: Any] ?? [:])
            }
        } catch {
            print("[GameWS] Decode error: \(error)")
        }
    }

    private func handleGameEvent(type: String, data: [String: Any]) {
        switch type {
        case "timer_tick":
            if let remaining = data["remaining"] as? Int {
                currentGame = currentGame.map { game in
                    Game(
                        id: game.id,
                        code: game.code,
                        state: game.state,
                        timeLimit: game.timeLimit,
                        timeRemaining: remaining,
                        maxStrikes: game.maxStrikes,
                        strikes: game.strikes,
                        modules: game.modules,
                        bombConnected: game.bombConnected,
                        expertConnected: game.expertConnected
                    )
                }
            }

        case "strike":
            if let strikes = data["strikes"] as? Int {
                currentGame = currentGame.map { game in
                    Game(
                        id: game.id,
                        code: game.code,
                        state: game.state,
                        timeLimit: game.timeLimit,
                        timeRemaining: game.timeRemaining,
                        maxStrikes: game.maxStrikes,
                        strikes: strikes,
                        modules: game.modules,
                        bombConnected: game.bombConnected,
                        expertConnected: game.expertConnected
                    )
                }
            }

        case "module_solved":
            // Refresh game state
            if let gameId = currentGame?.id {
                Task {
                    _ = try? await getGameState(gameId: gameId)
                }
            }

        case "game_won":
            currentGame = currentGame.map { game in
                Game(
                    id: game.id,
                    code: game.code,
                    state: .won,
                    timeLimit: game.timeLimit,
                    timeRemaining: game.timeRemaining,
                    maxStrikes: game.maxStrikes,
                    strikes: game.strikes,
                    modules: game.modules,
                    bombConnected: game.bombConnected,
                    expertConnected: game.expertConnected
                )
            }

        case "game_lost":
            currentGame = currentGame.map { game in
                Game(
                    id: game.id,
                    code: game.code,
                    state: .lost,
                    timeLimit: game.timeLimit,
                    timeRemaining: game.timeRemaining,
                    maxStrikes: game.maxStrikes,
                    strikes: game.strikes,
                    modules: game.modules,
                    bombConnected: game.bombConnected,
                    expertConnected: game.expertConnected
                )
            }

        default:
            print("[GameWS] Unknown event: \(type)")
        }
    }

    private func startPing() {
        pingTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 30_000_000_000)
                webSocketTask?.sendPing { _ in }
            }
        }
    }
}
