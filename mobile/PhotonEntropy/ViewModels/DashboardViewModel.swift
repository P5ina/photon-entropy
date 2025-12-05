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
    private var hasInitiallyLoaded = false

    var primaryDevice: DeviceStatus? {
        devices.first
    }

    init() {
        print("[VM] DashboardViewModel init")
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
                entropyPoolSize: devices[index].entropyPoolSize,
                isTooBright: update.isTooBright
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

    func initialLoad() async {
        guard !hasInitiallyLoaded else { return }
        await doRefresh()
        hasInitiallyLoaded = true
    }

    func refresh() async {
        // Ignore spurious refreshable triggers during/right after initial load
        guard hasInitiallyLoaded else {
            print("[REFRESH] Ignored - initial load in progress")
            return
        }
        await doRefresh()
    }

    private func doRefresh() async {
        guard !isLoading else {
            print("[REFRESH] Skipped - already loading")
            return
        }

        isLoading = true
        error = nil

        do {
            print("[REFRESH] Fetching...")
            let fetchedDevices = try await apiService.getDeviceStatus()
            let fetchedStats = try await apiService.getStats()

            devices = fetchedDevices
            stats = fetchedStats
            isConnected = true
            print("[REFRESH] Done - \(devices.count) devices")

            if !isWebSocketConnected {
                connectWebSocket()
            }
        } catch {
            print("[REFRESH] Error: \(error)")
            self.error = error.localizedDescription
            isConnected = false
        }

        isLoading = false
    }
}
