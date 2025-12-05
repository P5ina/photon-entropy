import Foundation

@MainActor
class HistoryViewModel: ObservableObject {
    @Published var commits: [EntropyCommit] = []
    @Published var isLoading = false
    @Published var error: String?

    private let apiService = APIService.shared

    func refresh() async {
        isLoading = true
        error = nil

        do {
            commits = try await apiService.getHistory(limit: 50)
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }
}
