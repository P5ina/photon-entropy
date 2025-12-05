import Foundation

struct EntropyCommit: Codable, Identifiable {
    let id: String
    let deviceId: String
    let quality: Double
    let samples: Int
    let createdAt: Date
    let tests: TestResults

    var qualityPercentage: Int {
        Int(quality * 100)
    }

    var createdAtFormatted: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: createdAt, relativeTo: Date())
    }

    var shortId: String {
        String(id.prefix(8))
    }

    enum CodingKeys: String, CodingKey {
        case id
        case deviceId = "device_id"
        case quality
        case samples
        case createdAt = "created_at"
        case tests
    }
}

struct TestResults: Codable {
    let frequencyPassed: Bool
    let runsPassed: Bool
    let chiPassed: Bool
    let variancePassed: Bool

    var passedCount: Int {
        [frequencyPassed, runsPassed, chiPassed, variancePassed].filter { $0 }.count
    }

    enum CodingKeys: String, CodingKey {
        case frequencyPassed = "frequency_passed"
        case runsPassed = "runs_passed"
        case chiPassed = "chi_passed"
        case variancePassed = "variance_passed"
    }
}
