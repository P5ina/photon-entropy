import Foundation

struct RandomResponse: Codable {
    let value: Int
    let generatedAt: Date

    enum CodingKeys: String, CodingKey {
        case value
        case generatedAt = "generated_at"
    }
}

struct PasswordResponse: Codable {
    let password: String
    let length: Int
    let generatedAt: Date

    enum CodingKeys: String, CodingKey {
        case password
        case length
        case generatedAt = "generated_at"
    }
}

struct UUIDResponse: Codable {
    let uuid: String
    let generatedAt: Date

    enum CodingKeys: String, CodingKey {
        case uuid
        case generatedAt = "generated_at"
    }
}

struct StatsResponse: Codable {
    let totalDevices: Int
    let totalCommits: Int
    let totalSamples: Int
    let entropyPoolSize: Int

    enum CodingKeys: String, CodingKey {
        case totalDevices = "total_devices"
        case totalCommits = "total_commits"
        case totalSamples = "total_samples"
        case entropyPoolSize = "entropy_pool_size"
    }
}
