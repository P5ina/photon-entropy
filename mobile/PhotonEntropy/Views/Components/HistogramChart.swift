import SwiftUI
import Charts

struct HistogramBin: Identifiable {
    let id = UUID()
    let range: ClosedRange<Double>
    let count: Int

    var midpoint: Double {
        (range.lowerBound + range.upperBound) / 2
    }

    var label: String {
        String(format: "%.1f", midpoint)
    }
}

struct HistogramChart: View {
    let values: [Double]
    let mean: Double
    let stdDev: Double
    let binCount: Int

    init(values: [Double], mean: Double, stdDev: Double, binCount: Int = 20) {
        self.values = values
        self.mean = mean
        self.stdDev = stdDev
        self.binCount = binCount
    }

    private var bins: [HistogramBin] {
        guard !values.isEmpty else { return [] }

        let minVal = values.min() ?? 0
        let maxVal = values.max() ?? 0
        let range = maxVal - minVal

        guard range > 0 else { return [] }

        let binWidth = range / Double(binCount)

        var binCounts = [Int](repeating: 0, count: binCount)

        for value in values {
            var binIndex = Int((value - minVal) / binWidth)
            binIndex = min(binIndex, binCount - 1)
            binCounts[binIndex] += 1
        }

        return binCounts.enumerated().map { index, count in
            let lowerBound = minVal + Double(index) * binWidth
            let upperBound = lowerBound + binWidth
            return HistogramBin(range: lowerBound...upperBound, count: count)
        }
    }

    private var maxCount: Int {
        bins.map(\.count).max() ?? 1
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Chart {
                ForEach(bins) { bin in
                    BarMark(
                        x: .value("Value", bin.midpoint),
                        y: .value("Count", bin.count)
                    )
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.blue.opacity(0.7), .purple.opacity(0.7)],
                            startPoint: .bottom,
                            endPoint: .top
                        )
                    )
                    .cornerRadius(2)
                }

                // Mean line
                RuleMark(x: .value("Mean", mean))
                    .foregroundStyle(.red)
                    .lineStyle(StrokeStyle(lineWidth: 2, dash: [5, 3]))
                    .annotation(position: .top, alignment: .center) {
                        Text("μ")
                            .font(.caption.bold())
                            .foregroundStyle(.red)
                    }

                // Standard deviation lines
                RuleMark(x: .value("-1σ", mean - stdDev))
                    .foregroundStyle(.orange.opacity(0.6))
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 2]))

                RuleMark(x: .value("+1σ", mean + stdDev))
                    .foregroundStyle(.orange.opacity(0.6))
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 2]))
            }
            .chartXAxisLabel("Value")
            .chartYAxisLabel("Frequency")
            .frame(height: 200)

            // Legend
            HStack(spacing: 16) {
                HStack(spacing: 4) {
                    Rectangle()
                        .fill(.red)
                        .frame(width: 16, height: 2)
                    Text("Mean (μ)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                HStack(spacing: 4) {
                    Rectangle()
                        .fill(.orange.opacity(0.6))
                        .frame(width: 16, height: 2)
                    Text("±1σ")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }
}

#Preview {
    let sampleValues: [Double] = (0..<100).map { _ in
        // Simulate normal distribution
        let u1 = Double.random(in: 0.001...1)
        let u2 = Double.random(in: 0...1)
        return 50 + 10 * sqrt(-2 * log(u1)) * cos(2 * .pi * u2)
    }

    return HistogramChart(values: sampleValues, mean: 50, stdDev: 10)
        .padding()
}
