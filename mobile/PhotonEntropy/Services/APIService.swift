import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case networkError(Error)
    case invalidResponse
    case serverError(Int)
    case decodingError(Error)
    case insufficientEntropy

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .invalidResponse:
            return "Invalid response from server"
        case .serverError(let code):
            return "Server error: \(code)"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .insufficientEntropy:
            return "Insufficient entropy in pool"
        }
    }
}

@MainActor
class APIService: ObservableObject {
    static let shared = APIService()

    @Published var baseURL: String = "http://localhost:8080"

    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    private init() {}

    // MARK: - Health

    func healthCheck() async -> Bool {
        guard let url = URL(string: "\(baseURL)/health") else { return false }

        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            return (response as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }

    // MARK: - Device

    func getDeviceStatus(deviceId: String? = nil) async throws -> [DeviceStatus] {
        var urlString = "\(baseURL)/api/v1/device/status"
        if let deviceId = deviceId {
            urlString += "?device_id=\(deviceId)"
        }

        guard let url = URL(string: urlString) else {
            throw APIError.invalidURL
        }

        return try await fetch(url: url)
    }

    func getHistory(deviceId: String? = nil, limit: Int = 20) async throws -> [EntropyCommit] {
        var urlString = "\(baseURL)/api/v1/device/history?limit=\(limit)"
        if let deviceId = deviceId {
            urlString += "&device_id=\(deviceId)"
        }

        guard let url = URL(string: urlString) else {
            throw APIError.invalidURL
        }

        return try await fetch(url: url)
    }

    // MARK: - Entropy Generation

    func generateRandom(min: Int = 0, max: Int = 100) async throws -> RandomResponse {
        guard let url = URL(string: "\(baseURL)/api/v1/entropy/random?min=\(min)&max=\(max)") else {
            throw APIError.invalidURL
        }

        return try await fetch(url: url)
    }

    func generatePassword(length: Int = 16) async throws -> PasswordResponse {
        guard let url = URL(string: "\(baseURL)/api/v1/entropy/password?length=\(length)") else {
            throw APIError.invalidURL
        }

        return try await fetch(url: url)
    }

    func generateUUID() async throws -> UUIDResponse {
        guard let url = URL(string: "\(baseURL)/api/v1/entropy/uuid") else {
            throw APIError.invalidURL
        }

        return try await fetch(url: url)
    }

    // MARK: - Stats

    func getStats() async throws -> StatsResponse {
        guard let url = URL(string: "\(baseURL)/api/v1/stats") else {
            throw APIError.invalidURL
        }

        return try await fetch(url: url)
    }

    // MARK: - Private

    private func fetch<T: Decodable>(url: URL) async throws -> T {
        do {
            let (data, response) = try await URLSession.shared.data(from: url)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }

            if httpResponse.statusCode == 503 {
                throw APIError.insufficientEntropy
            }

            guard (200...299).contains(httpResponse.statusCode) else {
                throw APIError.serverError(httpResponse.statusCode)
            }

            do {
                return try decoder.decode(T.self, from: data)
            } catch {
                throw APIError.decodingError(error)
            }
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }
}
