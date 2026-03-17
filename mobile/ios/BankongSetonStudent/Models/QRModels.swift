import Foundation

// MARK: - QR Cart Models

struct QrCartItem: Codable {
    let name: String
    let price: Double
    let qty: Int
}

struct QrCartResponse: Codable {
    let items: [QrCartItem]
    let total: Double
    let cashier: String
}

// MARK: - QR Confirm Models

struct QrConfirmRequest: Codable {
    let token: String
}

struct QrConfirmResponse: Codable {
    let message: String
    let newBalance: Double?

    enum CodingKeys: String, CodingKey {
        case message
        case newBalance = "new_balance"
    }
}
