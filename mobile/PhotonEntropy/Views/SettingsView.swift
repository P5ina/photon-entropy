import SwiftUI

struct SettingsView: View {
    @ObservedObject private var apiService = APIService.shared
    @State private var serverURL: String = ""
    @State private var isCheckingConnection = false
    @State private var connectionStatus: Bool?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Server URL", text: $serverURL)
                        .textContentType(.URL)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                        .autocorrectionDisabled()

                    Button {
                        Task {
                            await checkConnection()
                        }
                    } label: {
                        HStack {
                            Text("Test Connection")
                            Spacer()
                            if isCheckingConnection {
                                ProgressView()
                            } else if let status = connectionStatus {
                                Image(systemName: status ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundStyle(status ? .green : .red)
                            }
                        }
                    }
                    .disabled(isCheckingConnection)
                } header: {
                    Text("Server")
                } footer: {
                    Text("Enter the URL of your PhotonEntropy backend server")
                }

                Section("About") {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundStyle(.secondary)
                    }

                    Link(destination: URL(string: "https://github.com/P5ina/photon-entropy")!) {
                        HStack {
                            Text("GitHub Repository")
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Settings")
            .onAppear {
                serverURL = apiService.baseURL
            }
            .onChange(of: serverURL) { _, newValue in
                apiService.baseURL = newValue
                connectionStatus = nil
            }
        }
    }

    private func checkConnection() async {
        isCheckingConnection = true
        connectionStatus = nil

        connectionStatus = await apiService.healthCheck()

        isCheckingConnection = false
    }
}

#Preview {
    SettingsView()
}
