import Foundation
import UIKit
import Combine

enum GeneratorType: String, CaseIterable {
    case number = "Number"
    case password = "Password"
    case uuid = "UUID"

    var icon: String {
        switch self {
        case .number: return "number"
        case .password: return "key.fill"
        case .uuid: return "doc.text"
        }
    }
}

@MainActor
class GeneratorViewModel: ObservableObject {
    @Published var generatedValue: String = ""
    @Published var isLoading = false
    @Published var error: String?

    // Number settings
    @Published var minValue: Int = 1
    @Published var maxValue: Int = 100

    // Password settings
    @Published var passwordLength: Int = 16

    private let apiService = APIService.shared

    func generate(type: GeneratorType) async {
        isLoading = true
        error = nil
        generatedValue = ""

        do {
            switch type {
            case .number:
                let response = try await apiService.generateRandom(min: minValue, max: maxValue)
                generatedValue = String(response.value)

            case .password:
                let response = try await apiService.generatePassword(length: passwordLength)
                generatedValue = response.password

            case .uuid:
                let response = try await apiService.generateUUID()
                generatedValue = response.uuid
            }
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func copyToClipboard() {
        #if os(iOS)
        UIPasteboard.general.string = generatedValue
        #endif
    }
}
