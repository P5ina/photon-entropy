import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            DashboardView()
                .tabItem {
                    Label("Dashboard", systemImage: "gauge.with.dots.needle.bottom.50percent")
                }

            GeneratorView()
                .tabItem {
                    Label("Generator", systemImage: "dice.fill")
                }

            NormalDistributionView()
                .tabItem {
                    Label("Distribution", systemImage: "chart.bar.xaxis")
                }

            HistoryView()
                .tabItem {
                    Label("History", systemImage: "clock.arrow.circlepath")
                }

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape.fill")
                }
        }
    }
}

#Preview {
    ContentView()
}
