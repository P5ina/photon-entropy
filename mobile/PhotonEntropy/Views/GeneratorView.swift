import SwiftUI

struct GeneratorView: View {
    @StateObject private var viewModel = GeneratorViewModel()
    @State private var selectedType: GeneratorType = .number
    @State private var showCopiedToast = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    typePicker

                    resultCard

                    settingsSection

                    generateButton

                    if let error = viewModel.error {
                        ErrorBanner(message: error)
                    }
                }
                .padding()
            }
            .navigationTitle("Generator")
        }
        .overlay(alignment: .bottom) {
            if showCopiedToast {
                copiedToast
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
    }

    private var typePicker: some View {
        Picker("Type", selection: $selectedType) {
            ForEach(GeneratorType.allCases, id: \.self) { type in
                Label(type.rawValue, systemImage: type.icon)
                    .tag(type)
            }
        }
        .pickerStyle(.segmented)
    }

    private var resultCard: some View {
        VStack(spacing: 16) {
            if viewModel.isLoading {
                ProgressView()
                    .scaleEffect(1.5)
                    .frame(height: 60)
            } else if viewModel.generatedValue.isEmpty {
                Text("Tap Generate")
                    .font(.title2)
                    .foregroundStyle(.secondary)
                    .frame(height: 60)
            } else {
                Text(viewModel.generatedValue)
                    .font(selectedType == .password ? .system(.body, design: .monospaced) : .system(.largeTitle, design: .rounded).weight(.bold))
                    .multilineTextAlignment(.center)
                    .textSelection(.enabled)
                    .frame(minHeight: 60)

                Button {
                    viewModel.copyToClipboard()
                    withAnimation {
                        showCopiedToast = true
                    }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                        withAnimation {
                            showCopiedToast = false
                        }
                    }
                } label: {
                    Label("Copy", systemImage: "doc.on.doc")
                        .font(.subheadline)
                }
                .buttonStyle(.bordered)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 32)
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    @ViewBuilder
    private var settingsSection: some View {
        switch selectedType {
        case .number:
            numberSettings
        case .password:
            passwordSettings
        case .uuid:
            EmptyView()
        }
    }

    private var numberSettings: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Range")
                .font(.headline)

            HStack(spacing: 16) {
                VStack(alignment: .leading) {
                    Text("Min")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    TextField("Min", value: $viewModel.minValue, format: .number)
                        .textFieldStyle(.roundedBorder)
                        .keyboardType(.numberPad)
                }

                VStack(alignment: .leading) {
                    Text("Max")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    TextField("Max", value: $viewModel.maxValue, format: .number)
                        .textFieldStyle(.roundedBorder)
                        .keyboardType(.numberPad)
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var passwordSettings: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Length")
                    .font(.headline)
                Spacer()
                Text("\(viewModel.passwordLength)")
                    .font(.headline)
                    .foregroundStyle(.secondary)
            }

            Slider(value: Binding(
                get: { Double(viewModel.passwordLength) },
                set: { viewModel.passwordLength = Int($0) }
            ), in: 8...64, step: 1)
            .tint(.accentColor)
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private var generateButton: some View {
        Button {
            Task {
                await viewModel.generate(type: selectedType)
            }
        } label: {
            HStack {
                Image(systemName: "dice.fill")
                Text("Generate")
            }
            .font(.headline)
            .frame(maxWidth: .infinity)
            .padding()
        }
        .buttonStyle(.borderedProminent)
        .disabled(viewModel.isLoading)
    }

    private var copiedToast: some View {
        HStack {
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(.green)
            Text("Copied to clipboard")
        }
        .padding()
        .background(.ultraThinMaterial)
        .clipShape(Capsule())
        .padding(.bottom, 32)
    }
}

#Preview {
    GeneratorView()
}
