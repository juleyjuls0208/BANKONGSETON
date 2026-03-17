import Foundation
import SwiftUI

// MARK: - AuthManager

@MainActor
final class AuthManager: ObservableObject {
    @Published var isLoggedIn: Bool
    @Published var studentName: String
    @Published var showSessionExpiredAlert: Bool = false

    init() {
        // Restore session from Keychain on app launch
        isLoggedIn = KeychainHelper.read(forKey: "auth_token") != nil
        studentName = KeychainHelper.read(forKey: "student_name") ?? ""
    }

    // Called after successful login
    func login(token: String, student: Student, jwtToken: String? = nil) {
        KeychainHelper.save(token, forKey: "auth_token")
        KeychainHelper.save(student.studentId, forKey: "student_id")
        KeychainHelper.save(student.name, forKey: "student_name")
        if let jwt = jwtToken {
            KeychainHelper.save(jwt, forKey: "jwt_token")
        }
        if student.cardStatus?.lowercased() == "active" {
            KeychainHelper.delete(forKey: "isCardLost")
        }
        studentName = student.name
        isLoggedIn = true
    }

    // Called from Settings → Logout button
    func logout(apiClient: APIClient) async {
        _ = try? await apiClient.logout()  // best-effort server logout
        clearAll()
    }

    // Called when any ViewModel catches APIError.unauthorized (session expiry)
    func handleUnauthorized() {
        showSessionExpiredAlert = true
        // clearAll() is intentionally NOT called here.
        // It is called from the View's alert button action so the alert
        // is not torn down before the user reads it (isLoggedIn = false
        // would destroy the view immediately).
    }

    // Called when any ViewModel catches APIError.cardLost
    func handleCardLost() {
        // Persist the isCardLost flag BEFORE clearing everything else
        KeychainHelper.save("true", forKey: "isCardLost")
        clearAll()
    }

    // MARK: - Internal

    func clearAll() {
        let keysToDelete = [
            "auth_token",
            "student_id",
            "student_name",
            "last_balance",
            "theme_mode",
            "budget_alert_month",
            "budgetAlerted80",
            "budgetAlerted100",
            "jwt_token"
        ]
        keysToDelete.forEach { KeychainHelper.delete(forKey: $0) }
        isLoggedIn = false
        studentName = ""
    }
}
