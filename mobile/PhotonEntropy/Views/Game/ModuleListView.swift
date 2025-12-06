//
//  ModuleListView.swift
//  PhotonEntropy
//
//  List of game modules with instructions
//

import SwiftUI

struct ModuleListView: View {
    @ObservedObject var viewModel: GameViewModel

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                if let manual = viewModel.manual {
                    ModuleCard(
                        title: "Wires",
                        icon: "line.3.horizontal.decrease",
                        color: Color.theme.wires,
                        isSolved: viewModel.isModuleSolved("wires"),
                        isActive: viewModel.isModuleActive("wires"),
                        rules: manual.wires
                    )

                    ModuleCard(
                        title: "Simon Says",
                        icon: "circle.grid.3x3.fill",
                        color: Color.theme.simon,
                        isSolved: viewModel.isModuleSolved("simon"),
                        isActive: viewModel.isModuleActive("simon"),
                        rules: manual.simon
                    ) {
                        if viewModel.isModuleActive("simon") {
                            SimonColorButtons(viewModel: viewModel)
                        }
                    }

                    ModuleCard(
                        title: "Magnet",
                        icon: "wave.3.right",
                        color: Color.theme.magnet,
                        isSolved: viewModel.isModuleSolved("magnet"),
                        isActive: viewModel.isModuleActive("magnet"),
                        rules: manual.magnet
                    )
                } else {
                    LoadingCard()
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
        .background(Color(.systemGroupedBackground))
    }
}

// MARK: - Loading Card

struct LoadingCard: View {
    var body: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.2)

            Text("Loading instructions...")
                .font(.theme.body)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .frame(height: 120)
        .background(Color.theme.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}

// MARK: - Module Card

struct ModuleCard<ExtraContent: View>: View {
    let title: String
    let icon: String
    let color: Color
    let isSolved: Bool
    let isActive: Bool
    let rules: [String]
    @ViewBuilder var extraContent: () -> ExtraContent

    @State private var isExpanded: Bool = false

    init(
        title: String,
        icon: String,
        color: Color,
        isSolved: Bool,
        isActive: Bool,
        rules: [String],
        @ViewBuilder extraContent: @escaping () -> ExtraContent = { EmptyView() }
    ) {
        self.title = title
        self.icon = icon
        self.color = color
        self.isSolved = isSolved
        self.isActive = isActive
        self.rules = rules
        self.extraContent = extraContent
        self._isExpanded = State(initialValue: isActive)
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            Button {
                Haptics.light()
                withAnimation(.spring(response: 0.35, dampingFraction: 0.8)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack(spacing: 14) {
                    // Icon Container
                    ZStack {
                        RoundedRectangle(cornerRadius: 10, style: .continuous)
                            .fill(color.opacity(0.15))
                            .frame(width: 40, height: 40)

                        Image(systemName: icon)
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundStyle(color)
                    }

                    // Title
                    Text(title)
                        .font(.theme.moduleTitle)
                        .foregroundStyle(.primary)

                    Spacer()

                    // Status Badge
                    StatusBadge(isSolved: isSolved, isActive: isActive)

                    // Chevron
                    Image(systemName: "chevron.right")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(.tertiary)
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                }
                .padding(16)
            }
            .buttonStyle(.plain)

            // Expanded Content
            if isExpanded {
                VStack(alignment: .leading, spacing: 0) {
                    Divider()
                        .padding(.horizontal, 16)

                    VStack(alignment: .leading, spacing: 16) {
                        // Rules
                        VStack(alignment: .leading, spacing: 10) {
                            ForEach(Array(rules.enumerated()), id: \.offset) { index, rule in
                                RuleRow(number: index + 1, text: rule)
                            }
                        }

                        // Extra Content (e.g., Simon buttons)
                        extraContent()
                    }
                    .padding(16)
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .cardStyle(isActive: isActive, isSolved: isSolved)
        .onChange(of: isActive) { _, newValue in
            if newValue && !isExpanded {
                withAnimation(.spring(response: 0.35, dampingFraction: 0.8)) {
                    isExpanded = true
                }
            }
        }
    }
}

// MARK: - Status Badge

struct StatusBadge: View {
    let isSolved: Bool
    let isActive: Bool

    var body: some View {
        HStack(spacing: 4) {
            if isSolved {
                Image(systemName: "checkmark")
                    .font(.system(size: 10, weight: .bold))
                Text("Done")
            } else if isActive {
                Circle()
                    .fill(Color.theme.warning)
                    .frame(width: 6, height: 6)
                Text("Active")
            } else {
                Image(systemName: "lock.fill")
                    .font(.system(size: 9, weight: .medium))
                Text("Locked")
            }
        }
        .font(.system(size: 12, weight: .medium))
        .foregroundStyle(badgeColor)
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(
            Capsule()
                .fill(badgeColor.opacity(0.12))
        )
    }

    private var badgeColor: Color {
        if isSolved {
            return Color.theme.success
        } else if isActive {
            return Color.theme.warning
        } else {
            return .secondary
        }
    }
}

// MARK: - Rule Row

struct RuleRow: View {
    let number: Int
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Text("\(number)")
                .font(.system(size: 13, weight: .semibold, design: .rounded))
                .foregroundStyle(.secondary)
                .frame(width: 20, alignment: .trailing)

            Text(text)
                .font(.theme.body)
                .foregroundStyle(.primary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

// MARK: - Simon Color Buttons

struct SimonColorButtons: View {
    @ObservedObject var viewModel: GameViewModel
    @State private var lastResult: ActionFeedback?

    enum ActionFeedback {
        case success(String)
        case error(String)
    }

    var body: some View {
        VStack(spacing: 16) {
            // Instruction
            Text("Tap the colors in sequence")
                .font(.theme.caption)
                .foregroundStyle(.secondary)

            // Color Buttons
            HStack(spacing: 16) {
                SimonButton(color: .red, label: "R") {
                    tapColor("red")
                }

                SimonButton(color: .green, label: "G") {
                    tapColor("green")
                }

                SimonButton(color: .blue, label: "B") {
                    tapColor("blue")
                }
            }

            // Feedback
            if let feedback = lastResult {
                feedbackView(for: feedback)
                    .transition(.scale.combined(with: .opacity))
            }
        }
        .padding(.top, 8)
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: lastResult != nil)
    }

    @ViewBuilder
    private func feedbackView(for feedback: ActionFeedback) -> some View {
        switch feedback {
        case .success(let message):
            HStack(spacing: 6) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 14))
                Text(message)
                    .font(.theme.caption)
            }
            .foregroundStyle(Color.theme.success)

        case .error(let message):
            HStack(spacing: 6) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 14))
                Text(message)
                    .font(.theme.caption)
            }
            .foregroundStyle(Color.theme.accent)
        }
    }

    private func tapColor(_ color: String) {
        Haptics.light()
        Task {
            do {
                let response = try await viewModel.sendSimonColor(color)
                withAnimation {
                    if response.result.strike {
                        Haptics.error()
                        lastResult = .error("Wrong! Start over")
                    } else if response.result.solved {
                        Haptics.success()
                        lastResult = .success("Solved!")
                    } else {
                        lastResult = .success(response.result.message ?? "Correct!")
                    }
                }

                // Clear feedback after delay
                try? await Task.sleep(nanoseconds: 2_000_000_000)
                withAnimation {
                    lastResult = nil
                }
            } catch {
                Haptics.error()
                lastResult = .error("Connection error")
            }
        }
    }
}

// MARK: - Simon Button

struct SimonButton: View {
    let color: Color
    let label: String
    let action: () -> Void

    @State private var isPressed = false

    var body: some View {
        Button {
            action()
        } label: {
            ZStack {
                Circle()
                    .fill(color.gradient)
                    .frame(width: 64, height: 64)
                    .shadow(color: color.opacity(0.4), radius: isPressed ? 2 : 8, y: isPressed ? 1 : 4)

                Text(label)
                    .font(.system(size: 16, weight: .bold, design: .rounded))
                    .foregroundStyle(.white)
            }
            .scaleEffect(isPressed ? 0.92 : 1.0)
        }
        .buttonStyle(.plain)
        .pressEvents {
            withAnimation(.easeInOut(duration: 0.1)) {
                isPressed = true
            }
        } onRelease: {
            withAnimation(.easeInOut(duration: 0.15)) {
                isPressed = false
            }
        }
    }
}

// MARK: - Press Events Modifier

struct PressEventsModifier: ViewModifier {
    var onPress: () -> Void
    var onRelease: () -> Void

    func body(content: Content) -> some View {
        content
            .simultaneousGesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { _ in onPress() }
                    .onEnded { _ in onRelease() }
            )
    }
}

extension View {
    func pressEvents(onPress: @escaping () -> Void, onRelease: @escaping () -> Void) -> some View {
        modifier(PressEventsModifier(onPress: onPress, onRelease: onRelease))
    }
}

#Preview {
    ModuleListView(viewModel: GameViewModel())
}
