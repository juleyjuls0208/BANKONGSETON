import Foundation

enum APIEndpoints {
    static let baseURL = "https://juley2823.pythonanywhere.com/api"
    static let qrBaseURL = "https://bankoseton.pythonanywhere.com/api"

    static let login = "/auth/login"
    static let balance = "/student/balance"
    static let transactions = "/student/transactions"
    static let budget = "/student/budget"
    static let lostCard = "/student/lost-card"
    static let logout = "/auth/logout"
    static let budgetSummary = "/budget-summary"
    static let qrCart = "/qr/"          // append token: /qr/<token>
    static let qrConfirm = "/qr/confirm"
}
