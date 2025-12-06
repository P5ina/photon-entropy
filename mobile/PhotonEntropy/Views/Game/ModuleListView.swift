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
            LazyVStack(spacing: 16) {
                if let manual = viewModel.manual {
                    ModuleCard(
                        title: "Wires",
                        icon: "line.3.horizontal",
                        color: .red,
                        isSolved: viewModel.isModuleSolved("wires"),
                        isActive: viewModel.isModuleActive("wires")
                    ) {
                        RulesListView(rules: manual.wires)
                    }

                    ModuleCard(
                        title: "Keypad",
                        icon: "number.circle",
                        color: .blue,
                        isSolved: viewModel.isModuleSolved("keypad"),
                        isActive: viewModel.isModuleActive("keypad")
                    ) {
                        RulesListView(rules: manual.keypad)
                    }

                    ModuleCard(
                        title: "Simon Says",
                        icon: "circle.hexagongrid.fill",
                        color: .purple,
                        isSolved: viewModel.isModuleSolved("simon"),
                        isActive: viewModel.isModuleActive("simon")
                    ) {
                        VStack(alignment: .leading, spacing: 12) {
                            RulesListView(rules: manual.simon)

                            // Color buttons for Simon module
                            if viewModel.isModuleActive("simon") {
                                SimonColorButtons(viewModel: viewModel)
                            }
                        }
                    }

                    ModuleCard(
                        title: "Magnet",
                        icon: "sensor.tag.radiowaves.forward",
                        color: .orange,
                        isSolved: viewModel.isModuleSolved("magnet"),
                        isActive: viewModel.isModuleActive("magnet")
                    ) {
                        RulesListView(rules: manual.magnet)
                    }
                } else {
                    ProgressView("Loading instructions...")
                        .padding()
                }
            }
            .padding()
        }
    }
}

// MARK: - Simon Color Buttons

struct SimonColorButtons: View {
    @ObservedObject var viewModel: GameViewModel
    @State private var lastResult: String?

    var body: some View {
        VStack(spacing: 12) {
            Divider()

            Text("Tap the colors in order:")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            HStack(spacing: 16) {
                ColorButton(color: .red, label: "RED") {
                    tapColor("red")
                }

                ColorButton(color: .green, label: "GREEN") {
                    tapColor("green")
                }

                ColorButton(color: .blue, label: "BLUE") {
                    tapColor("blue")
                }
            }

            if let result = lastResult {
                Text(result)
                    .font(.caption)
                    .foregroundStyle(result.contains("wrong") ? .red : .green)
                    .transition(.opacity)
            }
        }
        .padding(.top, 8)
    }

    private func tapColor(_ color: String) {
        Task {
            do {
                let response = try await viewModel.sendSimonColor(color)
                withAnimation {
                    if response.result.strike {
                        lastResult = "Wrong! Start over."
                    } else if response.result.solved {
                        lastResult = "Solved!"
                    } else {
                        lastResult = response.result.message
                    }
                }
            } catch {
                lastResult = "Error: \(error.localizedDescription)"
            }
        }
    }
}

struct ColorButton: View {
    let color: Color
    let label: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Circle()
                .fill(color)
                .frame(width: 60, height: 60)
                .overlay(
                    Text(label)
                        .font(.caption2.bold())
                        .foregroundStyle(.white)
                )
                .shadow(color: color.opacity(0.5), radius: 4)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Module Card

struct ModuleCard<Content: View>: View {
    let title: String
    let icon: String
    let color: Color
    let isSolved: Bool
    let isActive: Bool
    @ViewBuilder let content: () -> Content

    @State private var isExpanded = false

    var body: some View {
        VStack(spacing: 0) {
            // Header
            Button {
                withAnimation(.spring(response: 0.3)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack {
                    Image(systemName: icon)
                        .font(.title2)
                        .foregroundStyle(color)
                        .frame(width: 40)

                    Text(title)
                        .font(.headline)
                        .foregroundStyle(.primary)

                    Spacer()

                    if isSolved {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                    } else if isActive {
                        Image(systemName: "play.circle.fill")
                            .foregroundStyle(.orange)
                    } else {
                        Image(systemName: "lock.circle")
                            .foregroundStyle(.gray)
                    }

                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                }
                .padding()
                .background(
                    isSolved ? Color.green.opacity(0.1) :
                    isActive ? Color.orange.opacity(0.1) :
                    Color(.systemGray6)
                )
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .buttonStyle(.plain)

            // Expanded Content
            if isExpanded {
                content()
                    .padding()
                    .background(Color(.systemGray6).opacity(0.5))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .padding(.top, 4)
            }
        }
    }
}

// MARK: - Rules List View

struct RulesListView: View {
    let rules: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            ForEach(rules, id: \.self) { rule in
                HStack(alignment: .top, spacing: 8) {
                    Text("•")
                        .foregroundStyle(.secondary)
                    Text(rule)
                        .font(.subheadline)
                }
            }
        }
    }
}

#Preview {
    ModuleListView(viewModel: GameViewModel())
}
