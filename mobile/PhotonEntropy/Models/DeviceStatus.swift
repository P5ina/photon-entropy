import Foundation

struct DeviceStatus: Codable, Identifiable {
    let deviceId: String
    let isOnline: Bool
    let lastSeen: Date
    let totalCommits: Int
    let averageQuality: Double
    let entropyPoolSize: Int?
    let isTooBright: Bool

    var id: String { deviceId }

    var qualityPercentage: Int {
        Int(averageQuality * 100)
    }

    var lastSeenFormatted: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: lastSeen, relativeTo: Date())
    }

    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case isOnline = "is_online"
        case lastSeen = "last_seen"
        case totalCommits = "total_commits"
        case averageQuality = "average_quality"
        case entropyPoolSize = "entropy_pool_size"
        case isTooBright = "is_too_bright"
    }
}
