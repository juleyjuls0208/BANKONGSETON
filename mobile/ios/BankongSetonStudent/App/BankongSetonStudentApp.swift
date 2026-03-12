import SwiftUI

// MARK: - App Entry Point

@main
struct BankongSetonStudentApp: App {
    @StateObject private var authManager = AuthManager()
    @StateObject private var apiClient = APIClient()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authManager)
                .environmentObject(apiClient)
        }
    }
}
