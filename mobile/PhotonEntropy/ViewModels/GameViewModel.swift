//
//  GameViewModel.swift
//  PhotonEntropy
//
//  ViewModel for the Expert's game view
//

import Foundation
import Combine

@MainActor
class GameViewModel: ObservableObject {
    @Published var gameId: String = ""
    @Published var game: Game?
    @Published var manual: GameManual?
    @Published var isLoading = false
    @Published var error: String?
    @Published var isConnected = false

    // Selected module for detailed view
    @Published var selectedModule: String?

    private let gameService = GameService.shared
    private var cancellables = Set<AnyCancellable>()

    init() {
        setupBindings()
    }

    private func setupBindings() {
        gameService.$currentGame
            .receive(on: DispatchQueue.main)
            .assign(to: &$game)

        gameService.$manual
            .receive(on: DispatchQueue.main)
            .assign(to: &$manual)

        gameService.$isConnected
            .receive(on: DispatchQueue.main)
            .assign(to: &$isConnected)

        gameService.$connectionError
            .receive(on: DispatchQueue.main)
            .sink { [weak self] error in
                if let error = error {
                    self?.error = error
                }
            }
            .store(in: &cancellables)
    }

    // MARK: - Actions

    func joinGame() async {
        guard !gameId.isEmpty else {
            error = "Please enter a game code"
            return
        }

        isLoading = true
        error = nil

        do {
            // Join as expert using the code
            let joinResponse = try await gameService.joinGame(code: gameId.uppercased(), role: .expert)

            // Get game state using the game_id from response
            _ = try await gameService.getGameState(gameId: joinResponse.gameId)

            // Get manual (instructions)
            _ = try await gameService.getManual(gameId: joinResponse.gameId)

            // Connect WebSocket for real-time updates
            gameService.connectWebSocket(gameId: joinResponse.gameId)

        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func leaveGame() {
        gameService.disconnectWebSocket()
        game = nil
        manual = nil
        gameId = ""
    }

    func refreshState() async {
        guard let id = game?.id else { return }

        do {
            _ = try await gameService.getGameState(gameId: id)
        } catch {
            self.error = error.localizedDescription
        }
    }

    // MARK: - Computed Properties

    var timeFormatted: String {
        guard let game = game else { return "--:--" }
        let minutes = game.timeRemaining / 60
        let seconds = game.timeRemaining % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }

    var strikesDisplay: String {
        guard let game = game else { return "" }
        let strikes = String(repeating: "X", count: game.strikes)
        let remaining = String(repeating: "O", count: game.maxStrikes - game.strikes)
        return strikes + remaining
    }

    var solvedModulesCount: Int {
        game?.modules.filter { $0.state == "solved" }.count ?? 0
    }

    var totalModulesCount: Int {
        game?.modules.count ?? 0
    }

    var isGameActive: Bool {
        game?.state == .playing
    }

    var isGameOver: Bool {
        game?.state == .won || game?.state == .lost
    }

    func isModuleSolved(_ type: String) -> Bool {
        game?.modules.first { $0.type == type }?.state == "solved"
    }
}
