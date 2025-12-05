import Foundation

@MainActor
class DashboardViewModel: ObservableObject {
    @Published var devices: [DeviceStatus] = []
    @Published var stats: StatsResponse?
    @Published var isLoading = false
    @Published var error: String?
    @Published var isConnected = false

    private let apiService = APIService.shared

    var primaryDevice: DeviceStatus? {
        devices.first
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
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }
}
