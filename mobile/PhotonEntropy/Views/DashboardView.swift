import SwiftUI

struct DashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    if let error = viewModel.error {
                        ErrorBanner(message: error)
                    }

                    connectionStatusSection

                    if let device = viewModel.primaryDevice {
                        deviceSection(device)
                    }

                    if let stats = viewModel.stats {
                        statsSection(stats)
                    }

                    if !viewModel.recentCommits.isEmpty {
                        recentCommitsSection
                    }
                }
                .padding()
            }
            .navigationTitle("PhotonEntropy")
            .refreshable {
                await viewModel.refresh()
            }
            .task {
                await viewModel.refresh()
            }
        }
    }

    private var connectionStatusSection: some View {
        HStack {
            Image(systemName: viewModel.isConnected ? "wifi" : "wifi.slash")
                .foregroundStyle(viewModel.isConnected ? .green : .red)

            Text(viewModel.isConnected ? "Connected to server" : "Disconnected")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            Spacer()

            if viewModel.isWebSocketConnected {
                HStack(spacing: 4) {
                    Circle()
                        .fill(.green)
                        .frame(width: 8, height: 8)
                    Text("Live")
                        .font(.caption)
                        .foregroundStyle(.green)
                }
            }

            if viewModel.isLoading {
                ProgressView()
                    .scaleEffect(0.8)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private func deviceSection(_ device: DeviceStatus) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("IoT Device")
                    .font(.headline)
                Spacer()
                StatusIndicator(isOnline: device.isOnline)
            }

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: "cpu")
                        .foregroundStyle(.secondary)
                    Text(device.deviceId)
                        .font(.title3.weight(.semibold))
                }

                HStack {
                    Image(systemName: "clock")
                        .foregroundStyle(.secondary)
                    Text("Last seen \(device.lastSeenFormatted)")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }

            HStack(spacing: 12) {
                StatCard(
                    title: "Quality",
                    value: "\(device.qualityPercentage)%",
                    icon: "checkmark.seal.fill",
                    color: device.averageQuality >= 0.75 ? .green : .orange
                )

                StatCard(
                    title: "Commits",
                    value: "\(device.totalCommits)",
                    icon: "arrow.up.doc.fill",
                    color: .blue
                )
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    private func statsSection(_ stats: StatsResponse) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("System Stats")
                .font(.headline)

            HStack(spacing: 12) {
                StatCard(
                    title: "Total Samples",
                    value: formatNumber(stats.totalSamples),
                    icon: "waveform.path",
                    color: .purple
                )

                StatCard(
                    title: "Entropy Pool",
                    value: formatBytes(stats.entropyPoolSize),
                    icon: "drop.fill",
                    color: .cyan
                )
            }
        }
    }

    private func formatNumber(_ n: Int) -> String {
        if n >= 1_000_000 {
            return String(format: "%.1fM", Double(n) / 1_000_000)
        } else if n >= 1_000 {
            return String(format: "%.1fK", Double(n) / 1_000)
        }
        return "\(n)"
    }

    private func formatBytes(_ bytes: Int) -> String {
        if bytes >= 1024 {
            return String(format: "%.1f KB", Double(bytes) / 1024)
        }
        return "\(bytes) B"
    }

    private var recentCommitsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Live Feed")
                    .font(.headline)
                Spacer()
                HStack(spacing: 4) {
                    Circle()
                        .fill(.green)
                        .frame(width: 6, height: 6)
                    Text("Realtime")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            ForEach(viewModel.recentCommits, id: \.id) { commit in
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 6) {
                            Image(systemName: commit.accepted ? "checkmark.circle.fill" : "xmark.circle.fill")
                                .foregroundStyle(commit.accepted ? .green : .orange)
                                .font(.caption)
                            Text("\(commit.samples) samples")
                                .font(.subheadline.weight(.medium))
                        }
                        Text(commit.deviceId)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    Spacer()

                    QualityBadge(quality: commit.quality)
                }
                .padding(.vertical, 8)

                if commit.id != viewModel.recentCommits.last?.id {
                    Divider()
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }
}

struct ErrorBanner: View {
    let message: String

    var body: some View {
        HStack {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(.orange)
            Text(message)
                .font(.subheadline)
            Spacer()
        }
        .padding()
        .background(Color.orange.opacity(0.1))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

#Preview {
    DashboardView()
}
