import SwiftUI

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    var color: Color = .accentColor

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundStyle(color)
                Spacer()
            }

            Text(value)
                .font(.title2.weight(.bold))
                .foregroundStyle(.primary)

            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

#Preview {
    HStack {
        StatCard(title: "Quality", value: "100%", icon: "checkmark.seal.fill", color: .green)
        StatCard(title: "Commits", value: "142", icon: "arrow.up.doc.fill", color: .blue)
    }
    .padding()
}
