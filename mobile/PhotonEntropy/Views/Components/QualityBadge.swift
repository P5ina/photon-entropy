import SwiftUI

struct QualityBadge: View {
    let quality: Double

    private var percentage: Int {
        Int(quality * 100)
    }

    private var color: Color {
        switch percentage {
        case 100:
            return .green
        case 75..<100:
            return .yellow
        case 50..<75:
            return .orange
        default:
            return .red
        }
    }

    private var icon: String {
        switch percentage {
        case 100:
            return "checkmark.circle.fill"
        case 75..<100:
            return "checkmark.circle"
        case 50..<75:
            return "exclamationmark.triangle.fill"
        default:
            return "xmark.circle.fill"
        }
    }

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption)
            Text("\(percentage)%")
                .font(.caption.weight(.semibold))
        }
        .foregroundStyle(color)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(color.opacity(0.15))
        .clipShape(Capsule())
    }
}

#Preview {
    VStack(spacing: 10) {
        QualityBadge(quality: 1.0)
        QualityBadge(quality: 0.75)
        QualityBadge(quality: 0.5)
        QualityBadge(quality: 0.25)
    }
}
