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
                        isSolved: viewModel.isModuleSolved("wires")
                    ) {
                        RulesListView(rules: manual.wires)
                    }

                    ModuleCard(
                        title: "Keypad",
                        icon: "number.circle",
                        color: .blue,
                        isSolved: viewModel.isModuleSolved("keypad")
                    ) {
                        RulesListView(rules: manual.keypad)
                    }

                    ModuleCard(
                        title: "Simon Says",
                        icon: "circle.hexagongrid.fill",
                        color: .purple,
                        isSolved: viewModel.isModuleSolved("simon")
                    ) {
                        RulesListView(rules: manual.simon)
                    }

                    ModuleCard(
                        title: "Magnet",
                        icon: "magnet",
                        color: .orange,
                        isSolved: viewModel.isModuleSolved("magnet")
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

// MARK: - Module Card

struct ModuleCard<Content: View>: View {
    let title: String
    let icon: String
    let color: Color
    let isSolved: Bool
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
                    }

                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                }
                .padding()
                .background(isSolved ? Color.green.opacity(0.1) : Color(.systemGray6))
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
