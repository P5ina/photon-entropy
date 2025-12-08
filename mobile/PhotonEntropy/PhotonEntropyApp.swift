//
//  PhotonEntropyApp.swift
//  PhotonEntropy
//
//  Created by Timur Turatbekov on 06.12.2025.
//

import SwiftUI

@main
struct PhotonEntropyApp: App {
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .onChange(of: scenePhase) { _, newPhase in
            GameService.shared.handleScenePhaseChange(to: newPhase)
        }
    }
}
