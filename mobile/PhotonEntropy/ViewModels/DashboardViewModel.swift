import Foundation
import Combine

@MainActor
class DashboardViewModel: ObservableObject {
    @Published var devices: [DeviceStatus] = []
    @Published var stats: StatsResponse?
    @Published var isLoading = false
    @Published var error: String?
    @Published var isConnected = false
    @Published var isWebSocketConnected = false
    @Published var recentCommits: [NewCommitData] = []

    private let apiService = APIService.shared
    private let wsService = WebSocketService.shared
    private var cancellables = Set<AnyCancellable>()

    var primaryDevice: DeviceStatus? {
        devices.first
    }

    init() {
        setupWebSocketSubscriptions()
    }

    private func setupWebSocketSubscriptions() {
        wsService.$isConnected
            .receive(on: DispatchQueue.main)
            .assign(to: &$isWebSocketConnected)

        wsService.deviceUpdateSubject
            .receive(on: DispatchQueue.main)
            .sink { [weak self] update in
                self?.handleDeviceUpdate(update)
            }
            .store(in: &cancellables)

        wsService.statsUpdateSubject
            .receive(on: DispatchQueue.main)
            .sink { [weak self] update in
                self?.handleStatsUpdate(update)
            }
            .store(in: &cancellables)

        wsService.newCommitSubject
            .receive(on: DispatchQueue.main)
            .sink { [weak self] commit in
                self?.handleNewCommit(commit)
            }
            .store(in: &cancellables)

        wsService.poolUpdateSubject
            .receive(on: DispatchQueue.main)
            .sink { [weak self] update in
                self?.handlePoolUpdate(update)
            }
            .store(in: &cancellables)
    }

    private func handleDeviceUpdate(_ update: DeviceUpdateData) {
        if let index = devices.firstIndex(where: { $0.deviceId == update.deviceId }) {
            devices[index] = DeviceStatus(
                deviceId: update.deviceId,
                isOnline: update.isOnline,
                lastSeen: update.lastSeen,
                totalCommits: Int(update.totalCommits),
                averageQuality: update.averageQuality,
                entropyPoolSize: devices[index].entropyPoolSize
            )
        }
    }

    private func handleStatsUpdate(_ update: StatsUpdateData) {
        stats = StatsResponse(
            totalDevices: update.totalDevices,
            totalCommits: update.totalCommits,
            totalSamples: update.totalSamples,
            entropyPoolSize: update.entropyPoolSize
        )
    }

    private func handleNewCommit(_ commit: NewCommitData) {
        recentCommits.insert(commit, at: 0)
        if recentCommits.count > 10 {
            recentCommits.removeLast()
        }
    }

    private func handlePoolUpdate(_ update: PoolUpdateData) {
        if var currentStats = stats {
            stats = StatsResponse(
                totalDevices: currentStats.totalDevices,
                totalCommits: currentStats.totalCommits,
                totalSamples: currentStats.totalSamples,
                entropyPoolSize: update.size
            )
        }
    }

    func connectWebSocket() {
        wsService.connect()
    }

    func disconnectWebSocket() {
        wsService.disconnect()
    }

    func refresh() async {
        isLoading = true
        error = nil

        isConnected = await apiService.healthCheck()

        if !isConnected {
            error = "Cannot connect to server"
            isLoading = false
            return
        }

        do {
            async let devicesTask = apiService.getDeviceStatus()
            async let statsTask = apiService.getStats()

            devices = try await devicesTask
            stats = try await statsTask

            // Connect WebSocket after initial data load
            if !isWebSocketConnected {
                connectWebSocket()
            }
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }
}
