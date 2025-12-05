import Foundation
import UIKit

@MainActor
class NormalDistributionViewModel: ObservableObject {
    @Published var values: [Double] = []
    @Published var isLoading = false
    @Published var error: String?

    // Parameters
    @Published var mean: Double = 0
    @Published var stdDev: Double = 1
    @Published var sampleCount: Int = 100

    // Computed statistics
    var actualMean: Double {
        guard !values.isEmpty else { return 0 }
        return values.reduce(0, +) / Double(values.count)
    }

    var actualStdDev: Double {
        guard values.count > 1 else { return 0 }
        let mean = actualMean
        let variance = values.map { pow($0 - mean, 2) }.reduce(0, +) / Double(values.count - 1)
        return sqrt(variance)
    }

    var minValue: Double {
        values.min() ?? 0
    }

    var maxValue: Double {
        values.max() ?? 0
    }

    private let apiService = APIService.shared

    func generate() async {
        isLoading = true
        error = nil

        do {
            let response = try await apiService.generateNormalDistribution(
                mean: mean,
                stdDev: stdDev,
                count: sampleCount
            )
            values = response.values
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func clear() {
        values = []
        error = nil
    }

    func copyValues() {
        let text = values.map { String(format: "%.6f", $0) }.joined(separator: "\n")
        UIPasteboard.general.string = text
    }
}
