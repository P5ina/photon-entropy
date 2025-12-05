import SwiftUI

struct HistoryView: View {
    @StateObject private var viewModel = HistoryViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.commits.isEmpty && !viewModel.isLoading {
                    emptyState
                } else {
                    commitsList
                }
            }
            .navigationTitle("History")
            .refreshable {
                await viewModel.refresh()
            }
            .task {
                await viewModel.refresh()
            }
            .overlay {
                if viewModel.isLoading && viewModel.commits.isEmpty {
                    ProgressView("Loading...")
                }
            }
        }
    }

    private var emptyState: some View {
        ContentUnavailableView(
            "No Commits Yet",
            systemImage: "tray",
            description: Text("Entropy commits from IoT devices will appear here")
        )
    }

    private var commitsList: some View {
        List(viewModel.commits) { commit in
            CommitRow(commit: commit)
        }
        .listStyle(.plain)
    }
}

struct CommitRow: View {
    let commit: EntropyCommit

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(commit.shortId)
                    .font(.headline.monospaced())

                Spacer()

                QualityBadge(quality: commit.quality)
            }

            HStack(spacing: 16) {
                Label("\(commit.samples)", systemImage: "waveform.path")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Label(commit.createdAtFormatted, systemImage: "clock")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            testsRow
        }
        .padding(.vertical, 4)
    }

    private var testsRow: some View {
        HStack(spacing: 8) {
            TestBadge(name: "F", passed: commit.tests.frequencyPassed)
            TestBadge(name: "R", passed: commit.tests.runsPassed)
            TestBadge(name: "X", passed: commit.tests.chiPassed)
            TestBadge(name: "V", passed: commit.tests.variancePassed)

            Spacer()

            Text("\(commit.tests.passedCount)/4 tests")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

struct TestBadge: View {
    let name: String
    let passed: Bool

    var body: some View {
        Text(name)
            .font(.caption2.weight(.bold))
            .frame(width: 20, height: 20)
            .background(passed ? Color.green.opacity(0.2) : Color.red.opacity(0.2))
            .foregroundStyle(passed ? .green : .red)
            .clipShape(Circle())
    }
}

#Preview {
    HistoryView()
}
