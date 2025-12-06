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
                        isSolved: viewModel.game?.modules["wires"]?.solved ?? false
                    ) {
                        WiresInstructionsView(manual: manual.wires)
                    }

                    ModuleCard(
                        title: "Keypad",
                        icon: "number.circle",
                        color: .blue,
                        isSolved: viewModel.game?.modules["keypad"]?.solved ?? false
                    ) {
                        KeypadInstructionsView(manual: manual.keypad)
                    }

                    ModuleCard(
                        title: "Simon Says",
                        icon: "circle.hexagongrid.fill",
                        color: .purple,
                        isSolved: viewModel.game?.modules["simon"]?.solved ?? false
                    ) {
                        SimonInstructionsView(manual: manual.simon)
                    }

                    ModuleCard(
                        title: "Magnet",
                        icon: "magnet",
                        color: .orange,
                        isSolved: viewModel.game?.modules["magnet"]?.solved ?? false
                    ) {
                        MagnetInstructionsView(manual: manual.magnet)
                    }

                    ModuleCard(
                        title: "Stability",
                        icon: "level",
                        color: .green,
                        isSolved: viewModel.game?.modules["stability"]?.solved ?? false
                    ) {
                        StabilityInstructionsView(manual: manual.stability)
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

// MARK: - Wires Instructions

struct WiresInstructionsView: View {
    let manual: WiresManual

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("WIRE COLORS:")
                .font(.caption.bold())
                .foregroundStyle(.secondary)

            HStack(spacing: 8) {
                ForEach(manual.colors, id: \.self) { color in
                    WireColorBadge(color: color)
                }
            }

            Divider()

            Text("CUT ORDER:")
                .font(.caption.bold())
                .foregroundStyle(.secondary)

            HStack(spacing: 4) {
                ForEach(Array(manual.cutOrder.enumerated()), id: \.offset) { index, wireIndex in
                    HStack(spacing: 2) {
                        Text("\(index + 1).")
                            .font(.caption)
                        WireColorBadge(color: manual.colors[wireIndex])
                    }
                }
            }

            if !manual.rules.isEmpty {
                Divider()

                Text("RULES:")
                    .font(.caption.bold())
                    .foregroundStyle(.secondary)

                ForEach(manual.rules, id: \.self) { rule in
                    HStack(alignment: .top) {
                        Text("•")
                        Text(rule)
                            .font(.subheadline)
                    }
                }
            }
        }
    }
}

struct WireColorBadge: View {
    let color: String

    var swiftUIColor: Color {
        switch color.lowercased() {
        case "red": return .red
        case "blue": return .blue
        case "white": return .white
        case "orange": return .orange
        case "yellow": return .yellow
        case "green": return .green
        default: return .gray
        }
    }

    var body: some View {
        Text(color.uppercased())
            .font(.caption2.bold())
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(swiftUIColor.opacity(0.3))
            .foregroundStyle(color.lowercased() == "white" ? .primary : swiftUIColor)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(swiftUIColor, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: 6))
    }
}

// MARK: - Keypad Instructions

struct KeypadInstructionsView: View {
    let manual: KeypadManual

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("CODE LENGTH: \(manual.codeLength) digits")
                .font(.subheadline.bold())

            if !manual.hints.isEmpty {
                Divider()

                Text("HINTS:")
                    .font(.caption.bold())
                    .foregroundStyle(.secondary)

                ForEach(manual.hints, id: \.self) { hint in
                    HStack(alignment: .top) {
                        Text("•")
                        Text(hint)
                            .font(.subheadline)
                    }
                }
            }

            Divider()

            Text("Use the rotary encoder to select each digit (0-9), then press to confirm.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

// MARK: - Simon Instructions

struct SimonInstructionsView: View {
    let manual: SimonManual

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("ROUNDS: \(manual.rounds)")
                .font(.subheadline.bold())

            Divider()

            Text("COLOR MAPPING:")
                .font(.caption.bold())
                .foregroundStyle(.secondary)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                ForEach(Array(manual.colorMapping.keys.sorted()), id: \.self) { key in
                    if let value = manual.colorMapping[key] {
                        HStack {
                            WireColorBadge(color: key)
                            Image(systemName: "arrow.right")
                                .font(.caption)
                            WireColorBadge(color: value)
                        }
                    }
                }
            }

            if !manual.rules.isEmpty {
                Divider()

                Text("RULES:")
                    .font(.caption.bold())
                    .foregroundStyle(.secondary)

                ForEach(manual.rules, id: \.self) { rule in
                    HStack(alignment: .top) {
                        Text("•")
                        Text(rule)
                            .font(.subheadline)
                    }
                }
            }
        }
    }
}

// MARK: - Magnet Instructions

struct MagnetInstructionsView: View {
    let manual: MagnetManual

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("REQUIRED APPLICATIONS: \(manual.required)")
                .font(.subheadline.bold())

            Divider()

            Text("SAFE ZONES (seconds):")
                .font(.caption.bold())
                .foregroundStyle(.secondary)

            ForEach(Array(manual.safeZones.enumerated()), id: \.offset) { _, zone in
                if zone.count >= 2 {
                    HStack {
                        Image(systemName: "clock")
                        Text("\(zone[0])s - \(zone[1])s")
                            .font(.subheadline.monospaced())
                    }
                }
            }

            if !manual.hints.isEmpty {
                Divider()

                ForEach(manual.hints, id: \.self) { hint in
                    HStack(alignment: .top) {
                        Text("•")
                        Text(hint)
                            .font(.subheadline)
                    }
                }
            }
        }
    }
}

// MARK: - Stability Instructions

struct StabilityInstructionsView: View {
    let manual: StabilityManual

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading) {
                    Text("Max Tilts")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text("\(manual.maxTilts)")
                        .font(.title2.bold())
                }

                Spacer()

                VStack(alignment: .trailing) {
                    Text("Stable Duration")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text("\(manual.duration)s")
                        .font(.title2.bold())
                }
            }

            if !manual.tips.isEmpty {
                Divider()

                Text("TIPS:")
                    .font(.caption.bold())
                    .foregroundStyle(.secondary)

                ForEach(manual.tips, id: \.self) { tip in
                    HStack(alignment: .top) {
                        Text("•")
                        Text(tip)
                            .font(.subheadline)
                    }
                }
            }
        }
    }
}

#Preview {
    ModuleListView(viewModel: GameViewModel())
}
