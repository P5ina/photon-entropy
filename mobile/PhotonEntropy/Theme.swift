//
//  Theme.swift
//  PhotonEntropy
//
//  Apple-style design system
//

import SwiftUI

// MARK: - Colors

extension Color {
    static let theme = ThemeColors()
}

struct ThemeColors {
    // Primary accent - warm red for the bomb theme
    let accent = Color(red: 1.0, green: 0.27, blue: 0.23)

    // Success states
    let success = Color(red: 0.2, green: 0.78, blue: 0.35)

    // Warning/Active states
    let warning = Color(red: 1.0, green: 0.62, blue: 0.04)

    // Subtle backgrounds
    let cardBackground = Color(.systemGray6)
    let cardBackgroundElevated = Color(.systemGray5)

    // Timer states
    let timerNormal = Color.primary
    let timerWarning = Color(red: 1.0, green: 0.62, blue: 0.04)
    let timerCritical = Color(red: 1.0, green: 0.27, blue: 0.23)

    // Module colors
    let wires = Color(red: 1.0, green: 0.27, blue: 0.23)
    let simon = Color(red: 0.69, green: 0.32, blue: 0.87)
    let magnet = Color(red: 1.0, green: 0.62, blue: 0.04)
}

// MARK: - Typography

extension Font {
    static let theme = ThemeFonts()
}

struct ThemeFonts {
    let timer = Font.system(size: 56, weight: .light, design: .rounded)
    let timerSmall = Font.system(size: 44, weight: .light, design: .rounded)
    let heroTitle = Font.system(size: 32, weight: .bold, design: .rounded)
    let sectionHeader = Font.system(size: 13, weight: .semibold, design: .default)
    let moduleTitle = Font.system(size: 17, weight: .semibold, design: .default)
    let body = Font.system(size: 15, weight: .regular, design: .default)
    let caption = Font.system(size: 13, weight: .regular, design: .default)
    let codeInput = Font.system(size: 28, weight: .medium, design: .monospaced)
}

// MARK: - View Modifiers

struct CardStyle: ViewModifier {
    var isActive: Bool = false
    var isSolved: Bool = false

    func body(content: Content) -> some View {
        content
            .background(backgroundColor)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    private var backgroundColor: Color {
        if isSolved {
            return Color.theme.success.opacity(0.12)
        } else if isActive {
            return Color.theme.warning.opacity(0.12)
        } else {
            return Color.theme.cardBackground
        }
    }
}

struct PrimaryButtonStyle: ButtonStyle {
    var isDestructive: Bool = false

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 17, weight: .semibold))
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .frame(height: 50)
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(isDestructive ? Color.theme.accent : Color.accentColor)
            )
            .opacity(configuration.isPressed ? 0.8 : 1.0)
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.easeInOut(duration: 0.15), value: configuration.isPressed)
    }
}

struct SecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 17, weight: .medium))
            .foregroundStyle(Color.theme.accent)
            .frame(maxWidth: .infinity)
            .frame(height: 50)
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(Color.theme.accent.opacity(0.12))
            )
            .opacity(configuration.isPressed ? 0.7 : 1.0)
            .animation(.easeInOut(duration: 0.15), value: configuration.isPressed)
    }
}

extension View {
    func cardStyle(isActive: Bool = false, isSolved: Bool = false) -> some View {
        modifier(CardStyle(isActive: isActive, isSolved: isSolved))
    }
}

// MARK: - Haptics

struct Haptics {
    static func light() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }

    static func medium() {
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
    }

    static func success() {
        UINotificationFeedbackGenerator().notificationOccurred(.success)
    }

    static func error() {
        UINotificationFeedbackGenerator().notificationOccurred(.error)
    }
}
