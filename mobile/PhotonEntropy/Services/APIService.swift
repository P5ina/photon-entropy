import Foundation
import Combine

enum APIError: LocalizedError {
    case invalidURL
    case networkError(Error)
    case invalidResponse
    case serverError(Int)
    case decodingError(Error)

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
        }
    }
}

@MainActor
class APIService: ObservableObject {
    static let shared = APIService()

    @Published var baseURL: String = "https://entropy.p5ina.dev"

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        return URLSession(configuration: config)
    }()

    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    private init() {}

    // MARK: - Health

    func healthCheck() async -> Bool {
        guard let url = URL(string: "\(baseURL)/health") else {
            return false
        }

        do {
            let (_, response) = try await session.data(from: url)
            return (response as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }
}
