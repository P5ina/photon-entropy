import SwiftUI

struct NormalDistributionView: View {
    @StateObject private var viewModel = NormalDistributionViewModel()
    @State private var showCopiedToast = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    parametersSection

                    if !viewModel.values.isEmpty {
                        chartSection
                        statisticsSection
                    } else if viewModel.isLoading {
                        loadingSection
                    } else {
                        placeholderSection
                    }

                    generateButton

                    if let error = viewModel.error {
                        ErrorBanner(message: error)
                    }
                }
                .padding()
            }
            .navigationTitle("Normal Distribution")
        }
        .overlay(alignment: .bottom) {
            if showCopiedToast {
                copiedToast
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
    }

    private var parametersSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Parameters")
                .font(.headline)

            HStack(spacing: 16) {
                VStack(alignment: .leading) {
                    Text("Mean (μ)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    TextField("Mean", value: $viewModel.mean, format: .number)
                        .textFieldStyle(.roundedBorder)
                        .keyboardType(.decimalPad)
                }

                VStack(alignment: .leading) {
                    Text("Std Dev (σ)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    TextField("Std Dev", value: $viewModel.stdDev, format: .number)
                        .textFieldStyle(.roundedBorder)
                        .keyboardType(.decimalPad)
                }
            }

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Sample Count")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text("\(viewModel.sampleCount)")
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(.secondary)
                }

                Slider(
                    value: Binding(
                        get: { Double(viewModel.sampleCount) },
                        set: { viewModel.sampleCount = Int($0) }
                    ),
                    in: 10...500,
                    step: 10
                )
                .tint(.accentColor)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var chartSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Distribution")
                    .font(.headline)
                Spacer()
                Button {
                    viewModel.copyValues()
                    withAnimation {
                        showCopiedToast = true
                    }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                        withAnimation {
                            showCopiedToast = false
                        }
                    }
                } label: {
                    Label("Copy", systemImage: "doc.on.doc")
                        .font(.caption)
                }
                .buttonStyle(.bordered)
            }

            HistogramChart(
                values: viewModel.values,
                mean: viewModel.mean,
                stdDev: viewModel.stdDev
            )
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var statisticsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Statistics")
                .font(.headline)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                StatItem(label: "Target μ", value: String(format: "%.2f", viewModel.mean))
                StatItem(label: "Actual μ", value: String(format: "%.4f", viewModel.actualMean))
                StatItem(label: "Target σ", value: String(format: "%.2f", viewModel.stdDev))
                StatItem(label: "Actual σ", value: String(format: "%.4f", viewModel.actualStdDev))
                StatItem(label: "Min", value: String(format: "%.4f", viewModel.minValue))
                StatItem(label: "Max", value: String(format: "%.4f", viewModel.maxValue))
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var loadingSection: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("Generating samples...")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .frame(height: 200)
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var placeholderSection: some View {
        VStack(spacing: 16) {
            Image(systemName: "chart.bar.xaxis")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("Generate samples to see distribution")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .frame(height: 200)
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var generateButton: some View {
        Button {
            Task {
                await viewModel.generate()
            }
        } label: {
            HStack {
                Image(systemName: "waveform.path.ecg")
                Text("Generate")
            }
            .font(.headline)
            .frame(maxWidth: .infinity)
            .padding()
        }
        .buttonStyle(.borderedProminent)
        .disabled(viewModel.isLoading || viewModel.stdDev <= 0)
    }

    private var copiedToast: some View {
        HStack {
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(.green)
            Text("Values copied to clipboard")
        }
        .padding()
        .background(.ultraThinMaterial)
        .clipShape(Capsule())
        .padding(.bottom, 32)
    }
}

private struct StatItem: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.subheadline.monospacedDigit().bold())
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

#Preview {
    NormalDistributionView()
}
