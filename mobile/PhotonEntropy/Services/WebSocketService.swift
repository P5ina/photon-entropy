import Foundation
import Combine

enum WebSocketMessageType: String, Codable {
    case poolUpdate = "pool_update"
    case deviceUpdate = "device_update"
    case newCommit = "new_commit"
    case statsUpdate = "stats_update"
}

struct WebSocketMessage: Codable {
    let type: WebSocketMessageType
    let data: AnyCodable
    let timestamp: Date

    enum CodingKeys: String, CodingKey {
        case type, data, timestamp
    }
}

struct PoolUpdateData: Codable {
    let size: Int
    let maxSize: Int

    enum CodingKeys: String, CodingKey {
        case size
        case maxSize = "max_size"
    }
}

struct DeviceUpdateData: Codable {
    let deviceId: String
    let isOnline: Bool
    let lastSeen: Date
    let totalCommits: Int
    let averageQuality: Double
    let isTooBright: Bool

    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case isOnline = "is_online"
        case lastSeen = "last_seen"
        case totalCommits = "total_commits"
        case averageQuality = "average_quality"
        case isTooBright = "is_too_bright"
    }
}

struct NewCommitData: Codable {
    let id: String
    let deviceId: String
    let quality: Double
    let samples: Int
    let accepted: Bool
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case deviceId = "device_id"
        case quality, samples, accepted
        case createdAt = "created_at"
    }
}

struct StatsUpdateData: Codable {
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

struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else {
            value = NSNull()
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        switch value {
        case let string as String:
            try container.encode(string)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let bool as Bool:
            try container.encode(bool)
        default:
            try container.encodeNil()
        }
    }
}

@MainActor
class WebSocketService: ObservableObject {
    static let shared = WebSocketService()

    @Published var isConnected = false
    @Published var poolSize: Int = 0
    @Published var poolMaxSize: Int = 0

    let poolUpdateSubject = PassthroughSubject<PoolUpdateData, Never>()
    let deviceUpdateSubject = PassthroughSubject<DeviceUpdateData, Never>()
    let newCommitSubject = PassthroughSubject<NewCommitData, Never>()
    let statsUpdateSubject = PassthroughSubject<StatsUpdateData, Never>()

    private var webSocketTask: URLSessionWebSocketTask?
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 10
    private var reconnectWorkItem: DispatchWorkItem?
    private var pingTask: Task<Void, Never>?

    // Dedicated session for WebSocket to avoid interference with API calls
    private lazy var webSocketSession: URLSession = {
        let config = URLSessionConfiguration.default
        config.waitsForConnectivity = true
        return URLSession(configuration: config)
    }()

    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    private init() {}

    func connect() {
        // Clean up any existing dead connection
        if let task = webSocketTask {
            if task.state != .running {
                cleanup()
            } else {
                return // Already connected
            }
        }

        let baseURL = APIService.shared.baseURL
        let wsURL = baseURL
            .replacingOccurrences(of: "https://", with: "wss://")
            .replacingOccurrences(of: "http://", with: "ws://")

        guard let url = URL(string: "\(wsURL)/ws") else { return }

        print("[WebSocket] Connecting to \(url)")
        let task = webSocketSession.webSocketTask(with: url)
        webSocketTask = task
        task.resume()

        isConnected = true
        reconnectAttempts = 0
        receiveMessage()
        startPing()
    }

    func reconnect() {
        cleanup()
        connect()
    }

    func disconnect() {
        reconnectWorkItem?.cancel()
        reconnectWorkItem = nil
        cleanup()
    }

    private func cleanup() {
        pingTask?.cancel()
        pingTask = nil
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isConnected = false
    }

    private func startPing() {
        pingTask?.cancel()
        pingTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 30_000_000_000) // 30 seconds
                guard !Task.isCancelled else { break }
                self?.webSocketTask?.sendPing { error in
                    Task { @MainActor in
                        if error != nil {
                            self?.handleDisconnect()
                        }
                    }
                }
            }
        }
    }

    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            Task { @MainActor in
                switch result {
                case .success(let message):
                    self?.handleMessage(message)
                    self?.receiveMessage()
                case .failure(let error):
                    print("[WebSocket] Receive error: \(error)")
                    self?.handleDisconnect()
                }
            }
        }
    }

    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        guard case .string(let text) = message else { return }

        // Backend may batch multiple JSON messages with newlines
        let lines = text.split(separator: "\n", omittingEmptySubsequences: true)

        for line in lines {
            guard let data = String(line).data(using: .utf8) else { continue }

            do {
                let wsMessage = try decoder.decode(WebSocketMessage.self, from: data)

                guard let dataDict = wsMessage.data.value as? [String: Any] else { continue }
                let dataJSON = try JSONSerialization.data(withJSONObject: dataDict)

                switch wsMessage.type {
                case .poolUpdate:
                    let update = try decoder.decode(PoolUpdateData.self, from: dataJSON)
                    poolSize = update.size
                    poolMaxSize = update.maxSize
                    poolUpdateSubject.send(update)

                case .deviceUpdate:
                    let update = try decoder.decode(DeviceUpdateData.self, from: dataJSON)
                    deviceUpdateSubject.send(update)

                case .newCommit:
                    let commit = try decoder.decode(NewCommitData.self, from: dataJSON)
                    newCommitSubject.send(commit)

                case .statsUpdate:
                    let stats = try decoder.decode(StatsUpdateData.self, from: dataJSON)
                    statsUpdateSubject.send(stats)
                }
            } catch {
                print("WebSocket decode error: \(error)")
            }
        }
    }

    private func handleDisconnect() {
        print("[WebSocket] Disconnected, attempt \(reconnectAttempts + 1)/\(maxReconnectAttempts)")
        pingTask?.cancel()
        pingTask = nil
        webSocketTask = nil
        isConnected = false

        guard reconnectAttempts < maxReconnectAttempts else {
            print("[WebSocket] Max reconnect attempts reached")
            return
        }

        reconnectAttempts += 1
        let delay = min(reconnectAttempts * 2, 30)
        print("[WebSocket] Reconnecting in \(delay)s...")

        reconnectWorkItem?.cancel()
        let workItem = DispatchWorkItem { [weak self] in
            Task { @MainActor in
                self?.connect()
            }
        }
        reconnectWorkItem = workItem
        DispatchQueue.main.asyncAfter(deadline: .now() + .seconds(delay), execute: workItem)
    }
}
