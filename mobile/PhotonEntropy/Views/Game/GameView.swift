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
        Group {
            if viewModel.game != nil {
                ActiveGameView(viewModel: viewModel)
            } else {
                JoinGameView(viewModel: viewModel)
            }
        }
    }
}

// MARK: - Join Game View

struct JoinGameView: View {
    @ObservedObject var viewModel: GameViewModel
    @FocusState private var isCodeFieldFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            // Icon
            ZStack {
                Circle()
                    .fill(Color.theme.accent.opacity(0.1))
                    .frame(width: 120, height: 120)

                Image(systemName: "bolt.fill")
                    .font(.system(size: 44, weight: .medium))
                    .foregroundStyle(Color.theme.accent)
            }
            .padding(.bottom, 32)

            // Title
            Text("Expert Mode")
                .font(.theme.heroTitle)
                .foregroundStyle(.primary)

            // Subtitle
            Text("Enter the code from the bomb")
                .font(.theme.body)
                .foregroundStyle(.secondary)
                .padding(.top, 8)

            Spacer()

            // Code Input Section
            VStack(spacing: 24) {
                // Code Field
                TextField("", text: $viewModel.gameId, prompt: Text("ABC123").foregroundStyle(.tertiary))
                    .font(.theme.codeInput)
                    .multilineTextAlignment(.center)
                    .textInputAutocapitalization(.characters)
                    .autocorrectionDisabled()
                    .focused($isCodeFieldFocused)
                    .padding(.vertical, 16)
                    .background(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .fill(Color.theme.cardBackground)
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .strokeBorder(isCodeFieldFocused ? Color.theme.accent.opacity(0.5) : .clear, lineWidth: 2)
                    )

                // Error Message
                if let error = viewModel.error {
                    HStack(spacing: 6) {
                        Image(systemName: "exclamationmark.circle.fill")
                            .font(.system(size: 14))
                        Text(error)
                            .font(.theme.caption)
                    }
                    .foregroundStyle(Color.theme.accent)
                    .transition(.opacity.combined(with: .move(edge: .top)))
                }

                // Join Button
                Button {
                    Haptics.medium()
                    Task {
                        await viewModel.joinGame()
                    }
                } label: {
                    if viewModel.isLoading {
                        ProgressView()
                            .tint(.white)
                    } else {
                        Text("Join Game")
                    }
                }
                .buttonStyle(PrimaryButtonStyle())
                .disabled(viewModel.gameId.isEmpty || viewModel.isLoading)
                .opacity(viewModel.gameId.isEmpty ? 0.5 : 1.0)
            }
            .padding(.horizontal, 24)
            .animation(.easeInOut(duration: 0.2), value: viewModel.error)

            Spacer()
            Spacer()
        }
        .onAppear {
            isCodeFieldFocused = true
        }
    }
}

// MARK: - Active Game View

struct ActiveGameView: View {
    @ObservedObject var viewModel: GameViewModel
    @State private var showLeaveAlert = false

    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                Color(.systemBackground)
                    .ignoresSafeArea()

                if viewModel.isGameOver {
                    GameOverView(viewModel: viewModel)
                } else {
                    VStack(spacing: 0) {
                        GameStatusHeader(viewModel: viewModel)
                        ModuleListView(viewModel: viewModel)
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    ConnectionIndicator(isConnected: viewModel.isConnected)
                }

                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showLeaveAlert = true
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 24))
                            .symbolRenderingMode(.hierarchical)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .alert("Leave Game?", isPresented: $showLeaveAlert) {
                Button("Cancel", role: .cancel) { }
                Button("Leave", role: .destructive) {
                    viewModel.leaveGame()
                }
            } message: {
                Text("Are you sure you want to leave this game?")
            }
        }
    }
}

// MARK: - Connection Indicator

struct ConnectionIndicator: View {
    let isConnected: Bool

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(isConnected ? Color.theme.success : Color.theme.accent)
                .frame(width: 8, height: 8)

            Text(isConnected ? "Connected" : "Disconnected")
                .font(.theme.caption)
                .foregroundStyle(.secondary)
        }
    }
}

// MARK: - Game Status Header

struct GameStatusHeader: View {
    @ObservedObject var viewModel: GameViewModel

    var body: some View {
        VStack(spacing: 16) {
            // Timer
            Text(viewModel.timeFormatted)
                .font(.theme.timer)
                .foregroundStyle(timerColor)
                .monospacedDigit()
                .contentTransition(.numericText())
                .animation(.linear(duration: 0.1), value: viewModel.game?.timeRemaining)

            // Status Row
            HStack(spacing: 24) {
                // Strikes
                HStack(spacing: 8) {
                    ForEach(0..<(viewModel.game?.maxStrikes ?? 3), id: \.self) { i in
                        Circle()
                            .fill(i < (viewModel.game?.strikes ?? 0) ? Color.theme.accent : Color.theme.cardBackground)
                            .frame(width: 12, height: 12)
                            .overlay(
                                Circle()
                                    .strokeBorder(i < (viewModel.game?.strikes ?? 0) ? Color.theme.accent : Color(.systemGray4), lineWidth: 1.5)
                            )
                    }

                    Text("Strikes")
                        .font(.theme.caption)
                        .foregroundStyle(.secondary)
                }

                Divider()
                    .frame(height: 20)

                // Modules Progress
                HStack(spacing: 8) {
                    Text("\(viewModel.solvedModulesCount)")
                        .font(.system(size: 17, weight: .semibold, design: .rounded))
                        .foregroundStyle(Color.theme.success)
                    Text("/")
                        .foregroundStyle(.tertiary)
                    Text("\(viewModel.totalModulesCount)")
                        .font(.system(size: 17, weight: .semibold, design: .rounded))
                        .foregroundStyle(.primary)

                    Text("Modules")
                        .font(.theme.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
        .padding(.horizontal, 24)
        .background(
            Rectangle()
                .fill(.ultraThinMaterial)
                .ignoresSafeArea(edges: .top)
        )
    }

    private var timerColor: Color {
        guard let game = viewModel.game else { return .primary }
        if game.timeRemaining <= 30 {
            return Color.theme.timerCritical
        } else if game.timeRemaining <= 60 {
            return Color.theme.timerWarning
        }
        return Color.theme.timerNormal
    }
}

// MARK: - Game Over View

struct GameOverView: View {
    @ObservedObject var viewModel: GameViewModel
    @State private var animateIcon = false
    @State private var animateText = false
    @State private var animateButton = false

    private var isWin: Bool {
        viewModel.game?.state == .won
    }

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            // Result Icon
            ZStack {
                Circle()
                    .fill((isWin ? Color.theme.success : Color.theme.accent).opacity(0.1))
                    .frame(width: 160, height: 160)
                    .scaleEffect(animateIcon ? 1 : 0.5)

                Image(systemName: isWin ? "checkmark" : "xmark")
                    .font(.system(size: 64, weight: .medium))
                    .foregroundStyle(isWin ? Color.theme.success : Color.theme.accent)
                    .scaleEffect(animateIcon ? 1 : 0)
            }
            .padding(.bottom, 32)

            // Result Text
            VStack(spacing: 8) {
                Text(isWin ? "Defused" : "Exploded")
                    .font(.theme.heroTitle)
                    .foregroundStyle(.primary)

                if isWin {
                    Text("\(viewModel.timeFormatted) remaining")
                        .font(.theme.body)
                        .foregroundStyle(.secondary)
                } else {
                    Text(viewModel.game?.strikes == viewModel.game?.maxStrikes ? "Too many strikes" : "Time ran out")
                        .font(.theme.body)
                        .foregroundStyle(.secondary)
                }
            }
            .opacity(animateText ? 1 : 0)
            .offset(y: animateText ? 0 : 20)

            Spacer()
            Spacer()

            // Play Again Button
            Button {
                Haptics.medium()
                viewModel.leaveGame()
            } label: {
                Text("Play Again")
            }
            .buttonStyle(SecondaryButtonStyle())
            .padding(.horizontal, 24)
            .padding(.bottom, 32)
            .opacity(animateButton ? 1 : 0)
            .offset(y: animateButton ? 0 : 20)
        }
        .onAppear {
            if isWin {
                Haptics.success()
            } else {
                Haptics.error()
            }

            withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) {
                animateIcon = true
            }
            withAnimation(.easeOut(duration: 0.4).delay(0.2)) {
                animateText = true
            }
            withAnimation(.easeOut(duration: 0.4).delay(0.4)) {
                animateButton = true
            }
        }
    }
}

// MARK: - Preview

#Preview {
    GameView()
}
