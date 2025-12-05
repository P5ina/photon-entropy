import SwiftUI

struct StatusIndicator: View {
    let isOnline: Bool

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(isOnline ? Color.green : Color.red)
                .frame(width: 8, height: 8)

            Text(isOnline ? "Online" : "Offline")
                .font(.subheadline.weight(.medium))
                .foregroundStyle(isOnline ? .green : .red)
        }
    }
}

#Preview {
    VStack(spacing: 20) {
        StatusIndicator(isOnline: true)
        StatusIndicator(isOnline: false)
    }
}
