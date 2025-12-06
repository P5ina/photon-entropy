//
//  GameView.swift
//  PhotonEntropy
//
//  Main game view for the Expert role
//

import SwiftUI

struct GameView: View {
    @StateObject private var viewModel = GameViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.game != nil {
                    ActiveGameView(viewModel: viewModel)
                } else {
                    JoinGameView(viewModel: viewModel)
                }
            }
            .navigationTitle("Bomb Defusal")
        }
    }
}

// MARK: - Join Game View

struct JoinGameView: View {
    @ObservedObject var viewModel: GameViewModel

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            Image(systemName: "bolt.trianglebadge.exclamationmark.fill")
                .font(.system(size: 80))
                .foregroundStyle(.red)

            Text("Expert Mode")
                .font(.largeTitle.bold())

            Text("Enter the game code shown on the bomb controller")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            TextField("Game Code", text: $viewModel.gameId)
                .textFieldStyle(.roundedBorder)
                .font(.title2.monospaced())
                .multilineTextAlignment(.center)
                .textInputAutocapitalization(.characters)
                .padding(.horizontal, 40)

            if let error = viewModel.error {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
            }

            Button {
                Task {
                    await viewModel.joinGame()
                }
            } label: {
                if viewModel.isLoading {
                    ProgressView()
                        .tint(.white)
                } else {
                    Text("Join Game")
                        .font(.headline)
                }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(viewModel.gameId.isEmpty || viewModel.isLoading)

            Spacer()
            Spacer()
        }
        .padding()
    }
}

// MARK: - Active Game View

struct ActiveGameView: View {
    @ObservedObject var viewModel: GameViewModel

    var body: some View {
        VStack(spacing: 0) {
            // Status Header
            GameStatusHeader(viewModel: viewModel)

            // Game Over Overlay or Module List
            if viewModel.isGameOver {
                GameOverView(viewModel: viewModel)
            } else {
                ModuleListView(viewModel: viewModel)
            }
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Leave") {
                    viewModel.leaveGame()
                }
                .foregroundStyle(.red)
            }
        }
    }
}

// MARK: - Game Status Header

struct GameStatusHeader: View {
    @ObservedObject var viewModel: GameViewModel

    var body: some View {
        VStack(spacing: 12) {
            // Timer
            HStack {
                Image(systemName: "timer")
                    .foregroundStyle(timerColor)
                Text(viewModel.timeFormatted)
                    .font(.system(size: 48, weight: .bold, design: .monospaced))
                    .foregroundStyle(timerColor)
            }

            // Strikes
            HStack(spacing: 4) {
                Text("STRIKES:")
                    .font(.caption.bold())
                    .foregroundStyle(.secondary)

                ForEach(0..<(viewModel.game?.maxStrikes ?? 3), id: \.self) { i in
                    Image(systemName: i < (viewModel.game?.strikes ?? 0) ? "xmark.circle.fill" : "circle")
                        .foregroundStyle(i < (viewModel.game?.strikes ?? 0) ? .red : .secondary)
                }
            }

            // Modules progress
            HStack {
                Text("Modules: \(viewModel.solvedModulesCount)/\(viewModel.totalModulesCount)")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                if viewModel.isConnected {
                    Image(systemName: "wifi")
                        .foregroundStyle(.green)
                } else {
                    Image(systemName: "wifi.slash")
                        .foregroundStyle(.red)
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial)
    }

    var timerColor: Color {
        guard let game = viewModel.game else { return .primary }
        if game.timeRemaining <= 30 {
            return .red
        } else if game.timeRemaining <= 60 {
            return .orange
        }
        return .primary
    }
}

// MARK: - Game Over View

struct GameOverView: View {
    @ObservedObject var viewModel: GameViewModel

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            if viewModel.game?.state == .won {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 100))
                    .foregroundStyle(.green)

                Text("DEFUSED!")
                    .font(.largeTitle.bold())
                    .foregroundStyle(.green)

                Text("Time remaining: \(viewModel.timeFormatted)")
                    .font(.title2)
            } else {
                Image(systemName: "flame.fill")
                    .font(.system(size: 100))
                    .foregroundStyle(.red)

                Text("BOOM!")
                    .font(.largeTitle.bold())
                    .foregroundStyle(.red)

                Text("The bomb exploded")
                    .font(.title2)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button("Play Again") {
                viewModel.leaveGame()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

            Spacer()
        }
        .padding()
    }
}

// MARK: - Preview

#Preview {
    GameView()
}
